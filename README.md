# Outside

A small, private app that helps you spend more time outdoors. Check in when you leave, build a gentle streak, and let an open-source sound model write down what you heard. No account, no server, no social feed.

Built for the Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass.

<!-- Add 1-2 screenshots here: ![Outside app](docs/screenshot.png) -->

## What it does
- **Check in and out.** Tap "I'm outside", see a timer, and write a short note when you're back.
- **Streak with rest days.** Counts consecutive days outside. You earn one rest day for every 7 days outside, so one missed day does not erase your streak.
- **Listen.** Tap "Listen for 10 seconds" and the app labels the sounds around you: birds, wind and leaves, water, traffic, voices, animals, bells, footsteps.
- **Journal.** Each walk is saved with its note and the sounds you heard.

## Why open models matter here
- **Private.** Audio is processed on the phone and discarded after a few seconds. Only the labels are saved. Nothing is uploaded, and there is no account.
- **Works offline.** The model ships inside the app, so it works with no signal.
- **Free to run.** No API, no subscription, no server to pay for.

## How it works
- The sound model is **YAMNet** (Google, Apache 2.0), which recognizes 521 sound classes. It runs in the app through **TensorFlow.js**.
- The 521 classes are grouped into the friendly categories above (see `www/model/labels.json`).
- The web app (plain HTML and JavaScript) is packaged as an Android app with **Capacitor**.
- Data is stored on the device only.

## Run it
Browser (quickest):
```
python3 -m http.server -d www 8000
```
Open `http://localhost:8000` (the microphone needs localhost or HTTPS).

Android:
```
npm install
npx cap sync
npx cap open android
```
Then run it from Android Studio on a phone with USB debugging on.

Model files live in `www/model/yamnet/`. TensorFlow.js is copied from `node_modules/@tensorflow/tfjs/dist/tf.min.js` into `www/lib/`.

## Limits
- It labels sound **types**, not species ("Birds", not "robin").
- It listens in 10-second bursts while the app is open, not in the background.
- Loud, close sounds are detected better than faint, distant ones.
- Android only for now.

## Credits
- YAMNet by Google, Apache License 2.0
- TensorFlow.js, Apache License 2.0
- Capacitor, MIT License
- Class list from the YAMNet class map in the TensorFlow models repository

## License
MIT for the app code. Third-party models and libraries keep their own licenses.