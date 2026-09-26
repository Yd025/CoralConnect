"""Challenges the booth can run.

Add a Challenge to CHALLENGES when you design a new round.
Each beat is one turn. anchors are the facts the latest message must contain
so the solver does not have to look them up. They stay on the server.
Compete mode shows fixture to every phone.
Collaborate mode deals parts: each person in a squad gets a different piece,
and the shared message has to carry every part's anchor.
Roleplay rounds belong here. Set Part.role to the character, put a fact only
that character knows in body, and set anchor to the phrase the shared message
must include from that piece.
simulated_reply is the answer used until XAI_API_KEY is set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Part:
    """One collaborator's piece of a turn. anchor is server-only."""

    role: str
    title: str
    body: str
    anchor: str


@dataclass(frozen=True)
class Beat:
    """One request in a thread. Anchors are the facts that keep the model from searching the web."""

    ask: str
    fixture_title: str
    fixture: str
    target_tokens: int
    anchors: tuple[str, ...]
    simulated_reply: str
    parts: tuple[Part, ...] = ()


@dataclass(frozen=True)
class Challenge:
    id: str
    title: str
    brief: str
    hint: str
    beats: tuple[Beat, ...]
    # Server-only rehearsal lines. One entry per beat. Never send these to phones.
    example_efficient: tuple[str, ...]
    example_bloated: str

    @property
    def target_tokens(self) -> int:
        return self.beats[-1].target_tokens if self.beats else 0


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


CHALLENGES: tuple[Challenge, ...] = (
    Challenge(
        id="invoice-bug",
        title="Invoice totals are wrong",
        brief="A billing job is mis-charging customers. The fix takes two passes: the coupon bug, then whatever production still fails after that patch.",
        hint="Name the function. If you leave it out, the model looks the bug up on the web, and that search is the bill.",
        beats=(
            Beat(
                ask="Coupons are discounting the tax as well as the goods. The module is below. Name the function and the change. Quote only the lines the model needs.",
                fixture_title="billing/invoice.py",
                fixture=_with_noise(INVOICE_FILE.strip(), "billing/invoice.py"),
                target_tokens=160,
                anchors=("apply_coupon", "total()"),
                simulated_reply=(
                    "In total(), apply_coupon runs on the taxed amount, so the coupon discounts tax. "
                    "Discount subtotal() first, then tax that result."
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
                target_tokens=200,
                anchors=("tax_exempt",),
                simulated_reply="In tax(), if account.get('tax_exempt'): return amount unchanged before applying the rate.",
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
        example_efficient=(
            "In total(), apply_coupon runs after tax(), so the coupon discounts tax. Discount subtotal() first, then tax the result.",
            "tax() ignores tax_exempt. If account.get('tax_exempt') is true, return the amount unchanged.",
        ),
        example_bloated=(
            "You are the on-call billing lead. Read the entire repository, restate every function, "
            "propose three architectures, and only then patch the invoice bug. File follows.\n"
            + INVOICE_FILE
            + "\nAlso consider the style guide, the last six months of git history, and every caller."
        )
        * 4,
    ),
    Challenge(
        id="null-profile",
        title="Account header crash",
        brief="Production is throwing in a React header. The first report is a null user. The second report shows up only after that guard ships.",
        hint="Name the crash. A vague 'fix the header' makes the model go search for it.",
        beats=(
            Beat(
                ask="Sentry: TypeError, cannot read 'name' of null, in AccountHeader. The component is below. Tell the model what to guard. Don't send any other files.",
                fixture_title="AccountHeader.tsx",
                fixture=_with_noise(PROFILE_FILE.strip(), "AccountHeader.tsx"),
                target_tokens=150,
                anchors=("profile.user",),
                simulated_reply="profile.user is null while the account request is in flight. Return null before reading profile.user.name.",
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
                target_tokens=190,
                anchors=("loading",),
                simulated_reply=(
                    "Don't return null for every missing user. If profile.status is 'loading', render a placeholder. "
                    "When status is 'ready', render the header from profile.user."
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
        example_efficient=(
            "AccountHeader reads profile.user.name while user is still null. Return early if profile.user is missing.",
            "The early return also runs while status is loading, so the header never mounts after the fetch. Render a placeholder when status is loading, and the real header when status is ready.",
        ),
        example_bloated=(
            "Please audit our design system, restate the component, list every prop, and rewrite AccountHeader from scratch. "
            + PROFILE_FILE
        )
        * 6,
    ),
    Challenge(
        id="half-migration",
        title="Deploy died mid-migration",
        brief="A schema change failed halfway through deploy. First find the statement that broke. Then unstick the retry, which is a different failure.",
        hint="Name the statement that failed. Otherwise the model searches the error instead of reading what you have.",
        beats=(
            Beat(
                ask="The deploy failed while adding coupon codes. The migration and the database error are below. Say which statement broke and what to change. Quote that statement, not the whole file.",
                fixture_title="migrations/014_invoices.sql + database log",
                fixture=_with_noise((MIGRATION_FILE + "\n" + MIGRATION_LOG).strip(), "014_invoices.sql"),
                target_tokens=170,
                anchors=("coupon_code",),
                simulated_reply=(
                    "The UPDATE sets coupon_code to '' on every existing row, then the unique index rejects those duplicates. "
                    "Leave missing coupons as NULL, and make the unique index partial: WHERE coupon_code IS NOT NULL."
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
                target_tokens=210,
                anchors=("already exists",),
                simulated_reply=(
                    "014 is half-applied, so don't rerun it. A new migration should drop invoices_coupon_code_idx if it exists, "
                    "set '' back to NULL, then create the partial unique index."
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
        example_efficient=(
            "The UPDATE sets coupon_code to '' for every row, then CREATE UNIQUE INDEX fails on those duplicates. Store NULL instead of '', and index WHERE coupon_code IS NOT NULL.",
            "014 already created the index, so a retry can't run it again. New migration: drop that index if present, turn '' into NULL, then add the partial unique index.",
        ),
        example_bloated=(
            "Here is our entire migration history and the on-call handbook. Summarize all of it, then fix the deploy. "
            + MIGRATION_FILE
            + MIGRATION_LOG
        )
        * 5,
    ),
    Challenge(
        id="token-in-the-log",
        title="Secret in the log",
        brief="Security review, two passes. A handler is copying request credentials into places other people can read. Name the leak without pasting the credential into the model.",
        hint="Name the header the log writes. If you only say 'check security', the model goes looking.",
        beats=(
            Beat(
                ask="Datadog is showing API tokens. The handler is below. Say what to stop writing, and where. Quote the line. Do not paste the file — it contains a sample credential.",
                fixture_title="export_handler.py",
                fixture=_with_noise(EXPORT_HANDLER.strip(), "export_handler.py"),
                target_tokens=160,
                anchors=("authorization",),
                simulated_reply=(
                    "handle_export logs the Authorization header on the info line. "
                    "Log the account id only. Never log or store that header."
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
                target_tokens=200,
                anchors=("500",),
                simulated_reply=(
                    "The except branch returns dict(request.headers). "
                    "Return a generic error string and a request id. Do not include headers."
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
        example_efficient=(
            "handle_export logs request.headers['Authorization'] on the info line. Log the account id instead, and do not write that header anywhere.",
            "The except branch still returns dict(request.headers) in the 500 body. Return a generic error and a request id, with no headers.",
        ),
        example_bloated=(
            "Please review our entire service, repeat every header you see, and then discuss the leak. File follows.\n"
            + EXPORT_HANDLER
        )
        * 5,
    ),
)


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
        "beats": [public_beat(beat) for beat in challenge.beats],
    }


def public_challenges() -> list[dict]:
    return [public_challenge(challenge) for challenge in CHALLENGES]
