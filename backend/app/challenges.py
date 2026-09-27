"""Challenges the booth can run.

PROBLEM_SETS are role-play rounds (farmer, reef scientist, cafe owner, club
webmaster, homeowner). DEV_CHALLENGES are code-debugging rounds. The admin
dropdown lists both, role-play first. See PROBLEM-SETS.md at the repo root.

Add a Challenge to PROBLEM_SETS or DEV_CHALLENGES when you design a new round.

Each beat is one turn. A beat lists the facts the latest message has to carry
so the model can answer without going to look them up. Every missing fact is
charged as one web lookup (see grading.py). Facts, forbidden patterns, and the
sample prompts stay on the server. Phones only receive ask, fixtureTitle,
fixture, and targetTokens, plus their own piece in collaborate mode.

Compete mode shows the fixture to every phone. Collaborate mode deals parts:
each person in a pair gets a different piece (role, title, body), and the
shared message has to carry every part's anchor. In collaborate mode a beat is
graded on its facts plus each part anchor those facts don't already cover
(grading.beat_for). Role-play rounds can use parts too: set Part.role to the
character, put a fact only that character knows in body, and set anchor to
the phrase the shared message must include from that piece.

simulated_reply is the answer used until XAI_API_KEY is set.

When you add a beat, also write its Samples. tests/test_grading.py checks that
every beat grades its samples in order: adequate beats bare beats partial beats
vague. If a sample lands in the wrong band, fix the fact patterns, not the test.
"""

from __future__ import annotations

from .round_types import Beat, Challenge, Fact, Part, Samples

# A credential in any form other than a placeholder. "Bearer <token>",
# "Bearer [redacted]", and "Bearer header" are fine.
BEARER_VALUE = (
    r"bearer\s+(?!(?:<|\[|\{|\(|\*|x{3}|redacted|token\b|header|credential|value))"
    r"[a-z0-9._~+/=-]{8,}"
)
DEMO_SECRET = "demo-token-not-real"


INVOICE_FILE = """\
def subtotal(lines):
    return sum(item["qty"] * item["price"] for item in lines)

def apply_coupon(amount, coupon):
    if not coupon:
        return amount
    return round(amount * (1 - coupon["percent"] / 100), 2)

def tax(amount, account):
    rate = account.get("tax_rate", 0.08)
    return round(amount * (1 + rate), 2)

def total(lines, account, coupon):
    base = subtotal(lines)
    taxed = tax(base, account)
    return apply_coupon(taxed, coupon)

def format_invoice(lines, account, coupon):
    due = total(lines, account, coupon)
    rows = [f"{item['sku']} x{item['qty']} @ {item['price']}" for item in lines]
    rows.append(f"account={account['id']} exempt={account.get('tax_exempt', False)}")
    rows.append(f"due={due}")
    return "\\n".join(rows)
"""

INVOICE_FOLLOWUP = """\
FAIL test_tax_exempt_skips_tax
account={'id': 'acme', 'tax_exempt': True, 'tax_rate': 0.08}
lines=[{'sku': 'WIDGET', 'qty': 1, 'price': 100}]
coupon={'percent': 10}
expected due=90.00
actual due=97.20
note: yesterday's patch discounts before tax, but exempt accounts still pay 8%
"""

PROFILE_FILE = """\
export function AccountHeader({ profile, onEdit }) {
  const name = profile.user.name;
  const plan = profile.user.plan ?? "free";
  return (
    <header>
      <img src={profile.user.avatar} alt="" />
      <h1>{name}</h1>
      <p>{plan}</p>
      <button onClick={() => onEdit(profile.user.id)}>Edit</button>
    </header>
  );
}
"""

PROFILE_FOLLOWUP = """\
Sentry follow-up, 10 minutes after the null guard shipped
AccountHeader returns null while profile.status === "loading"
When the request finishes, the header stays blank and Edit never mounts
profile.status values: "loading" | "ready" | "error"
"""

MIGRATION_FILE = """\
-- migrations/014_invoices.sql
ALTER TABLE invoices ADD COLUMN coupon_code text;
UPDATE invoices SET coupon_code = '' WHERE coupon_code IS NULL;
CREATE UNIQUE INDEX invoices_coupon_code_idx ON invoices (coupon_code);
"""

MIGRATION_LOG = """\
ERROR: could not create unique index "invoices_coupon_code_idx"
DETAIL: Key (coupon_code)=() is duplicated.
STATEMENT: CREATE UNIQUE INDEX invoices_coupon_code_idx ON invoices (coupon_code);
CONTEXT: migration 014_invoices, deploy 18:04 UTC
"""

MIGRATION_FOLLOWUP = """\
deploy retry, 18:11 UTC
ERROR: relation "invoices_coupon_code_idx" already exists
CONTEXT: migration 014 was half-applied. The UPDATE ran. The unique index was created on the second attempt's leftover, then the job died.
Need a follow-up migration, not a rerun of 014.
"""

EXPORT_HANDLER = """\
def handle_export(request):
    account_id = request.args.get("account_id", "")
    credential = request.headers.get("Authorization", "")
    logger.info("export started account=%s credential=%s", account_id, credential)
    try:
        rows = load_rows(account_id)
        return {"rows": rows}
    except Exception as exc:
        return {"error": str(exc), "headers": dict(request.headers)}, 500

# Datadog sample, 14:02 UTC
# INFO export started account=acme credential=Bearer demo-token-not-real
"""

EXPORT_FOLLOWUP = """\
Incident, 20 minutes later
The info log no longer contains Authorization.
A failed export still returned HTTP 500 with the raw header map.
Someone copied that JSON into the support Slack channel.
Sample value in the ticket: Authorization: Bearer demo-token-not-real
"""


def _with_noise(body: str, label: str) -> str:
    """Extra callers and notes, so the real source is buried the way it is in a repo."""
    lines = [body.rstrip(), "", f"# unrelated {label} context that usually gets pasted with the file"]
    for index in range(1, 55):
        lines.append(
            f"# caller {index}: nightly backfill still imports {label} "
            "and logs the full payload before the small fix"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Role-play problem sets
#
# Each one puts the player in a role with a real-looking dashboard or log.
# The player asks Grok to fix it. A good prompt names the two key details on
# the card; the plugin (and grading.py until the plugin is wired in) judges it.
# The cards are long on purpose: pasting the whole card costs tokens, quoting
# the one line that matters doesn't.
# ---------------------------------------------------------------------------

FARM_DASHBOARD = """\
GREEN ACRES FARM · irrigation dashboard · last 7 days
target soil moisture: 25-30%      rain skip rule: OFF (turned off in July)
rain this week: 22 mm (Tue 14 mm, Thu 8 mm)
water use this week: 412,000 L    (usual week: 190,000 L)
pond level: 38%   (two weeks ago: 71%)

zone  crop       valve  schedule         runtime/day  soil moisture
Z1    corn       V1     05:00 for 30 min   30 min       27%
Z2    corn       V2     05:00 for 30 min   30 min       26%
Z3    tomatoes   V3     02:00 for 90 min   540 min      44%
Z4    beans      V4     05:30 for 25 min   25 min       29%
Z5    squash     V5     06:00 for 20 min   20 min       28%
Z6    orchard    V6     04:00 for 45 min   45 min       31%

valve log, Thursday
02:00  V3 open    (Z3 schedule)
04:00  V6 open    (Z6 schedule)
04:45  V6 close
05:00  V1 open    (Z1 schedule)
05:00  V2 open    (Z2 schedule)
05:30  V1 close
05:30  V2 close
05:30  V4 open    (Z4 schedule)
05:55  V4 close
06:00  V5 open    (Z5 schedule)
06:20  V5 close
11:00  V3 close   (closed by hand, Sam)

valve log, Friday
02:00  V3 open    (Z3 schedule)
04:00  V6 open    (Z6 schedule)
04:45  V6 close
05:00  V1 open    (Z1 schedule)
05:00  V2 open    (Z2 schedule)
05:30  V1 close
05:30  V2 close
05:30  V4 open    (Z4 schedule)
05:55  V4 close
06:00  V5 open    (Z5 schedule)
06:20  V5 close
11:00  V3 close   (closed by hand, Sam)

pump pressure: 3.1 bar (normal)     filter: clean (checked Mon)
alerts: "V3 open longer than schedule" x7 (all dismissed)
"""

FARM_FOLLOWUP = """\
ZONE 3 controller log, after the valve fix
Thu 02:00  skip watering: soil moisture 44% > 30% target
Fri 02:00  skip watering: soil moisture 44% > 30% target
Sat 02:00  skip watering: soil moisture 44% > 30% target
sensor S3: last reading change Tue 14:12 (flat since then)
sensor S3 battery: 2%
hand probe check, Sat 09:00: 12% (dry)
the tomatoes are wilting
"""

REEF_ALERTS = """\
REEF WATCH · Buoy 7 · alert rules
rule R1  water_temp > 29.0 C    check every 5 min    notify: SMS on every check
rule R2  pH < 7.90              check every 15 min   notify: email once a day
rule R3  turbidity > 12 NTU     check every 10 min   notify: SMS once an hour
rule R4  battery < 20%          check every 60 min   notify: email

overnight readings, water_temp (C)
00:05 29.1  SMS    00:10 29.1  SMS    00:15 29.2  SMS    00:20 29.1  SMS
00:25 29.1  SMS    00:30 29.2  SMS    00:35 29.2  SMS    00:40 29.2  SMS
00:45 29.1  SMS    00:50 29.1  SMS    00:55 29.2  SMS    01:00 29.2  SMS
01:05 29.2  SMS    01:10 29.3  SMS    01:15 29.2  SMS    01:20 29.2  SMS
01:25 29.2  SMS    01:30 29.3  SMS    01:35 29.3  SMS    01:40 29.2  SMS
01:45 29.2  SMS    01:50 29.2  SMS    01:55 29.3  SMS    02:00 29.3  SMS
... 164 more readings, all above 29.0, all SMS ...
07:40 29.3  SMS    07:45 29.2  SMS    07:50 29.3  SMS    07:55 29.3  SMS

other readings overnight
pH: 8.02 to 8.05 (fine)
turbidity: 4 to 6 NTU (fine)
salinity: 35.1 PSU (fine)
battery: 81%

texts sent overnight: 212 (all from R1)
the team muted the SMS number at 03:00
bleaching watch: water above 30.0 C for 3 or more days
"""

REEF_FOLLOWUP = """\
Buoy 7 · the week after R1 was changed to one SMS per hour
day   max water_temp   texts from R1
Mon   29.4 C           24
Tue   29.8 C           24
Wed   30.2 C           24
Thu   30.4 C           24
Fri   30.3 C           24
every text says: "R1: water_temp above 29.0"
nobody noticed Wed to Fri, which is bleaching watch (above 30.0 C for 3+ days)
"""

CAFE_REPORT = """\
CORNER CAFE · smart plug energy report · last 30 days
electric bill: $612   (last month: $431)   rate: $0.17 per kWh

device             kWh    vs last month   runs per day
espresso machine    96    +2%             9 h
grinder             11    0%              2 h
dishwasher          54    -1%             3 h
walk-in cooler     612    +71%            22 h (compressor)
display fridge      88    +3%             24 h (normal for it)
ice machine         73    +1%             24 h
ovens              210    +4%             6 h
toaster             19    0%              2 h
lights             140    0%              13 h
HVAC               380    +5%             11 h
music + wifi        22    0%              24 h

walk-in cooler details
temperature: 3.9 C (setpoint 4.0 C)
door sensor, open time per day:
  week 1: 24 min    week 2: 27 min    week 3: 2 h 55 min    week 4: 3 h 10 min
door sensor note: open over 10 minutes at a time, 9 times a day, since week 3
new staff started week 3 (morning prep)

other notes
HVAC filter changed last month
dishwasher on eco mode
lights: LED since spring
"""

CAFE_FOLLOWUP = """\
walk-in cooler · the week after the door alarm went in
door open: 20 min per day (fixed)
compressor: 17 h per day   (old normal: 12 h)
month pace: 480 kWh        (old normal: 358 kWh)
temperature display: 1.0 C
thermostat setpoint: 1.0 C  (changed Mar 3 by "staff")
food safety range: 1-5 C   (cafe standard: 4 C)
condenser coil last cleaned: 14 months ago (dusty)
"""

SIGNUP_LOG = """\
ROBOTICS CLUB SITE · server.log · sign-ups opened 19:00
19:00:02 GET  /                  200
19:00:05 GET  /signup            200
19:00:41 POST /signup            200   desktop  Chrome
19:01:12 GET  /signup            200
19:01:30 POST /signup            500   iPhone   Safari
Traceback (most recent call last):
  File "app.py", line 42, in signup
    email = request.form["email"]
KeyError: 'email'
19:01:31 GET  /favicon.ico       404
19:02:03 POST /signup            200   desktop  Firefox
19:02:18 POST /signup            500   Android  Chrome
Traceback (most recent call last):
  File "app.py", line 42, in signup
    email = request.form["email"]
KeyError: 'email'
19:02:40 GET  /about             200
19:03:05 POST /signup            500   iPhone   Safari
Traceback (most recent call last):
  File "app.py", line 42, in signup
    email = request.form["email"]
KeyError: 'email'
19:03:10 GET  /static/logo.png   200
19:03:44 POST /signup            200   desktop  Edge

form fields
  templates/signup.html (desktop):  name="email"
  templates/signup_mobile.html:     name="Email"

today: 23 sign-ups from desktop, 0 from phones, 41 errors
"""

SIGNUP_FOLLOWUP = """\
signups table, sorted by email (after the phone fix)
id   email              created
14   ana@school.edu     19:40:02
15   ana@school.edu     19:40:03
16   ben@school.edu     19:41:10
17   Ben@school.edu     19:41:11
18   cho@school.edu     19:42:55
19   cho@school.edu     19:42:56
duplicates: 31 pairs, almost all 1 second apart
sign-up button: stays clickable after the first tap; school Wi-Fi is slow
database: no unique constraint on email
"""

SOLAR_APP = """\
HOME ENERGY APP · yesterday (sunny)
solar made: 31.2 kWh     home battery: 13.5 kWh
grid price: peak 17:00-21:00 $0.42 per kWh, off-peak 23:00-07:00 $0.11 per kWh
solar sold back 12:00-16:00: 9.8 kWh at $0.05

hour   solar kW   home use kW   battery
07:00  0.4        0.8           52%
08:00  1.5        0.7           58%
09:00  3.0        0.6           71%
10:00  4.4        0.6           86%
11:00  5.3        0.7           97%
12:00  5.8        0.9           100%
13:00  5.6        0.8           100%
14:00  5.1        0.9           100%
15:00  4.2        1.0           100%
16:00  3.0        1.1           100%
17:00  1.6        1.4           98%
18:00  0.6        9.5           71%
19:00  0.1        9.1           38%
20:00  0.0        8.9           9%
21:00  0.0        2.2           0%  (buying from grid at peak price)
22:00  0.0        1.5           0%
23:00  0.0        0.9           0%

big loads, 18:00-21:00
EV charger      7.2 kW   schedule: 18:00-21:00 daily   source: battery first
oven            2.1 kW   18:10-18:55
AC              1.4 kW   all evening
washer          0.5 kW   19:00-19:40

monthly: bought 212 kWh at peak price ($89)
"""

SOLAR_FOLLOWUP = """\
EV · last 5 days, charging moved to 11:00-15:00 on solar
day   weather   solar kWh   charged 11-15   car at 07:00
Mon   sunny     31          22 kWh          92%
Tue   cloudy     9           6 kWh          41%
Wed   cloudy     8           5 kWh          38%
Thu   sunny     30          21 kWh          90%
Fri   rain       5           3 kWh          35%
the commute needs 70%
off-peak grid: 23:00-07:00 at $0.11 per kWh
"""


PROBLEM_SETS: tuple[Challenge, ...] = (
    Challenge(
        id="farm-water",
        title="The thirsty farm",
        brief="You run Green Acres Farm. The water bill doubled and the pond is dropping fast. Ask Grok to find what's wasting water and fix it.",
        hint="Name the zone and what the numbers show. 'Fix my water' makes Grok guess.",
        beats=(
            Beat(
                ask="You're the farmer. Your irrigation dashboard is below. Ask Grok to stop the waste. A good prompt names the zone and what its numbers show.",
                fixture_title="Irrigation dashboard",
                fixture=FARM_DASHBOARD.strip(),
                facts=(
                    Fact(
                        "where",
                        "Where: zone 3 (tomatoes), valve V3",
                        ((r"\bz(one)?\s*-?\s*3\b", r"\bv\s*-?3\b", r"valve\s*3\b", r"tomato"),),
                    ),
                    Fact(
                        "what",
                        "What's wrong: V3 stays open 9 hours, not 90 minutes",
                        (
                            (
                                r"\b9\s*(h|hrs?|hours?)\b",
                                r"\bnine\s+hours?\b",
                                r"\b540\b",
                                r"\b44\s*%",
                                r"(stays?|stuck|left)\s+open",
                                r"open\s+(until|till)\s+11",
                                r"over[- ]?water",
                                r"\b90\s*min",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "Zone 3's valve V3 opens at 02:00 and stays open until someone closes it by hand at 11:00, about 9 hours "
                    "instead of 90 minutes. Check the V3 close command or replace the valve, and turn the rain skip rule back on."
                ),
                samples=Samples(
                    adequate="Zone 3 valve V3 stays open 9 hours a day instead of 90 minutes, and soil is at 44%. Close it after 90 minutes and turn the rain skip rule back on.",
                    bare="Zone 3 valve V3 stays open 9 hours a day; soil at 44%.",
                    partial="Zone 3 is using too much water. How do I fix it?",
                    vague="My water bill is too high. Can you fix my irrigation?",
                ),
            ),
            Beat(
                ask="The valve is fixed. Now zone 3 hasn't been watered in three days and the tomatoes are wilting. The controller log is below. Follow up. Grok already has your last message.",
                fixture_title="Zone 3 controller log",
                fixture=FARM_FOLLOWUP.strip(),
                facts=(
                    Fact("sensor", "The broken part: sensor S3 (battery 2%)", ((r"\bs\s*-?3\b", r"sensor", r"battery", r"probe"),)),
                    Fact(
                        "evidence",
                        "The evidence: stuck at 44%, real soil is 12%, so it skips",
                        (
                            (
                                r"\b44\s*%",
                                r"\b12\s*%",
                                r"\bflat\b",
                                r"\bstuck\b",
                                r"since\s+tue",
                                r"\bskip(s|ping|ped)?\b",
                                r"(hasn'?t|not|never)\s+water",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "Sensor S3 froze at 44% on Tuesday when its battery died, so the controller thinks the soil is wet and skips. "
                    "Replace the battery, check it against a hand probe, and run zone 3 on the timer until the readings match."
                ),
                samples=Samples(
                    adequate="Sensor S3 has been stuck at 44% since Tuesday (battery 2%), but a hand probe reads 12%, so the controller skips every watering. Replace the battery and water zone 3 on the timer until the sensor reads right.",
                    bare="Sensor S3 is stuck at 44% with a 2% battery; a hand probe reads 12%.",
                    partial="The tomatoes wilt because the controller skips watering every day. What should I do?",
                    vague="The tomatoes look sad now. Help?",
                ),
            ),
        ),
    ),
    Challenge(
        id="reef-alerts",
        title="Reef station alarm spam",
        brief="You're the marine scientist at Buoy 7, a reef monitoring station. Your phone got 212 heat alerts overnight, so the team muted it. Ask Grok to fix the alerts.",
        hint="Name the rule and how often it fires. 'Fix my alerts' makes Grok guess which one.",
        beats=(
            Beat(
                ask="You're the reef scientist. The alert rules and last night's log are below. Ask Grok to fix the alert flood. A good prompt names the rule and how often it fires.",
                fixture_title="Buoy 7 alert rules + overnight log",
                fixture=REEF_ALERTS.strip(),
                facts=(
                    Fact(
                        "where",
                        "Which rule: R1, water temperature above 29.0 C",
                        ((r"\br\s*-?1\b", r"rule\s*(one|1)\b", r"water[_ ]temp", r"temp(erature)?\s+(rule|alert)", r"\b29(\.0)?\s*(c\b|°)"),),
                    ),
                    Fact(
                        "what",
                        "What's wrong: it texts on every 5-minute check (212 overnight)",
                        ((r"every\s+(5|five)[\s-]*min", r"every\s+check", r"\b212\b", r"sms\s+(on\s+)?every"),),
                    ),
                ),
                simulated_reply=(
                    "R1 sends an SMS on every 5-minute check while the water stays above 29.0 C, so one warm night makes 212 texts. "
                    "Notify once when the temperature crosses 29.0 C, then at most once an hour while it stays above."
                ),
                samples=Samples(
                    adequate="Rule R1 (water_temp > 29.0 C) sends an SMS on every 5-minute check, which was 212 texts last night. Change it to notify once when it crosses 29.0 C, then at most once an hour.",
                    bare="Rule R1 sends an SMS every 5 minutes: 212 texts overnight.",
                    partial="Rule R1 keeps texting me all night. How do I fix it?",
                    vague="My reef alerts are out of control. Please fix them.",
                ),
            ),
            Beat(
                ask="R1 now texts once an hour. But last week the water went above 30 C for three days, the bleaching warning sign, and nobody noticed. The week's log is below. Follow up.",
                fixture_title="Buoy 7, the next week",
                fixture=REEF_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "signal",
                        "The real danger: above 30 C for 3+ days (bleaching watch)",
                        ((r"\b30(\.\d)?\s*(c\b|°)", r"bleach", r"\b3\+?\s*days\b", r"three\s+days"),),
                    ),
                    Fact(
                        "problem",
                        "Why it was missed: 24 identical texts a day, no separate warning",
                        (
                            (
                                r"\bsame\s+(text|message|alert|warning)",
                                r"\b24\b",
                                r"(look|read|say)s?\s+the\s+same",
                                r"identical",
                                r"sever",
                                r"escalat",
                                r"(different|separate|second|new)\s+(rule|alert|level|warning|message)",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "Every R1 text says the same thing, so a 30 C bleaching week looks like any warm night. Add rule R5: one "
                    "message, to a different channel, when water_temp stays above 30.0 C for 3 days, and keep R1 as a daily summary."
                ),
                samples=Samples(
                    adequate="The texts all say 'above 29.0', 24 a day, so nobody noticed the water stayed over 30 C for 3 days, which is bleaching watch. Add a second alert that fires once after 3 days above 30 C, with a different message.",
                    bare="All 24 daily texts read the same, even when the water sat above 30 C for 3 days (bleaching watch).",
                    partial="We missed the bleaching warning last week. How do we catch it next time?",
                    vague="The alerts still aren't working. Fix them please.",
                ),
            ),
        ),
    ),
    Challenge(
        id="cafe-cooler",
        title="The cafe's power bill",
        brief="You own the Corner Cafe. This month's electric bill jumped from $431 to $612. Ask Grok what's burning the power and how to stop it.",
        hint="Name the machine and what its numbers show. 'Lower my bill' makes Grok guess.",
        beats=(
            Beat(
                ask="You're the cafe owner. The smart plug report is below. Ask Grok to find the waste. A good prompt names the machine and what changed.",
                fixture_title="Smart plug energy report",
                fixture=CAFE_REPORT.strip(),
                facts=(
                    Fact("where", "Which machine: the walk-in cooler", ((r"walk[- ]?in", r"cooler", r"compressor"),)),
                    Fact(
                        "what",
                        "What changed: door open 3 hours a day (was 25 min), +71%",
                        ((r"\bdoor\b", r"\b3\s*h(ours?)?\b", r"\bthree\s+hours\b", r"\b612\s*kwh", r"\b71\s*%", r"\b22\s*h(ours?)?\b"),),
                    ),
                ),
                simulated_reply=(
                    "The walk-in cooler jumped 71% because its door has been open about 3 hours a day since week 3, so the "
                    "compressor runs 22 hours. Add a door alarm or self-closing hinge and show the new morning staff to prop it shut."
                ),
                samples=Samples(
                    adequate="The walk-in cooler's door is open 3 hours a day now (it was 25 minutes), so the compressor runs 22 hours and used 612 kWh, up 71%. How do I stop the door being left open?",
                    bare="Walk-in cooler: door open 3 h a day (was 25 min), compressor running 22 h, 612 kWh (+71%).",
                    partial="My walk-in cooler is using a lot more power. What should I do?",
                    vague="My electric bill went up a lot this month. Can you help me cut it?",
                ),
            ),
            Beat(
                ask="The door alarm works. The door is open 20 minutes a day, but the cooler still uses far more power than it used to. The new readings are below. Follow up.",
                fixture_title="Walk-in cooler, one week later",
                fixture=CAFE_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "setpoint",
                        "Cause 1: thermostat set to 1.0 C (standard is 4 C)",
                        ((r"thermostat", r"set\s*-?\s*point", r"\b1(\.0)?\s*(c\b|°)", r"set\s+to\s+1\b", r"too\s+cold"),),
                    ),
                    Fact("coil", "Cause 2: condenser coil not cleaned in 14 months", ((r"\bcoil", r"condenser", r"14\s+months", r"\bclean", r"dust"),)),
                ),
                simulated_reply=(
                    "Two things: the setpoint was dropped to 1.0 C, which makes the compressor work much harder than at 4 C, "
                    "and a coil that hasn't been cleaned in 14 months can't shed heat. Set it back to 4 C first, then clean the coil."
                ),
                samples=Samples(
                    adequate="The thermostat was changed to 1.0 C (our standard is 4 C), and the condenser coil hasn't been cleaned in 14 months. Is that why the compressor still runs 17 hours? What should I fix first?",
                    bare="Setpoint is 1.0 C, not 4 C, and the condenser coil was last cleaned 14 months ago.",
                    partial="The cooler thermostat is set to 1 C now. Should I change it?",
                    vague="The bill is still high. What else can I do?",
                ),
            ),
        ),
    ),
    Challenge(
        id="signup-crash",
        title="Club sign-ups are broken",
        brief="You run the robotics club website. Sign-ups opened tonight, and everyone on a phone gets 'Something went wrong.' Ask Grok to fix it.",
        hint="Name the error and why only phones hit it. 'The site is broken' makes Grok search.",
        beats=(
            Beat(
                ask="You're the club webmaster. The server log is below. Ask Grok to fix the phone sign-ups. A good prompt names the error line and why phones fail.",
                fixture_title="server.log",
                fixture=SIGNUP_LOG.strip(),
                facts=(
                    Fact(
                        "error",
                        "The error: KeyError 'email' in signup(), app.py line 42",
                        ((r"keyerror", r"line\s*42", r"request\.form", r"app\.py", r"signup\s*\("),),
                    ),
                    Fact(
                        "cause",
                        "Why phones fail: the mobile form names the field \"Email\"",
                        (
                            (
                                r"(?-i:\bEmail\b)",
                                r"capital",
                                r"upper\s*-?case",
                                r"case[- ]sensitive",
                                r"field\s+name",
                                r"mobile\s+(form|template|page)",
                                r"signup_mobile",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "signup() reads request.form['email'], but signup_mobile.html names the field 'Email', so phones raise a KeyError. "
                    "Rename the mobile field to name=\"email\"."
                ),
                samples=Samples(
                    adequate="signup() in app.py line 42 crashes with KeyError: 'email' because the mobile form names the field \"Email\" with a capital E. Rename the mobile field to \"email\".",
                    bare="KeyError: 'email' at app.py line 42; the mobile form's field is \"Email\" with a capital E.",
                    partial="Phones get a KeyError: 'email' on line 42 when they sign up. How do I fix it?",
                    vague="Our sign-up page is broken for some people. Please fix it.",
                ),
            ),
            Beat(
                ask="Phones can sign up now. But 31 people are signed up twice, and club emails go out doubled. The table is below. Follow up.",
                fixture_title="signups table",
                fixture=SIGNUP_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "cause",
                        "Why: double taps, 1 second apart, button stays clickable",
                        (
                            (
                                r"double[- ]?(tap|click|submit)",
                                r"(tap|click)\w*\s+[^.]{0,30}\btwice\b",
                                r"\b(1|one)\s+second",
                                r"(button|submit)[^.]{0,30}(disable|clickable|twice|again)",
                            ),
                        ),
                    ),
                    Fact(
                        "database",
                        "What lets it through: no unique constraint on email",
                        ((r"\bunique\b", r"constraint", r"lower\s*-?case", r"lower\(", r"case[- ]insensitive"),),
                    ),
                ),
                simulated_reply=(
                    "The pairs are one second apart, so people double-tap on slow Wi-Fi, and nothing stops a second row. "
                    "Disable the button after the first tap, and add a unique index on lower(email)."
                ),
                samples=Samples(
                    adequate="The 31 duplicates are about 1 second apart, so people double-tap the button on slow Wi-Fi, and the email column has no unique constraint (Ben@ and ben@ both got in). Disable the button after the first tap and add a unique index on lower(email).",
                    bare="Duplicates are 1 second apart (double taps), and there is no unique constraint on email, even across Ben@/ben@ case.",
                    partial="People tap the sign-up button twice and get two rows. How do we stop that?",
                    vague="Some people are signed up twice. Fix it?",
                ),
            ),
        ),
    ),
    Challenge(
        id="solar-battery",
        title="The solar battery dies by 9 pm",
        brief="Your family has solar panels and a home battery. The battery is empty by 9 pm every night, so the house buys the most expensive power. Ask Grok to fix the schedule.",
        hint="Name the device and its schedule. 'My battery dies' makes Grok guess.",
        beats=(
            Beat(
                ask="You're the homeowner. The energy app is below. Ask Grok why the battery runs out and what to change. A good prompt names the device and its schedule.",
                fixture_title="Home energy app",
                fixture=SOLAR_APP.strip(),
                facts=(
                    Fact("where", "Which device: the EV charger", ((r"\bev\b", r"car\s+charg", r"charger", r"electric\s+(car|vehicle)"),)),
                    Fact(
                        "what",
                        "What's wrong: it charges 18:00-21:00 at 7.2 kW from the battery",
                        (
                            (
                                r"18:00",
                                r"\b6\s*(pm|p\.m\.)?\s*(-|to|until|–)\s*9",
                                r"\b7\.2\b",
                                r"battery\s+first",
                                r"\bpeak\b",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "The EV charger pulls 7.2 kW from 18:00 to 21:00 with 'battery first', which empties 13.5 kWh in about two hours. "
                    "Move charging to 11:00-15:00 when solar is spare, or to 23:00 off-peak, and set it to grid-only."
                ),
                samples=Samples(
                    adequate="The EV charger is scheduled 18:00-21:00 at 7.2 kW with 'battery first', so it drains the home battery at peak price. Move charging to 11:00-15:00 on solar, or 23:00 off-peak from the grid.",
                    bare="EV charger: 7.2 kW, 18:00-21:00 daily, battery first.",
                    partial="The EV charger empties our home battery. What should we change?",
                    vague="Our solar battery dies every night. Can you help?",
                ),
            ),
            Beat(
                ask="Charging moved to 11:00-15:00 on solar. On cloudy days the car is only at about 40% by morning, and the commute needs 70%. The log is below. Follow up.",
                fixture_title="EV charging, last 5 days",
                fixture=SOLAR_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "gap",
                        "The gap: cloudy days leave the car near 40%, commute needs 70%",
                        ((r"cloud", r"\brain", r"\b(35|38|40|41)\s*%", r"\b70\s*%"),),
                    ),
                    Fact(
                        "fallback",
                        "The fix window: off-peak grid, 23:00-07:00 at $0.11",
                        ((r"off[- ]?peak", r"23:00", r"\b11\s*pm", r"overnight", r"\bnight\b", r"top[- ]?up", r"\$?0?\.11\b"),),
                    ),
                ),
                simulated_reply=(
                    "Keep solar charging from 11:00 to 15:00, and add a rule: if the car is under 70% at 21:00, "
                    "top it up from the grid between 23:00 and 07:00 at the $0.11 off-peak rate."
                ),
                samples=Samples(
                    adequate="On cloudy days solar only gets the car to about 40% by 07:00, and the commute needs 70%. Keep solar charging, but top up from the grid off-peak (23:00-07:00) whenever it's under 70% at 21:00.",
                    bare="Cloudy days: car at 35-41% by 07:00, commute takes 70%; off-peak is 23:00-07:00 at $0.11.",
                    partial="On cloudy days the car doesn't charge enough. What should we do?",
                    vague="The car isn't charged sometimes. Help?",
                ),
            ),
        ),
    ),
)


# Developer rounds: real code, two-step debugging threads.
DEV_CHALLENGES: tuple[Challenge, ...] = (
    Challenge(
        id="invoice-bug",
        title="Invoice totals are wrong",
        brief="A billing job is mis-charging customers. The fix takes two passes: the coupon bug, then whatever production still fails after that patch.",
        hint="Name the function and what goes wrong. Every fact you leave out is a web search the model has to run.",
        beats=(
            Beat(
                ask="Coupons are discounting the tax as well as the goods. The module is below. Name the function and the change. Quote only the lines the model needs.",
                fixture_title="billing/invoice.py",
                fixture=_with_noise(INVOICE_FILE.strip(), "billing/invoice.py"),
                facts=(
                    Fact(
                        "where",
                        "Where it breaks: total() calls apply_coupon",
                        ((r"apply[_ ]coupon", r"\btotal\s*\(", r"\btotal\s+function", r"\bfunction\s+total\b", r"\bin\s+total\b"),),
                    ),
                    Fact(
                        "what",
                        "What goes wrong: the coupon runs after tax",
                        (
                            (
                                r"after\s+(the\s+)?tax",
                                r"\btaxed\b",
                                r"before\s+(the\s+)?(coupon|discount)",
                                r"discount(s|ing)?\s+(the\s+)?tax\b",
                                r"\btax\w*\s+(is\s+)?(applied\s+|added\s+|computed\s+)?(first|before)\b",
                                r"\border\b",
                                r"\bsubtotal\b",
                                r"\b(swap|reorder|flip)\b",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "In total(), apply_coupon runs on the taxed amount, so the coupon discounts tax. "
                    "Discount subtotal() first, then tax that result."
                ),
                samples=Samples(
                    adequate="In total(), apply_coupon runs after tax(), so the coupon discounts tax. Discount subtotal() first, then tax the result.",
                    bare="apply_coupon runs after tax() in total().",
                    partial="apply_coupon is wrong in the invoice module. Please fix it.",
                    vague="Customers say their invoices are wrong. Can you look into our billing code and fix it?",
                ),
                parts=(
                    Part(
                        "You have the billing file",
                        "billing/invoice.py",
                        _with_noise(INVOICE_FILE.strip(), "billing/invoice.py"),
                        "apply_coupon",
                    ),
                    Part(
                        "You took the customer call",
                        "Support note",
                        "A customer says the coupon overcharged them on tax. A 10% coupon cut the tax as well as the goods. You do not have the source file. Your partner does.",
                        "overcharged",
                    ),
                ),
            ),
            Beat(
                ask="That patch shipped. Tax-exempt accounts are still taxed. The new failure is below. Follow up with the smallest change. The model already has your last message, so don't paste the file again.",
                fixture_title="CI failure",
                fixture=INVOICE_FOLLOWUP.strip(),
                facts=(
                    Fact("flag", "The flag: tax_exempt", ((r"tax[_ -]?exempt", r"\bexempt\b"),)),
                    Fact(
                        "where",
                        "Where it is ignored: tax(), or the failing numbers",
                        ((r"\btax\s*\(", r"\btax\s+function", r"\bfunction\s+tax\b", r"97\.2", r"\b90(\.0+)?\b", r"test_tax_exempt"),),
                    ),
                ),
                simulated_reply="In tax(), if account.get('tax_exempt'): return amount unchanged before applying the rate.",
                samples=Samples(
                    adequate="tax() ignores tax_exempt. If account.get('tax_exempt') is true, return the amount unchanged.",
                    bare="tax() ignores tax_exempt: expected due=90.00, actual due=97.20.",
                    partial="tax_exempt accounts are still getting charged. How do I fix it?",
                    vague="It's still broken for some customers. Can you fix it?",
                ),
                parts=(
                    Part("You have the CI failure", "CI failure", INVOICE_FOLLOWUP.strip(), "tax_exempt"),
                    Part(
                        "You shipped the last patch",
                        "Your note",
                        "You shipped the coupon change. Mention ticket 441 in the shared message so the new failure is tied to your patch. You do not have the CI log.",
                        "ticket 441",
                    ),
                ),
            ),
        ),
    ),
    Challenge(
        id="null-profile",
        title="Account header crash",
        brief="Production is throwing in a React header. The first report is a null user. The second report shows up only after that guard ships.",
        hint="Name the crash and where it happens. A vague 'fix the header' makes the model go search for both.",
        beats=(
            Beat(
                ask="Sentry: TypeError, cannot read 'name' of null, in AccountHeader. The component is below. Tell the model what to guard. Don't send any other files.",
                fixture_title="AccountHeader.tsx",
                fixture=_with_noise(PROFILE_FILE.strip(), "AccountHeader.tsx"),
                facts=(
                    Fact(
                        "crash",
                        "The crash: reading name of a null user",
                        (
                            (
                                r"typeerror",
                                r"can(no|')?t\s+read",
                                r"\.name\b",
                                r"read\w*\s+['\"]?name\b",
                                r"\bname\b[^.]{0,25}\b(null|undefined)\b",
                                r"\b(null|undefined)\b[^.]{0,25}\bname\b",
                            ),
                        ),
                    ),
                    Fact(
                        "where",
                        "Where: profile.user in AccountHeader",
                        ((r"profile\.user", r"accountheader", r"\buser\b[^.]{0,20}\b(is\s+)?(null|undefined|missing)\b"),),
                    ),
                ),
                simulated_reply="profile.user is null while the account request is in flight. Return null before reading profile.user.name.",
                samples=Samples(
                    adequate="AccountHeader reads profile.user.name while user is still null. Return early if profile.user is missing.",
                    bare="TypeError: cannot read 'name' of null in AccountHeader, profile.user is null there.",
                    partial="AccountHeader crashes in production. How do I fix it?",
                    vague="The header on the account page keeps crashing. Please fix it.",
                ),
                parts=(
                    Part(
                        "You have the component",
                        "AccountHeader.tsx",
                        _with_noise(PROFILE_FILE.strip(), "AccountHeader.tsx"),
                        "profile.user",
                    ),
                    Part(
                        "You are with the reporter",
                        "Reporter note",
                        "The reporter says the header crashes while the account request is still in flight. You do not have the component.",
                        "in flight",
                    ),
                ),
            ),
            Beat(
                ask="The null guard is live. The header now stays blank after the request finishes, and Edit never comes back. Follow up. Don't paste the component again.",
                fixture_title="Sentry follow-up",
                fixture=PROFILE_FOLLOWUP.strip(),
                facts=(
                    Fact("status", "The state: profile.status is 'loading'", ((r"\bloading\b", r"profile\.status", r"\bstatus\b"),)),
                    Fact(
                        "symptom",
                        "The symptom: header stays blank after the fetch",
                        (
                            (
                                r"\bblank\b",
                                r"\bempty\b",
                                r"never\s+(mounts|renders|shows|appears|comes\s+back|loads)",
                                r"(doesn'?t|does\s+not|won'?t)\s+(mount|render|show|appear|come\s+back)",
                                r"edit\s+(button\s+)?(is\s+)?(gone|missing|never|disappears)",
                                r"returns?\s+null",
                                r"early[- ](return|exit)",
                                r"\bready\b",
                                r"stays?\s+(null|hidden|gone)",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "Don't return null for every missing user. If profile.status is 'loading', render a placeholder. "
                    "When status is 'ready', render the header from profile.user."
                ),
                samples=Samples(
                    adequate="The early return also runs while status is loading, so the header never mounts after the fetch. Render a placeholder when status is loading, and the real header when status is ready.",
                    bare="Header stays blank after the fetch: profile.status is 'loading' when the early exit fires.",
                    partial="The header is still blank after the request finishes. What should change?",
                    vague="The header is still broken. Please fix it.",
                ),
                parts=(
                    Part("You have the follow-up", "Sentry follow-up", PROFILE_FOLLOWUP.strip(), "loading"),
                    Part(
                        "You watched the screen",
                        "What you saw",
                        "After the guard shipped, the edit button never came back. Say that in the shared message. You do not have the new report.",
                        "edit button",
                    ),
                ),
            ),
        ),
    ),
    Challenge(
        id="half-migration",
        title="Deploy died mid-migration",
        brief="A schema change failed halfway through deploy. First find the statement that broke. Then unstick the retry, which is a different failure.",
        hint="Name the statement and the error. Otherwise the model searches the error instead of reading what you have.",
        beats=(
            Beat(
                ask="The deploy failed while adding coupon codes. The migration and the database error are below. Say which statement broke and what to change. Quote that statement, not the whole file.",
                fixture_title="migrations/014_invoices.sql + database log",
                fixture=_with_noise((MIGRATION_FILE + "\n" + MIGRATION_LOG).strip(), "014_invoices.sql"),
                facts=(
                    Fact(
                        "statement",
                        "The statement: the UPDATE that sets coupon_code to ''",
                        ((r"\bupdate\b", r"''", r'""', r"empty\s+(string|value|coupon)", r"blank\s+(string|value)", r"\bnull\b"),),
                    ),
                    Fact(
                        "error",
                        "The error: duplicate '' keys on the unique index",
                        ((r"\bunique\b", r"duplicat", r"coupon_code_idx", r"\bindex\b"),),
                    ),
                ),
                simulated_reply=(
                    "The UPDATE sets coupon_code to '' on every existing row, then the unique index rejects those duplicates. "
                    "Leave missing coupons as NULL, and make the unique index partial: WHERE coupon_code IS NOT NULL."
                ),
                samples=Samples(
                    adequate="The UPDATE sets coupon_code to '' for every row, then CREATE UNIQUE INDEX fails on those duplicates. Store NULL instead of '', and index WHERE coupon_code IS NOT NULL.",
                    bare="The UPDATE sets coupon_code to '', so the unique index hits duplicate keys.",
                    partial="The deploy fails on the unique index. What should we change?",
                    vague="Our deploy broke partway through a database migration. What should we do to fix it?",
                ),
                parts=(
                    Part(
                        "You have the migration",
                        "migrations/014_invoices.sql",
                        _with_noise(MIGRATION_FILE.strip(), "014_invoices.sql"),
                        "alter table",
                    ),
                    Part(
                        "You have the database error",
                        "Database log",
                        MIGRATION_LOG.strip(),
                        "duplicated",
                    ),
                ),
            ),
            Beat(
                ask="Someone retried the deploy. The new error is below. Write the follow-up migration only. Do not resend 014.",
                fixture_title="Retry log",
                fixture=MIGRATION_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "error",
                        "The new error: the index already exists (014 is half-applied)",
                        ((r"already\s+(exists|created|there|applied|ran|built)", r"\bexists\b", r"half[- ]?applied", r"partial(ly)?\s+applied"),),
                    ),
                    Fact(
                        "want",
                        "What you want: a new migration, not a rerun of 014",
                        (
                            (
                                r"new\s+migration",
                                r"follow[- ]?up\s+migration",
                                r"\b015\b",
                                r"(don'?t|do\s+not|not|never|instead\s+of|without)\s+(a\s+)?re-?run",
                                r"drop\s+(the\s+|that\s+)?index",
                                r"if\s+(not\s+)?exists",
                            ),
                        ),
                    ),
                ),
                simulated_reply=(
                    "014 is half-applied, so don't rerun it. A new migration should drop invoices_coupon_code_idx if it exists, "
                    "set '' back to NULL, then create the partial unique index."
                ),
                samples=Samples(
                    adequate="014 already created the index, so a retry can't run it again. New migration: drop that index if present, turn '' into NULL, then add the partial unique index.",
                    bare="Retry error: invoices_coupon_code_idx already exists; 014 is half-applied and this is a follow-up migration.",
                    partial="The retry says the index already exists. What now?",
                    vague="The retry failed too. What should we do?",
                ),
                parts=(
                    Part(
                        "You have the retry error",
                        "Retry log",
                        'ERROR: relation "invoices_coupon_code_idx" already exists',
                        "already exists",
                    ),
                    Part(
                        "You know how the deploy failed",
                        "Deploy note",
                        "014 was half-applied. The UPDATE ran and the job died. They need a new migration, not a rerun of 014. You do not have the new error text.",
                        "half-applied",
                    ),
                ),
            ),
        ),
    ),
    Challenge(
        id="token-in-the-log",
        title="Secret in the log",
        brief="Security review, two passes. A handler is copying request credentials into places other people can read. Name the leak without pasting the credential into the model.",
        hint="Name the header and where it gets written. Never paste the token itself: that is an automatic F.",
        beats=(
            Beat(
                ask="Datadog is showing API tokens. The handler is below. Say what to stop writing, and where. Quote the line. Do not paste the whole file: its log sample contains a credential.",
                fixture_title="export_handler.py",
                fixture=_with_noise(EXPORT_HANDLER.strip(), "export_handler.py"),
                facts=(
                    Fact(
                        "header",
                        "The header: Authorization",
                        ((r"authori[sz]ation", r"auth(entication)?\s+header", r"\bcredentials?\b", r"\b(api\s+|bearer\s+|access\s+)?tokens?\b"),),
                    ),
                    Fact(
                        "where",
                        "Where: the logger.info line in handle_export",
                        ((r"\blog(s|ged|ging|ger)?\b", r"handle_export", r"\binfo\b", r"datadog"),),
                    ),
                ),
                forbidden=(DEMO_SECRET, BEARER_VALUE),
                simulated_reply=(
                    "handle_export logs the Authorization header on the info line. "
                    "Log the account id only. Never log or store that header."
                ),
                samples=Samples(
                    adequate="handle_export logs request.headers['Authorization'] on the info line. Log the account id instead, and do not write that header anywhere.",
                    bare="handle_export writes the Authorization header into the info log.",
                    partial="Our logs are exposing something sensitive. Please stop it.",
                    vague="Security says something in our export endpoint is unsafe. Can you check it and fix it?",
                    leak="handle_export logs the Authorization header (Bearer demo-token-not-real) on the info line. Stop logging it.",
                ),
                parts=(
                    Part(
                        "You have the handler",
                        "export_handler.py",
                        _with_noise(EXPORT_HANDLER.strip(), "export_handler.py"),
                        "authorization",
                    ),
                    Part(
                        "You are reading the alert",
                        "Datadog alert",
                        "The alert says API tokens are showing up in logs. You do not have the handler. Your partner does.",
                        "api tokens",
                    ),
                ),
            ),
            Beat(
                ask="The info log is fixed. A 500 response is still returning the raw request headers, and someone pasted that response into Slack. Follow up with the response change only. Do not resend the handler or the token.",
                fixture_title="Incident note",
                fixture=EXPORT_FOLLOWUP.strip(),
                facts=(
                    Fact(
                        "branch",
                        "Where: the except branch that returns a 500",
                        ((r"\b500\b", r"\bexcept\b", r"exception", r"error\s+(response|body|branch|path|handler)"),),
                    ),
                    Fact("leak", "What leaks: the raw request headers", ((r"\bheaders?\b", r"header\s+map"),)),
                ),
                forbidden=(DEMO_SECRET, BEARER_VALUE),
                simulated_reply=(
                    "The except branch returns dict(request.headers). "
                    "Return a generic error string and a request id. Do not include headers."
                ),
                samples=Samples(
                    adequate="The except branch still returns dict(request.headers) in the 500 body. Return a generic error and a request id, with no headers.",
                    bare="The 500 branch returns dict(request.headers) in the body.",
                    partial="The 500 response is still leaking. How do we fix it?",
                    vague="Something is still leaking. Can you fix it?",
                    leak="The 500 body returns dict(request.headers), e.g. Authorization: Bearer demo-token-not-real. Return a generic error.",
                ),
                parts=(
                    Part("You have the incident note", "Incident note", EXPORT_FOLLOWUP.strip(), "500"),
                    Part(
                        "You saw where it was pasted",
                        "What you saw",
                        "Someone copied the failed response into Slack. Call it the slack paste in the shared message. You do not have the incident writeup.",
                        "slack paste",
                    ),
                ),
            ),
        ),
    ),
)


# Imported last so this module can finish defining Challenge first.
from .builds import BUILD_CHALLENGES  # noqa: E402

# Build rounds first: that is what the pair room plays.
CHALLENGES: tuple[Challenge, ...] = BUILD_CHALLENGES + PROBLEM_SETS + DEV_CHALLENGES
BUILD_IDS = {challenge.id for challenge in BUILD_CHALLENGES}

_BY_ID = {challenge.id: challenge for challenge in CHALLENGES}


def get_challenge(challenge_id: str) -> Challenge | None:
    return _BY_ID.get(challenge_id)


def public_beat(beat: Beat) -> dict:
    return {
        "ask": beat.ask,
        "fixtureTitle": beat.fixture_title,
        "fixture": beat.fixture,
        "targetTokens": beat.target_tokens,
    }


def public_challenge(challenge: Challenge) -> dict:
    return {
        "id": challenge.id,
        "title": challenge.title,
        "brief": challenge.brief,
        "hint": challenge.hint,
        "turnCount": len(challenge.beats),
        "targetTokens": challenge.target_tokens,
        "build": bool(challenge.files),
        "files": [{"name": name, "body": body} for name, body in challenge.files],
        "beats": [public_beat(beat) for beat in challenge.beats],
    }


def public_challenges() -> list[dict]:
    return [public_challenge(challenge) for challenge in CHALLENGES]
