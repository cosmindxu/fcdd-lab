// Minimal D1 shim over node:sqlite, with a cooperative scheduler barrier at
// every statement execution -- this is the yield point the oracle drives.
import { DatabaseSync } from 'node:sqlite';
export function makeDB(sqlPath, sched) {
  const db = new DatabaseSync(':memory:');
  db.exec(sqlPath);
  const wrap = (sql) => {
    let args = [];
    const self = {
      bind(...a) { args = a; return self; },
      async first() { await sched(); const r = db.prepare(sql).get(...args); return r === undefined ? null : r; },
      async all()   { await sched(); return { results: db.prepare(sql).all(...args) }; },
      async run()   { await sched(); const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
    };
    return self;
  };
  return { prepare: wrap, _raw: db };
}
