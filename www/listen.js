// Automatic listening while a walk is active. YAMNet (Apache-2.0) + TensorFlow.js, fully on-device.
// Audio stays in memory for a few seconds, is classified, then discarded. Only labels are saved.
(() => {
  const WINDOW_S = 5, RATE = 16000;
  const MIN = { water: 0.12, wind: 0.25, traffic: 0.25 };      // detection bar per group (default 0.3)
  const STEADY = new Set(['water', 'wind', 'traffic']);        // steady sounds: use the average over the window
  let model = null, meta = null, running = false, starting = false, userPaused = false;
  let stream = null, ctx = null, src = null, proc = null, wake = null;

  const say = t => { $('heard').textContent = t; };
  const label = t => { $('listenlabel').textContent = t; $('listen').classList.toggle('on', running); };

  async function load() {
    if (model) return;
    say('Loading the sound model (first time only)...');
    try {
      meta = await (await fetch('model/labels.json')).json();
      if (!window.tf || typeof window.tf.loadGraphModel !== 'function') {
        throw new Error('TensorFlow.js is unavailable in this browser.');
      }
      const graph = await tf.loadGraphModel('model/yamnet/model.json?v=2');
      model = graph;
    } catch (error) {
      console.warn('Sound recognition is unavailable in this build:', error);
      model = 'unavailable';
      if (S.active) S.active.soundDetectionUnavailable = true;
      say('Sound recognition is unavailable. Your walk note will still use time and steps.');
      label('Sound detection unavailable');
      throw error;
    }
  }

  function resample(raw, inRate) {
    const n = Math.floor(raw.length * RATE / inRate), out = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const x = i * inRate / RATE, i0 = Math.floor(x), f = x - i0;
      out[i] = raw[i0] * (1 - f) + (raw[i0 + 1] ?? raw[i0]) * f;
    }
    return out;
  }

  function classify(wave) {
    return tf.tidy(() => {
      const out = model.predict(tf.tensor1d(wave));
      const list = out.shape ? [out] : Array.isArray(out) ? out : Object.values(out);
      const sc = list.find(t => t.shape[t.shape.length - 1] === 521).reshape([-1, 521]);
      return { max: sc.max(0).arraySync(), mean: sc.mean(0).arraySync() };
    });
  }

  function found(r) {
    return Object.entries(meta.groups)
      .map(([key, ids]) => ({ key, score: Math.max(...ids.map(i => (STEADY.has(key) ? r.mean : r.max)[i])) }))
      .filter(g => g.score >= (MIN[g.key] || 0.3))
      .sort((a, b) => b.score - a.score);
  }

  async function handle(raw, inRate) {
    const r = classify(resample(raw, inRate));
    const hits = found(r);
    if (S.active) {
      S.active.sounds = S.active.sounds || {};
      hits.forEach(g => { S.active.sounds[g.key] = (S.active.sounds[g.key] || 0) + 1; });
      save();
    }
    const now = hits.length ? hits.map(g => SOUND_LABELS[g.key]).join(', ') : 'nothing clear';
    const all = S.active ? soundText(S.active.sounds) : '';
    say('Now: ' + now + (all ? '  |  This walk: ' + all : ''));
    const top = r.max.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]).slice(0, 3);
    $('top3').textContent = 'Model hears: ' + top.map(([v, i]) => meta.names[i] + ' ' + v.toFixed(2)).join(', ');
  }

  async function start() {
    if (running || starting) return;
    starting = true;
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      const audioReady = ctx.resume();
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
      });
      await audioReady;
      if (ctx.state !== 'running') throw new Error('Audio is paused by the browser. Tap to retry.');
      await load();
      if (model === 'unavailable') { stop(); starting = false; return; }
      try { wake = await navigator.wakeLock.request('screen'); } catch (e) {}   // keep screen on so listening continues
      src = ctx.createMediaStreamSource(stream);
      proc = ctx.createScriptProcessor(4096, 1, 1);
      let chunks = [], got = 0, busy = false;
      const need = ctx.sampleRate * WINDOW_S;
      proc.onaudioprocess = e => {
        if (!S.active) return;
        chunks.push(new Float32Array(e.inputBuffer.getChannelData(0))); got += 4096;
        if (got >= need && !busy) {
          const raw = new Float32Array(got); let o = 0;
          for (const c of chunks) { raw.set(c, o); o += c.length; }
          chunks = []; got = 0; busy = true;
          handle(raw, ctx.sampleRate).catch(console.error).finally(() => { busy = false; });
        }
      };
      src.connect(proc); proc.connect(ctx.destination);
      running = true; label('Listening. Tap to pause');
      say('Listening...');
    } catch (e) {
      console.error(e);
      if (S.active) S.active.soundDetectionUnavailable = true;
      stop(); userPaused = true;
      label('Listening off. Tap to retry');
      say("Couldn't listen: " + (e.message || e.name) + '. Check microphone permission.');
    }
    starting = false;
  }

  document.addEventListener('outside:start-listening', start);

  function stop() {
    running = false;
    try { proc && proc.disconnect(); src && src.disconnect(); } catch (e) {}
    if (stream) stream.getTracks().forEach(t => t.stop());
    if (ctx) ctx.close().catch(() => {});
    if (wake) wake.release().catch(() => {});
    stream = ctx = src = proc = wake = null;
  }

  $('listen').onclick = () => {
    userPaused = !userPaused;
    if (userPaused) { stop(); label('Listening paused. Tap to resume'); }
    else start();
  };

  setInterval(() => {                       // start with the walk, stop when it ends
    if (S.active && !running && !starting && !userPaused) start();
    if (!S.active && (running || userPaused)) {
      stop(); userPaused = false; label('Starting to listen...'); $('top3').textContent = '';
    }
  }, 1000);
})();