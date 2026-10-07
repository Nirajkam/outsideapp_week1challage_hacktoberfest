// Sound listening: Google's YAMNet (Apache-2.0) running on-device with TensorFlow.js.
// Audio is held in memory for a few seconds, classified, then discarded. Only labels are saved.
(() => {
  const SECONDS = 10, RATE = 16000, THRESHOLD = 0.3;
  let model = null, meta = null;
  const status = t => { $('heard').textContent = t; };

  async function load() {
    if (model) return;
    status('Loading the sound model (first time only)...');
    meta = await (await fetch('model/labels.json')).json();
    model = await tf.loadGraphModel('model/yamnet/model.json');
  }

  async function record() {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
    });
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const src = ctx.createMediaStreamSource(stream);
    const proc = ctx.createScriptProcessor(4096, 1, 1);
    const chunks = []; let got = 0; const need = ctx.sampleRate * SECONDS;
    await new Promise(done => {
      proc.onaudioprocess = e => {
        chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
        got += 4096; if (got >= need) done();
      };
      src.connect(proc); proc.connect(ctx.destination);
    });
    stream.getTracks().forEach(t => t.stop());
    proc.disconnect(); src.disconnect();
    const inRate = ctx.sampleRate; await ctx.close();

    const raw = new Float32Array(got); let o = 0;
    for (const c of chunks) { raw.set(c, o); o += c.length; }
    const n = Math.floor(raw.length * RATE / inRate), wave = new Float32Array(n);
    for (let i = 0; i < n; i++) {                       // linear resample to 16 kHz
      const x = i * inRate / RATE, i0 = Math.floor(x), f = x - i0;
      wave[i] = raw[i0] * (1 - f) + (raw[i0 + 1] ?? raw[i0]) * f;
    }
    return wave;
  }

  function classify(wave) {
    return tf.tidy(() => {
      const out = model.predict(tf.tensor1d(wave));
      const list = out.shape ? [out] : Array.isArray(out) ? out : Object.values(out);
      const scores = list.find(t => t.shape[t.shape.length - 1] === 521);
      return scores.reshape([-1, 521]).max(0).arraySync();   // best score per class across the clip
    });
  }

  function groupScores(perClass) {
    return Object.entries(meta.groups)
      .map(([key, ids]) => ({ key, score: Math.max(...ids.map(i => perClass[i])) }))
      .filter(g => g.score >= THRESHOLD)
      .sort((a, b) => b.score - a.score);
  }

  $('listen').onclick = async () => {
    const btn = $('listen'); btn.disabled = true;
    try {
      await load();
      status('Listening for ' + SECONDS + ' seconds. Stay still.');
      const wave = await record();
      status('Working out what you heard...');
      const found = groupScores(classify(wave));
      if (S.active) {
        S.active.sounds = S.active.sounds || {};
        found.forEach(g => { S.active.sounds[g.key] = (S.active.sounds[g.key] || 0) + 1; });
        save();
      }
      status(found.length
        ? 'Heard: ' + found.map(g => SOUND_LABELS[g.key]).join(', ')
        : 'Nothing clear this time. Try again.');
    } catch (e) {
      console.error(e);
      status("Couldn't listen: " + (e.message || e.name) + '. Check microphone permission.');
    }
    btn.disabled = false;
  };
})();
