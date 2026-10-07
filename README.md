# Outside

Outside is a lightweight walking journal and trip tracker for phone-friendly use. It helps you record where you went, how long you were outside, how you felt, what you heard, and what made the trip memorable. Each outing becomes a searchable, exportable trip entry that can be reviewed later.

## Features

- Start a walking trip with a place name and quick details
- Track elapsed time while you are outside
- Capture route, weather, company, mood, and highlights
- Save notes and quick observations from each trip
- Log approximate step count from phone motion data when available
- Listen for environmental sounds on-device when the browser allows it
- Export the journal as plain text and copy/share it

## How it works

1. Open the app in a browser.
2. Enter a place name such as a park, riverside trail, or neighborhood street.
3. Tap “I’m outside” to start the trip.
4. Add trip details like route, weather, company, mood, and notes.
5. Finish the trip with “I’m back” to save the entry to your journal.

## Run locally

```bash
npm start
```

Then open the browser at:

```text
http://localhost:4173
```

## Detailed trip examples

### Trip 1: Sunrise river walk

This trip begins before most of the city wakes up. The route follows the riverside path with a cool breeze and still water reflecting the first light. The mood is quiet and clear, with a solo pace and enough room to think. The best moment comes when a bird call cuts through the morning stillness and the whole bank feels calm and open. Notes for this trip might include: “the air smelled like wet stone,” “the path was nearly empty,” and “the sunrise made the whole stretch feel like a reset.”

### Trip 2: Forest trail after rain

This outing is slower and more grounded. The trail is damp, the weather is cool and cloudy, and the ground smells rich and leafy. A friend accompanies the walk, and the pace is easy and conversational. The highlights include the sound of rain dripping from the tree line and the view of soft mist lifting between trunks. This is the kind of trip that feels restorative: the body moves, the mind settles, and the notes capture the mood as reflective and calm.

### Trip 3: Evening neighborhood loop

The route is a familiar neighborhood circuit with a few small detours. The weather is mild and the evening light feels warm and golden. Company is a dog and a few neighbors seen briefly along the way. The mood is upbeat and relaxed, and the walk includes a short pause to watch the sky change color. Highlights include hearing laughter from a nearby porch, noticing the first signs of evening traffic settling down, and feeling a gentle reset after a busy day.

### Trip 4: Midday park reset

This trip is short but high-energy. The route covers the park loop and a bench by the pond. The weather is bright and sunny, and the mood is focused and recharged. The walk works as a midday reset: breathing deeper, listening to wind through the trees, and taking in the open space. The notes likely mention the light, the motion of leaves, and the feeling of being back in rhythm after a long stretch of indoor work.

## Data handling

The journal is stored locally in the browser using localStorage, so each device keeps its own trips unless you export the journal and save or share the text. This makes the app simple and private while still letting you review or copy historical outings.

## Notes

The sound-recognition feature depends on browser support and the availability of a compatible TensorFlow model. If the model is unavailable, the app gracefully keeps the trip journal working and records your notes without blocking the rest of the experience.
