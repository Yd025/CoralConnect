# CoralConnect

Two strangers find each other, write one prompt together, and watch a living reef show the energy that prompt just spent.

Play it at [coralconnectgt.tech](https://coralconnectgt.tech).

## Inspiration

We started with the ocean.

A prompt looks free. It is not. Every token is electricity, and that electricity lands somewhere: on a grid, in waste heat, and in oceans that are already warming. Reefs bleach while the chat window stays white. The environmental cost of AI is real, and it is invisible at the moment someone hits send.

That invisibility was the thing we wanted to build against. Our first idea was an MCP for AI token usage: a tool beside the model that priced a prompt before it ran, so a developer could see the tokens, the energy, and the ocean in the same glance. HackGT 13's theme is Seaside Market. The fit was immediate. A seaside market is where the water's cost becomes public, something people can point at, trade, and argue over.

We also believe this lesson only sticks if it is shared. A private meter is easy to ignore. A game is not. So CoralConnect became a game of prompt battling. You and another person write prompts against one living reef. A careful prompt, the kind that carries the source so the model does not have to go search, leaves the water alive. A thin prompt spends tokens on a lookup, and the whole room watches the reef take the hit. The education is the battle. The ocean is the scoreboard.

The animal on your phone grew from the same belief. If token use is something we learn together, the game should put two people in front of one sea and make them find each other first.

## What it does

CoralConnect is a live booth. You walk up with your phone. A laptop beside you holds a reef.

Open the pair room. There is no host and no code to memorize. Two taps tell the room what you build and what you care about:

- Apps, Data, Systems, Hardware, or Design
- People, Planet, Trust, Speed, or Cost

The room pairs you with someone already waiting. Shared work counts first. Shared care counts next. Both phones light up with the same animal, a Seagull or a Turtle or a Dolphin, and you find that person in the crowd.

Grok then introduces you for real. It writes what you share, what only one of you brings, and a question about the environment to ask out loud when the round ends. Each phone holds a different function in the same small app. One of you sends the message. The other reports who is in the room. You have two minutes. You write one prompt together. Grok edits the file.

The reef on the laptop keeps the score.

- Name the file and the function, and the water stays clear.
- Leave a fact out, and that fact is charged as a web lookup of about 1,200 tokens. The reef wilts.
- Paste the whole file, and your own tokens count too. Length is not the same thing as care.
- Earn an A or an A+, and Grok Imagine paints a turtle or a coral bloom into the scene.

After every turn your phone shows a receipt: what the message included, what the model had to look up, the tokens that set the grade, and the carbon those tokens represent. The figure is a teaching model you can read on the spot: `0.0003 kWh` per 1,000 tokens, times `390 g CO2` per kWh, drawn again as if a million developers had sent the same prompt.

A second mode fills a compete table of up to ten people. Each phone has its own thread. The reef is still shared. The rounds put you inside work that already has an environmental stake:

- a farm whose water bill doubled
- a reef station muted by hundreds of heat alerts
- a cafe cooler burning the month's power
- a home battery empty by 9 pm, buying the most expensive electricity
- real debugging threads, including a handler that must never paste a live credential into the chat

The pair board at the side of the booth keeps every finished team. People can pair again. The reef remembers.

## How we built it

CoralConnect is a full-stack booth you can run in one command and open on a phone across the room.

The frontend is Next.js and TypeScript. It is the whole stage:

- the walk-up pair room
- the phone controller, with a shared prompt both people can type
- the admin console and join QR
- the main-stage aquarium, from thriving water down to sludge
- the live pair board
- the receipt, the grade, and the generated reward art

The backend is FastAPI and Python. It runs sessions, pairing, reef health, and the carbon grade. Game state stays live across reloads. Phones and the stage stay in sync over a WebSocket.

Grok is the model inside the experience, and it has a job on every beat:

- it edits the pair's project file from the prompt they wrote
- it answers a debugging thread the way a coding agent would
- it reviews the prompt against the round's facts
- it introduces the pair in their own words
- Grok Imagine paints the turtle or the bloom when the turn earns it

The judge is four layers, and it is the same judge on the phone, on the stage, and on the API. It counts tokens. It checks the facts that round requires. It asks Grok to review the message. On a full reading it measures the real run, including any web search the model actually performed. The rules set the floor. A flattering sentence cannot buy a higher grade. Credentials are stripped before any text reaches the model, the thread, or the other phone.

The public home of the project is [coralconnectgt.tech](https://coralconnectgt.tech). That `.tech` name is the join link on the QR, so a phone in the crowd opens the booth directly.

## Challenges we ran into

The first hard problem was making the grade mean something. A single keyword like "fix the 500" sounds specific and still forces the model to guess the file, the branch, and the fact. We built each round around the facts a careful prompt has to carry, and we taught every fact to accept the many ways a person might say it. Every sample prompt is tested, so a vague line and a precise one cannot land in the same band.

The second problem was flattery. If the model could raise a score, the winning move would be to ask for an A+. The reviewer and the measured run can add the cost of a real search. They cannot erase a lookup the message already earned. The reef only moves when the work was real.

The third problem was the room itself. Strangers will not wait for an organizer with a microphone. The pair room stands open. It matches on the two taps, puts the same animal on both phones, and starts a two-minute clock when both people tap Start. Each person can see only their own function, so the prompt is something they have to build together.

The fourth problem was trust in the number. A carbon claim that arrives as a vibe gets waved off. We put the arithmetic on the receipt, in tokens first and grams second, and we scale the waste to a million developers so the reef is a picture of a habit, not a single unlucky prompt.

## Accomplishments that we're proud of

We are proud that CoralConnect feels like a place you walk into, not a chat window you demo.

A person can tap two answers, find a stranger by an animal name, hear what they have in common, finish a small app in two minutes, read a receipt, and watch a reef change because of the sentence they wrote. The pair board fills behind them. The next pair is already waiting.

We are proud of the judge. It sees the lookup a person would otherwise miss, prices it, and draws it. That is the whole idea of an oracle: the hidden work, made visible. Grok writes the code, names the connection, and paints the reward. The AI is the product, not a caption on the side.

We are proud of the safety in the small things. A secret pasted into the chat is a failing grade, and it never leaves the server. The answer key for a round stays on the server too. Players get a hint about what is missing. They do not get the solution handed back.

We are also proud that the same reef teaches two lessons at once. It is a picture of wasted computation, and it is a picture of water, heat, power, and a battery that should have lasted the night. The social round ends with a question about the environment, asked out loud, by two people who just met.

## What we learned

A short prompt can cost more than a long one. The expensive part is the search the message refuses to do itself.

One message is not a debugging session. The interesting failure arrives second, after the model has already answered, when the follow-up has to carry a new fact.

Connection needs a reason to stand up. Matching two dropdowns is not an introduction. The introduction is the animal you have to find, the function you cannot see on your own phone, and the question you ask before you split up.

People trust a number they can recompute. The reef is memorable because the receipt is plain.

## What's next for CoralConnect

CoralConnect stays up at [coralconnectgt.tech](https://coralconnectgt.tech) as a public pair room. The board will be filled with real teams.

The next steps are whole products we left on the dock:

- **The MCP we first imagined.** A Model Context Protocol server that any coding agent can call before it sends a prompt. It runs the same judge as the booth and returns the receipt: tokens, the facts still missing, the carbon, and what the reef would do. The agent can hold the call when the water would take sludge. Installing it is how CoralConnect leaves the floor and sits beside the model all week.
- **One ocean for the whole market.** Every pair and every compete table writes into a single reef that lives at coralconnectgt.tech for the event. You walk up and inherit the sea the last team left behind. A public tide chart names who healed it and who dumped sludge, and the health bar on the stage is the crowd's, not one table's.
- **A season, not a round.** A match is four tides in a row: the farm's water, the reef station, the cafe cooler, and the home battery. Damage carries. A careful prompt in the last tide can still bring a dying ocean back. The pair gets one receipt for the whole season, and the board ranks seasons, not single turns.

Our long-term vision is a room where every prompt shows its cost, and every stranger leaves with someone they actually talked to.