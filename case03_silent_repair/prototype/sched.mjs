// Deterministic cooperative scheduler. Every DB op is a yield point; the word
// (e.g. "ABBA") fixes the interleaving. If the word names a client that has no
// pending op after the event loop has fully drained, that client is finished
// and its letter is skipped -- so the exploration never deadlocks and never
// depends on a timer.
export function makeSched() {
  const waiters = []; let word = [], wi = 0, scheduledDrain = false;
  const tryRelease = () => {
    while (wi < word.length) {
      const idx = waiters.findIndex(w => w.id === word[wi]);
      if (idx >= 0) { wi++; waiters.splice(idx,1)[0].resolve(); return true; }
      return false;                       // wanted client not (yet) waiting
    }
    if (waiters.length) { waiters.shift().resolve(); return true; }   // word spent: FIFO
    return false;
  };
  const drain = () => {
    scheduledDrain = false;
    if (tryRelease()) return;
    if (waiters.length && wi < word.length) { wi++; pump(); }   // skip a finished client
  };
  const pump = () => {
    if (tryRelease()) return;
    if (!scheduledDrain) { scheduledDrain = true; setImmediate(drain); }
  };
  return { setWord(w){ word=[...w]; wi=0; }, yield(id){ return new Promise(r => { waiters.push({id,resolve:r}); pump(); }); } };
}
