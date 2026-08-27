import { readFileSync } from 'node:fs';
import { AsyncLocalStorage } from 'node:async_hooks';
import worker from './worker.js';
import { makeDB } from './d1shim.mjs';
import { makeSched } from './sched.mjs';
const SCHEMA = readFileSync('./schema.sql', 'utf8');
const als = new AsyncLocalStorage();
const post = (env, path, body) => worker.fetch(new Request('http://x' + path, {
  method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) }), env);

async function trial(word) {
  const sched = makeSched();
  const DB = makeDB(SCHEMA, () => { const id = als.getStore(); return id ? sched.yield(id) : Promise.resolve(); });
  const env = { DB };
  const g = await (await post(env, '/api/games', { mode:'h2h', name:'W' })).json();   // setup: untagged, free
  sched.setWord(word);
  const mk = (tag) => als.run(tag, () => post(env, `/api/games/${g.id}/join`, { name: tag }));
  const pA = mk('A'), pB = mk('B');
  const [rA, rB] = await Promise.all([pA, pB]);
  const row = DB._raw.prepare('SELECT black_token, black_name FROM games WHERE id=?').get(g.id);
  return { a: rA.status, b: rB.status, black: row.black_name };
}
const words = ['AABB','ABAB','ABBA','BAAB','BABA','BBAA'];
let bad = 0;
for (const w of words) {
  const r = await trial(w);
  const dbl = (r.a === 200 && r.b === 200);
  if (dbl) bad++;
  console.log(`  word=${w}  joinA=${r.a} joinB=${r.b} stored_black=${r.black}  ${dbl ? '<== TWO PLAYERS SEATED (invariant C2 violated)' : 'ok'}`);
}
console.log(`\ninterleavings admitting a double seat: ${bad}/${words.length}`);
