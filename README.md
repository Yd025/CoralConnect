# CoralConnect

**A game of prompt battling, scored by the ocean.**

We started with the water. AI tokens are electricity, and that electricity reaches oceans that are already under stress. Our first idea was an MCP that priced a prompt's token use before it ran. HackGT 13 is Seaside Market, so that cost belonged in public. We believe the way to teach it is a game: two people, one reef, and a battle over who can spend the model's attention with care.

CoralConnect is that game. You find a partner by the animal on your phone and write a single prompt together. Grok builds the missing function. The shared reef thrives when the prompt carries the facts, and wilts when the model has to go search for them.

Play it at **[coralconnectgt.tech](https://coralconnectgt.tech)**.

## The experience

### Find your person

Open the pair room on your phone. No host. No code to shout across the table. Two taps:


| What you build                        | What you care about                |
| ------------------------------------- | ---------------------------------- |
| Apps, Data, Systems, Hardware, Design | People, Planet, Trust, Speed, Cost |


The room pairs you with someone already waiting. Shared work comes first, then shared care. Both phones show the same animal, a Seagull, Turtle, Dolphin, Octopus, Whale, Crab, Ray, or Heron. You find them in the crowd.

Grok introduces you in a sentence that is actually about you: what you share, what only one of you brings, and a question about the environment to ask when the round ends.

### Build one thing, together

Each phone holds a different function in the same small app. Team chat. A snack counter. Hackathon check-in. A song booth. A task board. You have two minutes. The prompt has to name the file and the function, because your partner's half is not on your screen. Grok edits the file. Either of you can send it. You share the score.

### Watch the reef

The laptop is the ocean.


| Grade | What the prompt did                                   | What the reef does |
| ----- | ----------------------------------------------------- | ------------------ |
| A+    | The facts, and a clear ask, inside a 200-token budget | A turtle arrives   |
| A     | The facts, said plainly                               | A coral bloom      |
| B     | The facts, buried in a large paste                    | The water holds    |
| C     | One fact left for the model to look up                | Murk               |
| D     | The whole file, dumped in                             | Heavier murk       |
| F     | "Fix it." Or a pasted secret.                         | Sludge             |


Every missing fact is one web lookup, about **1,200 tokens**. The message's own tokens count, so pasting everything is not a free pass. After the turn, the phone prints a receipt: included, looked up, tokens, and carbon.

The carbon line is a teaching model printed in full: **0.0003 kWh** per 1,000 tokens, times **390 g CO2** per kWh. The same waste is drawn again as if a million developers had sent it.

An adequate follow-up can bring a damaged reef back. An A or A+ asks Grok Imagine for the turtle or the bloom, and the picture fades into the scene.

### Take a table

Compete mode seats up to ten people, each with their own thread and the same shared reef. The rounds are stories with a meter already running:

- a farm whose water bill doubled
- a reef station drowned in heat alerts
- a cafe cooler eating the month's power
- a home battery empty by 9 pm
- debugging threads a real codebase would recognize, including one where a credential must stay out of the prompt

Debugging rounds run in two steps. The first message carries the first failure. The second failure is new, and the follow-up has to bring its own source. The score is the average. The reef moves on every turn.

Finished pairs stay on the board. People can pair again.

## How CoralConnect answers HackGT 13

One product. The main track, two sponsor challenges, and a public home on a `.tech` domain.

### Oracle of the Deep — ML/AI

*Dive into the depths of data and surface something brilliant through innovative ML/AI and visualization that sees what no one else can.*

The judge is the oracle. It sees the work a thin prompt hides.

1. **Count.** Every token in the message, against a 200-token budget.
2. **Rules.** The facts this round requires. Leave one out, and the model is charged a search.
3. **Review.** Grok reads the prompt and can only add cost. Asking to be graded an A+ does nothing.
4. **Measure.** A full reading uses the real Grok run, including web searches the model actually made.

That grade is not a number in a sidebar. It is the reef: thriving, stressed, bleaching, or dead, plus murk, sludge, a turtle, or a bloom. Grok also writes the code, introduces the pair, and paints the reward. The visualization is the insight. You watch the hidden lookup happen to an ocean.

### Meta — Bringing People Closer Together with AI

*Build the AI-powered social product you wish existed.*

CoralConnect is for anyone who would otherwise spend a weekend next to a stranger and never learn what that person builds.

AI is the introduction, not a sticker on a matchmaking form.

- The two taps say what you build and what you care about.
- The shared animal gets you across the room.
- Grok writes the specific overlap, the thing only one of you brings, and the question you should ask out loud.
- The task is split so the app exists only if you talk. Each of you holds a function the other cannot see.
- Two minutes later you have a score, a reef, and a reason to keep talking about the environment.

A dropdown can say you both picked Apps. Grok is what says why you should work together.

### A Marina’s Mission — social good, presented by Aramco

*Design technology that makes a real difference, in climate, energy, and the problems close to home.*

The reef is a climate instrument wearing a story.

Wasted prompts are wasted energy. CoralConnect prices that waste in tokens and in grams of CO2, then shows the habit at the scale of a million developers. The role-play rounds are the same lesson in a life someone is already living: irrigation left on, a reef sensor screaming until the team mutes it, a cooler that never cycles off, a battery schedule that buys peak power every night. The adequate prompt names the zone, the rule, the machine, or the device. The thin prompt makes the model search, and the water answers.

The pair round ends the same way. Two people who just met ask each other what they would change so the work costs the ocean less.

### Best .Tech Domain Name

The booth lives at **[coralconnectgt.tech](https://coralconnectgt.tech)**.

That name is the front door. The join QR hands a phone the public host, the stage and the API share it, and the project has an address that can outlast the weekend. CoralConnect is a `.tech` project in the literal sense: the domain is how strangers get into the reef.

## Under the hood


|                  |                                                                        |
| ---------------- | ---------------------------------------------------------------------- |
| Stage and phones | Next.js, TypeScript                                                    |
| Carbon engine    | FastAPI, Python                                                        |
| The model        | Grok for the edit, the answer, the review, and the introduction        |
| The picture      | Grok Imagine, after an A or A+                                         |
| The room         | WebSockets, a standing pair room, a compete table, a public pair board |
| The home         | `coralconnectgt.tech`                                                  |


The grade, in one line:

```
tokens you wrote
+ 1,200 for every fact you left out
+ a little more if you never say what you want, or you ask for the whole file rewritten
= the work the reef is judging, against a 200-token budget
```

A secret in the prompt is an F, and it is redacted before it can reach the model or another player. The answer key stays on the server. Players see a hint. They do not see the solution.

Every round's sample prompts are tested, from the precise one to the vague one, so the reef and the receipt stay honest. The full design of the judge is in [docs/PROMPT-JUDGE.md](docs/PROMPT-JUDGE.md). Every role-play card is in [PROBLEM-SETS.md](PROBLEM-SETS.md).

## Run the booth

The public site (HTTPS on coralconnectgt.tech) runs from `docker-compose.prod.yml`. The steps, firewall ports, and spending caps are in [deploy/README.md](deploy/README.md).

Docker, from this folder:

```bash
cp -n backend/.env.example backend/.env
docker compose up --build
```

The site is on port 3000. The engine is on port 8080.

- **Pair room:** [http://localhost:3000/collaborate](http://localhost:3000/collaborate)
- **Compete table and QR:** [http://localhost:3000/admin](http://localhost:3000/admin)
- **The reef:** `/stage/CODE`
- **A phone:** `/play/CODE`
- **The board:** [http://localhost:3000/pairs](http://localhost:3000/pairs)

Put your key in `backend/.env` for live Grok edits, the spoken-aloud introduction, and reward art:

```bash
XAI_API_KEY=your-key
GROK_MODEL=grok-4.6
GROK_IMAGE_MODEL=grok-imagine-image-2.0
GROK_IMAGES=true
TECH_DOMAIN=coralconnectgt.tech
```

Keys come from [console.x.ai](https://console.x.ai). `TECH_DOMAIN` is the host printed on the QR.

Games survive a restart in the `coral-data` volume. Edits under `backend/app`, `frontend/app`, `frontend/components`, `frontend/lib`, and `frontend/public` show up without a rebuild.

Without Docker (Python 3.10 or newer):

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

```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```

