# Outside

Outside is a lightweight walking journal and trip tracker for phone-friendly use. It records where you went, how long you were outside, approximate steps, and environmental sounds identified on your phone. Each outing becomes an exportable trip entry you can review later.

## Features

- Start a walking trip with an optional place name
- Track elapsed time while you are outside
- Automatically write a short trip note from locally detected sounds, duration, and steps
- Log approximate step count from phone motion data when available
- Listen for environmental sounds on-device when the browser allows it
- Export the journal as plain text and copy/share it

## How it works

1. Open the app in a browser.
2. Enter a place name such as a park, riverside trail, or neighborhood street.
3. Tap “I’m outside” to start the trip.
4. Finish the trip with “I’m back” to automatically write and save a journal entry.

## Run locally

```bash
npm start
```

Then open the browser at:

```text
http://localhost:4173
```

## Example generated entries

### Environmental sounds identified

“A 12-minute walk at Riverside Park. The local sound model picked up birds and wind and leaves. The phone counted about 1,240 steps.”

### No clear sound detected

“A 5-minute walk. The sound model did not identify a clear environmental sound. The phone counted about 510 steps.”

### Steps unavailable

“A 12-minute walk at the park. The local sound model picked up water.”

## Data handling

The journal is stored locally in the browser using localStorage, so each device keeps its own trips unless you export the journal and save or share the text. This makes the app simple and private while still letting you review or copy historical outings.

## Notes

The on-device YAMNet model classifies environmental sounds; the journal note is composed locally from detected sounds, duration, and step count. It does not use a text-generation model or guess details such as weather, route, mood, or company. Sound recognition requires microphone permission and browser support. If listening is unavailable, the journal still saves trip duration and available step count.
