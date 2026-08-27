import { readFileSync } from 'node:fs';
import { AsyncLocalStorage } from 'node:async_hooks';
import { makeDB } from './d1shim.mjs';
import { makeSched } from './sched.mjs';
const SCHEMA = readFileSync('./schema.sql','utf8');
const als = new AsyncLocalStorage();
const P = (w,env,path,body) => w.fetch(new Request('http://x'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),env);

async function seq(w) {                       // the VISIBLE suite's join test (sequential)
  const DB = makeDB(SCHEMA, () => Promise.resolve()); const env = {DB};
  const g = await (await P(w,env,'/api/games',{name:'W'})).json();
  const r1 = await P(w,env,`/api/games/${g.id}/join`,{name:'A'});
  const r2 = await P(w,env,`/api/games/${g.id}/join`,{name:'B'});
  return r1.status===200 && r2.status===409;
}
async function conc(w, word) {
  const sched = makeSched();
  const DB = makeDB(SCHEMA, () => { const id=als.getStore(); return id?sched.yield(id):Promise.resolve(); });
  const env={DB};
  const g = await (await P(w,env,'/api/games',{name:'W'})).json();
  sched.setWord(word);
  const mk=(t)=>als.run(t,()=>P(w,env,`/api/games/${g.id}/join`,{name:t}));
  const [a,b]=await Promise.all([mk('A'),mk('B')]);
  const row=DB._raw.prepare('SELECT black_token FROM games WHERE id=?').get(g.id);
  const okCount = [a,b].filter(r=>r.status===200).length;
  return okCount===1 && !!row.black_token;    // clause C2: exactly one seat
}
const words=[];
const gen=(p,na,nb)=>{ if(na===0&&nb===0){words.push(p);return;} if(na)gen(p+'A',na-1,nb); if(nb)gen(p+'B',na,nb-1); };
gen('',3,3);                                   // all C(6,3)=20 interleavings of 3 ops each
for (const [label,file] of [['SEEDED (faulty)','./worker.js'],['PLAUSIBLE-WRONG repair','./worker_wrong.js'],['CORRECT repair','./worker_right.js']]) {
  const w = (await import(file)).default;
  const v = await seq(w);
  let fails=0; for (const wd of words) if (!(await conc(w,wd))) fails++;
  console.log(`${label.padEnd(24)} visible(sequential): ${v?'PASS':'FAIL'}   hidden(${words.length} interleavings): ${fails?`FAIL in ${fails}`:'PASS'}`);
}
