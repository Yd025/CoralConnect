# CoralConnect problem sets

Five role-play rounds for the booth. Each one gives the player a role, a real-looking dashboard or log, and a problem to fix by prompting Grok. The plugin judges each prompt: is it specific enough for Grok to act on, and how many tokens did it save or waste?

This file is generated from `backend/app/challenges.py` (`PROBLEM_SETS`), so the numbers below are what the game actually scores. The four code-debugging rounds (`DEV_CHALLENGES`) are still in the game after these.

## How a round works

1. The player gets a role and a data card (a dashboard, a report, or a log).
2. They write a prompt asking Grok to fix the problem. Grok answers.
3. The plugin judges the prompt: horrible, okay, or efficient, and how many tokens it saved or wasted.
4. A twist arrives (turn 2), and they prompt again. In Collaborate mode, the pair shares one draft.

## How the judge scores a prompt

Each turn has **2 key details**. A good prompt names both, plus what the player wants done.

- **Each missing detail costs about 1,200 tokens**, because Grok has to go look for it or guess.
- **No ask** (never says what they want) costs 250.
- **The message's own tokens count too,** so pasting the whole card isn't free.
- **Saved** = the vague prompt's total minus this prompt's total.

| Tokens Grok handles | Grade |
| --- | --- |
| up to 200 | A+ |
| up to 400 | A |
| up to 800 | B |
| up to 1,400 | C (one detail missing) |
| up to 2,200 | D |
| more | F (both details missing) |

## For the plugin

Until the plugin is wired in, `backend/app/grading.py` does this judging. To let the plugin judge instead, send it:

- the player's prompt
- the round's key details (the numbered list under each turn below; the game sends these as `beat.anchors`)

and have it return: a verdict (efficient, okay, or horrible), the tokens it thinks Grok will spend, which details are missing, and a shorter version of the prompt that still names every detail. The game can then show "This prompt saved 2,370 tokens" or "This prompt is horrible: Grok has to guess the zone."

## Summary

| # | Round | Role | Turn 1 problem | Turn 2 twist |
| --- | --- | --- | --- | --- |
| 1 | The thirsty farm (`farm-water`) | Farmer | Zone 3's valve stays open 9 hours | A dead sensor stops all watering |
| 2 | Reef station alarm spam (`reef-alerts`) | Reef scientist | Heat alert texts every 5 minutes | A real bleaching week gets missed |
| 3 | The cafe's power bill (`cafe-cooler`) | Cafe owner | Cooler door left open 3 hours a day | Thermostat too cold, dirty coil |
| 4 | Club sign-ups are broken (`signup-crash`) | Club webmaster | Phones crash on a KeyError | 31 people signed up twice |
| 5 | The solar battery dies by 9 pm (`solar-battery`) | Homeowner | EV charging drains the battery at peak | Cloudy days leave the car at 40% |

## 1. The thirsty farm

**Role:** Farmer. You run Green Acres Farm. The water bill doubled and the pond is dropping fast. Ask Grok to find what's wasting water and fix it.

**Hint shown to players:** Name the zone and what the numbers show. 'Fix my water' makes Grok guess.

### Turn 1

**On the phone:** You're the farmer. Your irrigation dashboard is below. Ask Grok to stop the waste. A good prompt names the zone and what its numbers show.

**The lines that matter on the card:**

```
Z3    tomatoes   V3     02:00 for 90 min   540 min      44%
11:00  V3 close   (closed by hand, Sam)
```

**Key details a good prompt names:**

1. Where: zone 3 (tomatoes), valve V3
2. What's wrong: V3 stays open 9 hours, not 90 minutes

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| My water bill is too high. Can you fix my irrigation? | 2,414 | F | Horrible. Grok has to go find where and what's wrong: about 2,414 tokens of searching and guessing. |
| Zone 3 is using too much water. How do I fix it? | 1,212 | C | Okay, but it leaves out what's wrong, so Grok looks that up (+1,200). Saves 1,202 tokens vs the vague prompt. |
| Zone 3 valve V3 stays open 9 hours a day; soil at 44%. | 264 | A | Specific, but it never says what you want (+250). Saves 2,150 tokens vs the vague prompt. |
| Zone 3 valve V3 stays open 9 hours a day instead of 90 minutes, and soil is at 44%. Close it after 90 minutes and turn the rain skip rule back on. | 37 | A+ | Efficient. Grok has what it needs. Saves 2,377 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): Zone 3's valve V3 opens at 02:00 and stays open until someone closes it by hand at 11:00, about 9 hours instead of 90 minutes. Check the V3 close command or replace the valve, and turn the rain skip rule back on.

### Turn 2 (the twist)

**On the phone:** The valve is fixed. Now zone 3 hasn't been watered in three days and the tomatoes are wilting. The controller log is below. Follow up. Grok already has your last message.

**The lines that matter on the card:**

```
sensor S3: last reading change Tue 14:12 (flat since then)
hand probe check, Sat 09:00: 12% (dry)
```

**Key details a good prompt names:**

1. The broken part: sensor S3 (battery 2%)
2. The evidence: stuck at 44%, real soil is 12%, so it skips

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| The tomatoes look sad now. Help? | 2,408 | F | Horrible. Grok has to go find the broken part and the evidence: about 2,408 tokens of searching and guessing. |
| The tomatoes wilt because the controller skips watering every day. What should I do? | 1,221 | C | Okay, but it leaves out the broken part, so Grok looks that up (+1,200). Saves 1,187 tokens vs the vague prompt. |
| Sensor S3 is stuck at 44% with a 2% battery; a hand probe reads 12%. | 267 | A | Specific, but it never says what you want (+250). Saves 2,141 tokens vs the vague prompt. |
| Sensor S3 has been stuck at 44% since Tuesday (battery 2%), but a hand probe reads 12%, so the controller skips every watering. Replace the battery and water zone 3 on the timer until the sensor reads right. | 52 | A+ | Efficient. Grok has what it needs. Saves 2,356 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): Sensor S3 froze at 44% on Tuesday when its battery died, so the controller thinks the soil is wet and skips. Replace the battery, check it against a hand probe, and run zone 3 on the timer until the readings match.

## 2. Reef station alarm spam

**Role:** Reef scientist. You're the marine scientist at Buoy 7, a reef monitoring station. Your phone got 212 heat alerts overnight, so the team muted it. Ask Grok to fix the alerts.

**Hint shown to players:** Name the rule and how often it fires. 'Fix my alerts' makes Grok guess which one.

### Turn 1

**On the phone:** You're the reef scientist. The alert rules and last night's log are below. Ask Grok to fix the alert flood. A good prompt names the rule and how often it fires.

**The lines that matter on the card:**

```
rule R1  water_temp > 29.0 C    check every 5 min    notify: SMS on every check
texts sent overnight: 212 (all from R1)
```

**Key details a good prompt names:**

1. Which rule: R1, water temperature above 29.0 C
2. What's wrong: it texts on every 5-minute check (212 overnight)

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| My reef alerts are out of control. Please fix them. | 2,413 | F | Horrible. Grok has to go find which rule and what's wrong: about 2,413 tokens of searching and guessing. |
| Rule R1 keeps texting me all night. How do I fix it? | 1,213 | C | Okay, but it leaves out what's wrong, so Grok looks that up (+1,200). Saves 1,200 tokens vs the vague prompt. |
| Rule R1 sends an SMS every 5 minutes: 212 texts overnight. | 265 | A | Specific, but it never says what you want (+250). Saves 2,148 tokens vs the vague prompt. |
| Rule R1 (water_temp > 29.0 C) sends an SMS on every 5-minute check, which was 212 texts last night. Change it to notify once when it crosses 29.0 C, then at most once an hour. | 44 | A+ | Efficient. Grok has what it needs. Saves 2,369 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): R1 sends an SMS on every 5-minute check while the water stays above 29.0 C, so one warm night makes 212 texts. Notify once when the temperature crosses 29.0 C, then at most once an hour while it stays above.

### Turn 2 (the twist)

**On the phone:** R1 now texts once an hour. But last week the water went above 30 C for three days, the bleaching warning sign, and nobody noticed. The week's log is below. Follow up.

**The lines that matter on the card:**

```
every text says: "R1: water_temp above 29.0"
Thu   30.4 C           24
```

**Key details a good prompt names:**

1. The real danger: above 30 C for 3+ days (bleaching watch)
2. Why it was missed: 24 identical texts a day, no separate warning

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| The alerts still aren't working. Fix them please. | 2,413 | F | Horrible. Grok has to go find the real danger and why it was missed: about 2,413 tokens of searching and guessing. |
| We missed the bleaching warning last week. How do we catch it next time? | 1,218 | C | Okay, but it leaves out why it was missed, so Grok looks that up (+1,200). Saves 1,195 tokens vs the vague prompt. |
| All 24 daily texts read the same, even when the water sat above 30 C for 3 days (bleaching watch). | 275 | A | Specific, but it never says what you want (+250). Saves 2,138 tokens vs the vague prompt. |
| The texts all say 'above 29.0', 24 a day, so nobody noticed the water stayed over 30 C for 3 days, which is bleaching watch. Add a second alert that fires once after 3 days above 30 C, with a different message. | 53 | A+ | Efficient. Grok has what it needs. Saves 2,360 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): Every R1 text says the same thing, so a 30 C bleaching week looks like any warm night. Add rule R5: one message, to a different channel, when water_temp stays above 30.0 C for 3 days, and keep R1 as a daily summary.

## 3. The cafe's power bill

**Role:** Cafe owner. You own the Corner Cafe. This month's electric bill jumped from $431 to $612. Ask Grok what's burning the power and how to stop it.

**Hint shown to players:** Name the machine and what its numbers show. 'Lower my bill' makes Grok guess.

### Turn 1

**On the phone:** You're the cafe owner. The smart plug report is below. Ask Grok to find the waste. A good prompt names the machine and what changed.

**The lines that matter on the card:**

```
walk-in cooler     612    +71%            22 h (compressor)
week 1: 24 min    week 2: 27 min    week 3: 2 h 55 min    week 4: 3 h 10 min
```

**Key details a good prompt names:**

1. Which machine: the walk-in cooler
2. What changed: door open 3 hours a day (was 25 min), +71%

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| My electric bill went up a lot this month. Can you help me cut it? | 2,417 | F | Horrible. Grok has to go find which machine and what changed: about 2,417 tokens of searching and guessing. |
| My walk-in cooler is using a lot more power. What should I do? | 1,216 | C | Okay, but it leaves out what changed, so Grok looks that up (+1,200). Saves 1,201 tokens vs the vague prompt. |
| Walk-in cooler: door open 3 h a day (was 25 min), compressor running 22 h, 612 kWh (+71%). | 273 | A | Specific, but it never says what you want (+250). Saves 2,144 tokens vs the vague prompt. |
| The walk-in cooler's door is open 3 hours a day now (it was 25 minutes), so the compressor runs 22 hours and used 612 kWh, up 71%. How do I stop the door being left open? | 43 | A+ | Efficient. Grok has what it needs. Saves 2,374 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): The walk-in cooler jumped 71% because its door has been open about 3 hours a day since week 3, so the compressor runs 22 hours. Add a door alarm or self-closing hinge and show the new morning staff to prop it shut.

### Turn 2 (the twist)

**On the phone:** The door alarm works. The door is open 20 minutes a day, but the cooler still uses far more power than it used to. The new readings are below. Follow up.

**The lines that matter on the card:**

```
thermostat setpoint: 1.0 C  (changed Mar 3 by "staff")
condenser coil last cleaned: 14 months ago (dusty)
```

**Key details a good prompt names:**

1. Cause 1: thermostat set to 1.0 C (standard is 4 C)
2. Cause 2: condenser coil not cleaned in 14 months

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| The bill is still high. What else can I do? | 2,411 | F | Horrible. Grok has to go find cause 1 and cause 2: about 2,411 tokens of searching and guessing. |
| The cooler thermostat is set to 1 C now. Should I change it? | 1,215 | C | Okay, but it leaves out cause 2, so Grok looks that up (+1,200). Saves 1,196 tokens vs the vague prompt. |
| Setpoint is 1.0 C, not 4 C, and the condenser coil was last cleaned 14 months ago. | 271 | A | Specific, but it never says what you want (+250). Saves 2,140 tokens vs the vague prompt. |
| The thermostat was changed to 1.0 C (our standard is 4 C), and the condenser coil hasn't been cleaned in 14 months. Is that why the compressor still runs 17 hours? What should I fix first? | 47 | A+ | Efficient. Grok has what it needs. Saves 2,364 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): Two things: the setpoint was dropped to 1.0 C, which makes the compressor work much harder than at 4 C, and a coil that hasn't been cleaned in 14 months can't shed heat. Set it back to 4 C first, then clean the coil.

## 4. Club sign-ups are broken

**Role:** Club webmaster. You run the robotics club website. Sign-ups opened tonight, and everyone on a phone gets 'Something went wrong.' Ask Grok to fix it.

**Hint shown to players:** Name the error and why only phones hit it. 'The site is broken' makes Grok search.

### Turn 1

**On the phone:** You're the club webmaster. The server log is below. Ask Grok to fix the phone sign-ups. A good prompt names the error line and why phones fail.

**The lines that matter on the card:**

```
KeyError: 'email'   (app.py, line 42, in signup)
templates/signup_mobile.html:     name="Email"
```

**Key details a good prompt names:**

1. The error: KeyError 'email' in signup(), app.py line 42
2. Why phones fail: the mobile form names the field "Email"

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| Our sign-up page is broken for some people. Please fix it. | 2,415 | F | Horrible. Grok has to go find the error and why phones fail: about 2,415 tokens of searching and guessing. |
| Phones get a KeyError: 'email' on line 42 when they sign up. How do I fix it? | 1,220 | C | Okay, but it leaves out why phones fail, so Grok looks that up (+1,200). Saves 1,195 tokens vs the vague prompt. |
| KeyError: 'email' at app.py line 42; the mobile form's field is "Email" with a capital E. | 273 | A | Specific, but it never says what you want (+250). Saves 2,142 tokens vs the vague prompt. |
| signup() in app.py line 42 crashes with KeyError: 'email' because the mobile form names the field "Email" with a capital E. Rename the mobile field to "email". | 40 | A+ | Efficient. Grok has what it needs. Saves 2,375 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): signup() reads request.form['email'], but signup_mobile.html names the field 'Email', so phones raise a KeyError. Rename the mobile field to name="email".

### Turn 2 (the twist)

**On the phone:** Phones can sign up now. But 31 people are signed up twice, and club emails go out doubled. The table is below. Follow up.

**The lines that matter on the card:**

```
duplicates: 31 pairs, almost all 1 second apart
database: no unique constraint on email
```

**Key details a good prompt names:**

1. Why: double taps, 1 second apart, button stays clickable
2. What lets it through: no unique constraint on email

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| Some people are signed up twice. Fix it? | 2,410 | F | Horrible. Grok has to go find why and what lets it through: about 2,410 tokens of searching and guessing. |
| People tap the sign-up button twice and get two rows. How do we stop that? | 1,219 | C | Okay, but it leaves out what lets it through, so Grok looks that up (+1,200). Saves 1,191 tokens vs the vague prompt. |
| Duplicates are 1 second apart (double taps), and there is no unique constraint on email, even across Ben@/ben@ case. | 279 | A | Specific, but it never says what you want (+250). Saves 2,131 tokens vs the vague prompt. |
| The 31 duplicates are about 1 second apart, so people double-tap the button on slow Wi-Fi, and the email column has no unique constraint (Ben@ and ben@ both got in). Disable the button after the first tap and add a unique index on lower(email). | 61 | A+ | Efficient. Grok has what it needs. Saves 2,349 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): The pairs are one second apart, so people double-tap on slow Wi-Fi, and nothing stops a second row. Disable the button after the first tap, and add a unique index on lower(email).

## 5. The solar battery dies by 9 pm

**Role:** Homeowner. Your family has solar panels and a home battery. The battery is empty by 9 pm every night, so the house buys the most expensive power. Ask Grok to fix the schedule.

**Hint shown to players:** Name the device and its schedule. 'My battery dies' makes Grok guess.

### Turn 1

**On the phone:** You're the homeowner. The energy app is below. Ask Grok why the battery runs out and what to change. A good prompt names the device and its schedule.

**The lines that matter on the card:**

```
EV charger      7.2 kW   schedule: 18:00-21:00 daily   source: battery first
```

**Key details a good prompt names:**

1. Which device: the EV charger
2. What's wrong: it charges 18:00-21:00 at 7.2 kW from the battery

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| Our solar battery dies every night. Can you help? | 2,413 | F | Horrible. Grok has to go find which device and what's wrong: about 2,413 tokens of searching and guessing. |
| The EV charger empties our home battery. What should we change? | 1,216 | C | Okay, but it leaves out what's wrong, so Grok looks that up (+1,200). Saves 1,197 tokens vs the vague prompt. |
| EV charger: 7.2 kW, 18:00-21:00 daily, battery first. | 264 | A | Specific, but it never says what you want (+250). Saves 2,149 tokens vs the vague prompt. |
| The EV charger is scheduled 18:00-21:00 at 7.2 kW with 'battery first', so it drains the home battery at peak price. Move charging to 11:00-15:00 on solar, or 23:00 off-peak from the grid. | 47 | A+ | Efficient. Grok has what it needs. Saves 2,366 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): The EV charger pulls 7.2 kW from 18:00 to 21:00 with 'battery first', which empties 13.5 kWh in about two hours. Move charging to 11:00-15:00 when solar is spare, or to 23:00 off-peak, and set it to grid-only.

### Turn 2 (the twist)

**On the phone:** Charging moved to 11:00-15:00 on solar. On cloudy days the car is only at about 40% by morning, and the commute needs 70%. The log is below. Follow up.

**The lines that matter on the card:**

```
Tue   cloudy     9           6 kWh          41%
off-peak grid: 23:00-07:00 at $0.11 per kWh
```

**Key details a good prompt names:**

1. The gap: cloudy days leave the car near 40%, commute needs 70%
2. The fix window: off-peak grid, 23:00-07:00 at $0.11

| Prompt | Tokens Grok handles | Grade | What the plugin says |
| --- | --- | --- | --- |
| The car isn't charged sometimes. Help? | 2,410 | F | Horrible. Grok has to go find the gap and the fix window: about 2,410 tokens of searching and guessing. |
| On cloudy days the car doesn't charge enough. What should we do? | 1,216 | C | Okay, but it leaves out the fix window, so Grok looks that up (+1,200). Saves 1,194 tokens vs the vague prompt. |
| Cloudy days: car at 35-41% by 07:00, commute takes 70%; off-peak is 23:00-07:00 at $0.11. | 273 | A | Specific, but it never says what you want (+250). Saves 2,137 tokens vs the vague prompt. |
| On cloudy days solar only gets the car to about 40% by 07:00, and the commute needs 70%. Keep solar charging, but top up from the grid off-peak (23:00-07:00) whenever it's under 70% at 21:00. | 48 | A+ | Efficient. Grok has what it needs. Saves 2,362 tokens vs the vague prompt. |

**Grok's stand-in answer** (used when there's no API key): Keep solar charging from 11:00 to 15:00, and add a rule: if the car is under 70% at 21:00, top it up from the grid between 23:00 and 07:00 at the $0.11 off-peak rate.

## Adding a new problem

Copy one of the `Challenge(...)` blocks in `PROBLEM_SETS`, write its data card, its 2 facts per turn (with several phrasings each), and its 4 sample prompts. Then run `cd backend && python -m pytest -q`. The tests check that every sample lands in its grade band. Regenerate this file with `cd backend && python scripts/problem_sets_doc.py`.
