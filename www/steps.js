// Approximate step counter from the phone's motion sensor. Works only while the app is open.
// If counts are too high or low, change THRESH (higher = fewer steps).
(() => {
  const THRESH = 1.3, MIN_GAP = 300;
  let on = false, seen = false, avg = 9.8, last = 0, up = false, lastSave = 0;

  function onMotion(e) {
    const a = e.accelerationIncludingGravity;
    if (!a) return;
    seen = true;
    if (!S.active) return;
    const m = Math.hypot(a.x || 0, a.y || 0, a.z || 0);
    avg += (m - avg) * 0.05;                       // slow baseline = gravity
    const v = m - avg, now = Date.now();
    if (v > THRESH && !up && now - last > MIN_GAP) { up = true; last = now; S.active.steps = (S.active.steps || 0) + 1; }
    else if (v < THRESH * 0.4) up = false;
  }

  setInterval(() => {
    if (S.active && !on) { window.addEventListener('devicemotion', onMotion); on = true; }
    if (!S.active && on) { window.removeEventListener('devicemotion', onMotion); on = false; }
    if (S.active) {
      const n = S.active.steps || 0;
      $('steps').textContent = seen ? '~' + n.toLocaleString() + ' steps' : 'Steps are counted on a phone';
      if (Date.now() - lastSave > 5000) { save(); lastSave = Date.now(); }
    }
  }, 1000);
})();
