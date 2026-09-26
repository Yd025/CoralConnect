# CoralConnect

CoralConnect is a booth game for HackGT 13. Two people scan a QR code, get paired or race, and prompt a coding model through a real debugging thread. The laptop shows a shared reef. An adequate prompt leaves the reef alive. A prompt that makes the model go look the answer up dumps sludge in the water.

## Problem statement

Developers and coding agents send thin prompts into an LLM and let the model do the rest of the job. The model then spends tokens searching the web, opening docs, and reconstructing a file the human already had on screen. That extra work is the cost: more tokens, more GPU time, more energy. The prompt itself can be short. The waste is the lookup the prompt forces.

CoralConnect makes that lookup visible. Each challenge puts a real source in front of the player: a billing function, a crashing React header, a half-applied migration, or a handler that logs a credential. The adequate move is to put that source in the message so the model can answer from what it was given. If the message leaves the source out, the engine charges about 1,200 tokens for the web search the model would run. That charge is what moves the reef. Prompt length is not the score.

A round is two steps, because one message is not a real debugging session. The first message has to carry the first failure. After the model answers, a second failure arrives, and the follow-up needs its own source. The score is the average of the two turns. Every turn also changes the shared reef.

## 👑 Main track

Submit to **one** track: **A Marina’s Mission** (Social Good), presented by Aramco Americas.

The project is a climate and energy tool. It shows developers the carbon cost of making a model do extra work, using an educational estimate of `0.0003 kWh` per 1,000 lookup tokens times `390 g CO2` per kWh. The same search is also shown as if a million developers sent that thin prompt. The reef is the lesson, not a separate theme.

We are not submitting to Oracle of the Deep, The Lighthouse Laboratory, or The Shipyard.

## Sponsor tracks

HackGT allows any number of sponsor challenges alongside the one main track. We are entering these three.

### Meta — Bringing People Closer Together with AI

Collaborate mode is the connection. Each person taps two words: what they build and what they care about. Collaborate is pairs of two. The next person in shares your animal, and both phones say the name so you have to find each other in the room. With a Grok key, the phone also says what you share, so you can be sure you have the right person. Each phone then holds a different piece of the same challenge. When the round ends, the pair stays and talks about the environment. Compete mode stays the solo contrast, with the full source on one phone.

Devpost needs a public repo, a 2–3 minute demo video, and a short note on who it is for, how it strengthens connection, and why AI is required. Who it is for: hackathon attendees who would otherwise sit next to a stranger and never learn what that person builds. Connection: the questionnaire gives them a reason to talk, and the split challenge gives them something they can only finish together. AI is required because it reads those two answers and names the specific overlap. Roleplay challenges use the same piece format: each character gets a fact the other does not have.

### SpaceXAI — Make it Legendary

The project is built in Cursor. With `XAI_API_KEY` set, Grok (`grok-4.6`) writes the debugging reply and Grok Imagine (`grok-imagine-image-2.0`) paints the turtle or coral bloom when a turn earns an A or A+. The societal problem is the energy cost of models that have to go search because the prompt was thin. Paste the key into `backend/.env` before the demo. Without the key, grades and the reef still run, and the reply is a stand-in.

### Notability — Trust the Process

Use Notability during the hackathon for the architecture diagram and the phone and stage wireframes. On Devpost, tag Notability, add a short note on how it was used, and attach at least two screenshots. The app does not need a code change for this.

## Sponsor tracks we are not entering

These challenges ask for a different artifact than this booth game.

- **NSA HEARSAY** wants a synthetic-audio score in a CSV.
- **NSA Packet Pursuit** wants flags from a packet capture.
- **NSA Codebreaker** wants a reverse-engineering write-up on their own challenge.
- **Visa** wants a generative shopping and payments flow.
- **Impiricus** wants a new HCP engagement tool, and SMS is off limits.

**Secret in the log** is a CoralConnect round about a handler that writes an `Authorization` header into logs and error responses. It teaches the same adequate-prompt lesson, with a credential as the source the model should not have to hunt for. It is not an NSA submission.

## 60-second pitch

AI burns energy when a thin prompt makes the model look the answer up on the web. CoralConnect is a booth game that shows that cost on a shared reef.

For A Marina’s Mission, every missing source is charged as a web lookup, about 1,200 tokens, and the reef wilts. Include the function, the error, or the header, and the model does no extra search.

For Meta, two phones show the same animal. Those two people find each other in the room, solve one challenge together, and then talk about the environment.

For SpaceXAI, Grok writes the reply and Grok Imagine paints the reward when the prompt was adequate.

## What the booth shows

The laptop runs two things:

- **Carbon engine** (`backend/`) — FastAPI. Sessions, pairing, lookup grades, reef health, Grok.
- **Screens** (`frontend/`) — Next.js. Admin console, phone controller, main-stage aquarium.

Phones only need the Next.js link. The page calls the API on port 8080 of the same computer.

- **Carbon engine** (`backend/`) — FastAPI. Sessions, pairing, token grades, reef health, Grok.
- **Screens** (`frontend/`) — Next.js. Admin console, phone controller, main-stage aquarium.

Phones only need the Next.js link. The page calls the API on port 8080 of the same computer.

## Run it

Docker is the way to start the booth. From this folder:

```bash
cp -n backend/.env.example backend/.env
docker compose up --build
```

That publishes the site on port 3000 and the carbon engine on port 8080. Open [http://localhost:3000/admin](http://localhost:3000/admin).

Source edits in `backend/app`, `frontend/app`, `frontend/components`, `frontend/lib`, and `frontend/public` show up without a rebuild. Game state is kept in the `coral-data` volume.

1. Pick **Collaborate** (two short answers, then a shared prompt where each phone has a different piece) or **Compete** (everyone writes alone).
2. Pick a challenge and create the game.
3. Open the main stage on the laptop monitor.
4. The QR code is the join link. If it points at `localhost`, change **Phone link host** to this computer's Wi-Fi address. Phones have to be on the same network, and macOS may ask to allow incoming connections for Node and Python.

Leave `XAI_API_KEY` blank and the booth still runs. Grades, reef health, and a stand-in code answer all work. Paste a key from [console.x.ai](https://console.x.ai) into `backend/.env` when you want live Grok answers and Grok Imagine reward art.

```bash
# backend/.env
XAI_API_KEY=your-key
GROK_MODEL=grok-4.6
GROK_IMAGE_MODEL=grok-imagine-image-2.0
GROK_IMAGES=true
```

With Docker, games live in the `coral-data` volume, so a container restart does not wipe the lobby. A local backend instead writes `backend/data/sessions.json`. Either file holds admin and player keys. Do not commit it.

To run without Docker, use two terminals:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

```bash
cd frontend
npm install
npm run dev
```

## What each person owns

**Admin / main stage** — already wired. `/admin` creates the room. `/stage/CODE` is the monitor. `/play/CODE` is the phone.

**Reef teammates.** Put full-scene SVGs in `frontend/public/reef/`:

| File | When it shows |
| --- | --- |
| `thriving.svg` | Reef health 75–100 |
| `stressed.svg` | 50–74 |
| `bleaching.svg` | 25–49 |
| `dead.svg` | 0–24 |

If a file is missing, the screen uses the drawing in `frontend/components/reef/FallbackReef.tsx`. You can replace that component. Do not change the props on `ReefStage`. Murk, the sludge barrel, the red flash, reward names, and the health number are already connected to the game.

**Phone teammates.** The controller is `frontend/app/play/[code]/page.tsx`. Shared typing in collaborate mode goes over the WebSocket as a `draft` message. Last write wins.

## How a round works

Each challenge is a two-step debugging thread. The phone shows a real file or log. The message has to include the fact the model would otherwise search for. After the model answers, a second failure lands, and that follow-up needs its own source. A vague message charges about 1,200 lookup tokens and wilts the reef. Including the source charges none.

Collaborate: the room holds up to 8 people, in pairs of 2. When the second person of a pair joins, both phones show the same animal, such as Seagull. They find each other by that name. With a Grok key, the phone adds what those two share and a question about the environment for the end of the round. Each phone gets a different piece of the turn, and the shared message has to include both. Either person can submit. The pair shares one score. An odd person keeps waiting, and the round will not start until every pair is complete. Roleplay challenges add a `Part` per character in `backend/app/challenges.py`.

Compete: each phone has its own thread. The reef is still shared.

The score is the average of the turns in the thread. Every turn also changes the reef.

Rehearsal buttons on the admin page inject an adequate prompt and a vague one, so you can test the reef before anyone scans in.

## Carbon grade

The grade is the extra work, not the length of the prompt. If the message names the source (the function, the error, the header), the lookup cost is 0 and the grade is A+. If it doesn't, the engine charges 1,200 tokens for the web search the model would run, and the grade is F.

Health stays between 0 and 100. An adequate follow-up can bring a damaged reef back.

The gram number is an educational estimate, not a full lifecycle assessment: `0.0003 kWh` per 1,000 lookup tokens, times `390 g CO2` per kWh. That search is also shown as if a million developers sent the same thin prompt.

A and A+ prompts ask Grok Imagine for a turtle or a bloom. The picture is optional. The SVG reward shows immediately, and the generated image swaps in if it arrives.

## Tests

```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```
