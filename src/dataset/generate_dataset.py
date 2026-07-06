"""Generate a synthetic-but-realistic business email dataset.

Why synthetic: real inboxes contain private and personal data. A synthetic
generator lets us publish the project publicly, control the difficulty, and —
most importantly — attach *ground-truth evaluation labels* to every example
(`required_facts`, `must_include`, `must_not_include`, ...). Those labels are
what let the evaluator score a reply on substance rather than surface wording.

The generator composes emails from per-category template banks with randomized
slot fills (names, companies, dates, amounts, ...). Each gold reply is built to
contain the required facts and must-include phrases and to avoid the
must-not-include phrases, so the labels are internally consistent by
construction.

Run:
    python -m src.dataset.generate_dataset --n 220 --seed 7
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from src.config import DATA_DIR
from src.schemas import Category, EmailExample, RiskLevel

# --- slot banks -----------------------------------------------------------

FIRST_NAMES = [
    "Sarah", "James", "Priya", "Daniel", "Mei", "Omar", "Elena", "Tom",
    "Aisha", "Lucas", "Nina", "Carlos", "Hana", "Ben", "Sofia", "Raj",
]
LAST_NAMES = [
    "Chen", "Patel", "Nguyen", "Garcia", "Kowalski", "Okafor", "Rossi",
    "Andersen", "Silva", "Khan", "Müller", "Ivanov",
]
COMPANIES = [
    "Northwind Labs", "Acme Retail", "Brightpath", "Vertex Systems", "Lumen Health",
    "Orbit Logistics", "Quill Media", "Fernpath", "Copperline", "Harbor & Co",
]
PRODUCTS = [
    "the Analytics dashboard", "the API gateway", "the mobile SDK",
    "the billing portal", "the reporting module", "the sync engine",
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIMES = ["9:00 AM", "10:30 AM", "1:00 PM", "2:30 PM", "4:00 PM"]
TIMEZONES = ["ET", "PT", "CET", "GMT"]
ROLES = ["Backend Engineer", "Product Designer", "Data Scientist", "Account Executive"]


def _person() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _first() -> str:
    return random.choice(FIRST_NAMES)


# --- category generators --------------------------------------------------
# Each returns: (incoming, gold, required_facts, must_include, must_not_include,
#                intent, tone, ideal_action, risk_level)

Generated = Tuple[str, str, List[str], List[str], List[str], str, str, str, RiskLevel]


def gen_scheduling() -> Generated:
    sender = _first()
    me = _first()
    day, time, tz = random.choice(DAYS), random.choice(TIMES), random.choice(TIMEZONES)
    topic = random.choice(["the Q3 roadmap", "onboarding", "the integration review", "budget planning"])
    incoming = (
        f"Hi {me},\n\nCould we find 30 minutes this week to discuss {topic}? "
        f"I'm fairly flexible but afternoons work best for me. Let me know what suits you.\n\nThanks,\n{sender}"
    )
    slot = f"{day} at {time} {tz}"
    gold = (
        f"Hi {sender},\n\nHappy to meet about {topic}. {slot} works well on my end — "
        f"I'll send a calendar invite with a video link. If that time doesn't suit you, "
        f"just share a couple of afternoon slots and I'll adjust.\n\nBest,\n{me}"
    )
    return (
        incoming, gold,
        [slot, topic],
        [day, time, "calendar invite"],
        ["I am unavailable", "cannot meet"],
        "propose_meeting_time", "friendly-professional",
        "Confirm a specific time and send a calendar invite.", RiskLevel.LOW,
    )


def gen_recruiting() -> Generated:
    candidate = _person()
    me = _first()
    role = random.choice(ROLES)
    company = random.choice(COMPANIES)
    day, time = random.choice(DAYS), random.choice(TIMES)
    incoming = (
        f"Hello,\n\nI came across the {role} opening at {company} and I'm very interested. "
        f"I have five years of relevant experience. Could you tell me about the next steps "
        f"and interview process?\n\nRegards,\n{candidate}"
    )
    gold = (
        f"Hi {candidate.split()[0]},\n\nThanks for your interest in the {role} role at {company}. "
        f"The next step is a 45-minute screening call, and I'd suggest {day} at {time}. "
        f"After that we run one technical round and a final team conversation. "
        f"Could you share your availability and an updated resume?\n\nBest,\n{me}\nTalent Team, {company}"
    )
    return (
        incoming, gold,
        [role, "screening call", "technical round"],
        [role, company, "next step"],
        ["you are rejected", "we are not hiring"],
        "explain_hiring_process", "warm-professional",
        "Outline interview steps and request availability plus resume.", RiskLevel.LOW,
    )


def gen_customer_support() -> Generated:
    customer = _first()
    me = _first()
    product = random.choice(PRODUCTS)
    ticket = f"#{random.randint(10000, 99999)}"
    issue = random.choice(["failing to load", "returning a 500 error", "syncing very slowly", "logging users out"])
    incoming = (
        f"Hi support,\n\n{product} has been {issue} since yesterday and it's blocking my team. "
        f"This is urgent. Can you help?\n\n{customer}"
    )
    gold = (
        f"Hi {customer},\n\nSorry for the disruption — I've opened ticket {ticket} and our team is "
        f"investigating {product} {issue}. As an immediate workaround, please clear the app cache and "
        f"retry; I'll update you within 4 hours with a root cause. Could you confirm your account email "
        f"and roughly when the issue started?\n\nBest,\n{me}\nCustomer Support"
    )
    return (
        incoming, gold,
        [ticket, "workaround", "4 hours"],
        [ticket, "update", "account"],
        ["this is your fault", "we cannot help"],
        "acknowledge_and_troubleshoot", "empathetic-professional",
        "Open a ticket, give a workaround and an update ETA, request details.", RiskLevel.MEDIUM,
    )


def gen_sales_demo() -> Generated:
    prospect = _person()
    me = _first()
    company = random.choice(COMPANIES)
    product = random.choice(PRODUCTS)
    incoming = (
        f"Hi,\n\nWe're evaluating tools for our team at {company} and {product} looks promising. "
        f"Could we set up a demo? We're especially interested in pricing for around 40 seats.\n\n{prospect}"
    )
    day, time = random.choice(DAYS), random.choice(TIMES)
    gold = (
        f"Hi {prospect.split()[0]},\n\nGreat to hear {company} is exploring {product}. I'd love to run a "
        f"30-minute demo — would {day} at {time} work? I'll tailor it to a 40-seat setup and walk through "
        f"pricing options on the call. In the meantime, is there a specific workflow you'd like us to focus on?"
        f"\n\nBest,\n{me}\nSales"
    )
    return (
        incoming, gold,
        ["30-minute demo", "40-seat", "pricing"],
        ["demo", product, "pricing"],
        ["free forever", "unlimited everything"],
        "book_demo_and_address_pricing", "enthusiastic-professional",
        "Offer a tailored demo slot and address the seat-based pricing question.", RiskLevel.MEDIUM,
    )


def gen_invoice_payment() -> Generated:
    sender = _first()
    me = _first()
    company = random.choice(COMPANIES)
    inv = f"INV-{random.randint(1000, 9999)}"
    amount = f"${random.choice([1200, 2400, 3600, 5000, 8750]):,}"
    incoming = (
        f"Hello,\n\nWe received invoice {inv} for {amount} but the PO number is missing and one line item "
        f"looks duplicated. Could you review before we process payment?\n\nThanks,\n{sender} — {company}"
    )
    gold = (
        f"Hi {sender},\n\nThanks for flagging invoice {inv}. You're right — I've removed the duplicated line "
        f"item and added your PO number, so the corrected total is {amount}. A revised copy is attached, and "
        f"payment terms remain net-30. Please let me know if anything else needs adjusting.\n\nBest,\n{me}\nBilling"
    )
    return (
        incoming, gold,
        [inv, amount, "net-30"],
        [inv, "corrected", "PO"],
        ["pay immediately", "we never make mistakes"],
        "resolve_invoice_discrepancy", "precise-professional",
        "Acknowledge the discrepancy, correct the invoice, restate terms.", RiskLevel.HIGH,
    )


def gen_project_update() -> Generated:
    lead = _first()
    me = _first()
    project = random.choice(["Project Atlas", "the migration", "the redesign", "the v2 launch"])
    pct = random.choice([40, 55, 70, 85])
    day = random.choice(DAYS)
    incoming = (
        f"Hi team,\n\nCan you give me a quick status on {project}? Leadership is asking whether we're on track "
        f"for the launch and if there are any blockers.\n\n{lead}"
    )
    gold = (
        f"Hi {lead},\n\nHere's where {project} stands: we're about {pct}% complete and on track for launch. "
        f"The one blocker is a pending security review, which we expect cleared by {day}. No change to the "
        f"timeline at this stage — I'll send the next update on {day}.\n\nBest,\n{me}"
    )
    return (
        incoming, gold,
        [f"{pct}%", "on track", "security review"],
        [f"{pct}%", "blocker", day],
        ["everything is broken", "we will definitely miss the deadline"],
        "report_project_status", "concise-professional",
        "Summarize progress, name the blocker and ETA, confirm timeline.", RiskLevel.MEDIUM,
    )


def gen_partnership() -> Generated:
    sender = _person()
    me = _first()
    company = random.choice(COMPANIES)
    mine = random.choice(COMPANIES)
    incoming = (
        f"Hello,\n\nI lead partnerships at {company}. I think there's a strong fit for a co-marketing "
        f"partnership with {mine} around joint webinars and a referral program. Would you be open to a "
        f"conversation?\n\n{sender}"
    )
    day, time = random.choice(DAYS), random.choice(TIMES)
    gold = (
        f"Hi {sender.split()[0]},\n\nThanks for reaching out — a co-marketing partnership between {company} "
        f"and {mine} sounds worth exploring, especially the joint webinar idea. Could we start with a 30-minute "
        f"intro call, perhaps {day} at {time}? Beforehand, it would help to understand your audience size and "
        f"what a referral program would look like on your side.\n\nBest,\n{me}\nPartnerships"
    )
    return (
        incoming, gold,
        ["co-marketing", "intro call", "webinar"],
        [company, "partnership", "call"],
        ["we commit to a contract", "guaranteed revenue"],
        "explore_partnership", "diplomatic-professional",
        "Express measured interest and propose an exploratory call with questions.", RiskLevel.MEDIUM,
    )


def gen_event_logistics() -> Generated:
    sender = _first()
    me = _first()
    event = random.choice(["the customer summit", "the team offsite", "the launch dinner", "the workshop"])
    day, time = random.choice(DAYS), random.choice(TIMES)
    count = random.choice([12, 25, 40, 60])
    incoming = (
        f"Hi,\n\nI'm finalizing details for {event}. Can you confirm the headcount, start time, and whether "
        f"we need any dietary accommodations?\n\nThanks,\n{sender}"
    )
    gold = (
        f"Hi {sender},\n\nConfirmed for {event}: we're expecting {count} attendees, and the start time is "
        f"{time}. Please plan for 3 vegetarian and 2 gluten-free meals. I'll share the final rooming and "
        f"agenda by {day}. Let me know if the caterer needs anything else from us.\n\nBest,\n{me}"
    )
    return (
        incoming, gold,
        [str(count), time, "vegetarian"],
        [str(count), time, "gluten-free"],
        ["cancel the event", "no food will be provided"],
        "confirm_event_details", "organized-professional",
        "Confirm headcount, start time, and dietary needs; give a follow-up date.", RiskLevel.LOW,
    )


def gen_complaint_escalation() -> Generated:
    customer = _first()
    me = _first()
    product = random.choice(PRODUCTS)
    incoming = (
        f"This is the third time I've written about {product} losing my data and no one has fixed it. "
        f"I'm extremely frustrated and considering cancelling our contract. I expect this resolved today.\n\n{customer}"
    )
    ticket = f"#{random.randint(10000, 99999)}"
    gold = (
        f"Hi {customer},\n\nI'm sorry — this should never have taken three messages, and I understand your "
        f"frustration. I'm escalating this to our senior engineering team now under priority ticket {ticket} "
        f"and will personally own it until it's resolved. I'll call you today with a concrete update. Could you "
        f"confirm the best number to reach you?\n\nSincerely,\n{me}\nCustomer Success"
    )
    return (
        incoming, gold,
        [ticket, "escalating", "today"],
        ["sorry", ticket, "update"],
        ["calm down", "it's not a big deal", "nothing we can do"],
        "de_escalate_and_own", "apologetic-accountable",
        "Apologize, escalate to senior team, commit to a same-day update.", RiskLevel.HIGH,
    )


def gen_follow_up() -> Generated:
    sender = _first()
    me = _first()
    topic = random.choice(["the proposal", "my application", "the contract draft", "our quote"])
    days_ago = random.choice([5, 7, 10, 14])
    incoming = (
        f"Hi {me},\n\nJust following up on {topic} I sent about {days_ago} days ago. I haven't heard back and "
        f"wanted to check whether you need anything else from me.\n\nThanks,\n{sender}"
    )
    day = random.choice(DAYS)
    gold = (
        f"Hi {sender},\n\nThanks for the nudge and apologies for the delay on {topic}. It's currently with our "
        f"team for review, and I expect to have a clear answer for you by {day}. Nothing further is needed from "
        f"you right now — I'll follow up as soon as I hear back.\n\nBest,\n{me}"
    )
    return (
        incoming, gold,
        [topic, day, "review"],
        [topic, "by " + day],
        ["I forgot about you", "we lost your email"],
        "acknowledge_follow_up", "courteous-professional",
        "Acknowledge, give a concrete next-response date, set expectations.", RiskLevel.LOW,
    )


GENERATORS: Dict[Category, Callable[[], Generated]] = {
    Category.SCHEDULING: gen_scheduling,
    Category.RECRUITING: gen_recruiting,
    Category.CUSTOMER_SUPPORT: gen_customer_support,
    Category.SALES_DEMO: gen_sales_demo,
    Category.INVOICE_PAYMENT: gen_invoice_payment,
    Category.PROJECT_UPDATE: gen_project_update,
    Category.PARTNERSHIP: gen_partnership,
    Category.EVENT_LOGISTICS: gen_event_logistics,
    Category.COMPLAINT_ESCALATION: gen_complaint_escalation,
    Category.FOLLOW_UP: gen_follow_up,
}


def build_dataset(n: int, seed: int) -> List[EmailExample]:
    random.seed(seed)
    categories = list(GENERATORS.keys())
    examples: List[EmailExample] = []
    seen_emails: set[str] = set()

    idx = 0
    attempts = 0
    # Round-robin across categories so the dataset is balanced.
    while len(examples) < n and attempts < n * 20:
        attempts += 1
        category = categories[idx % len(categories)]
        idx += 1
        (incoming, gold, req, inc, notinc, intent, tone, action, risk) = GENERATORS[category]()
        if incoming in seen_emails:  # avoid exact duplicates
            continue
        seen_emails.add(incoming)
        examples.append(
            EmailExample(
                id=f"ex-{len(examples):04d}",
                category=category,
                intent=intent,
                tone=tone,
                incoming_email=incoming,
                gold_reply=gold,
                required_facts=req,
                must_include=inc,
                must_not_include=notinc,
                ideal_action=action,
                risk_level=risk,
            )
        )
    return examples


def write_jsonl(examples: List[EmailExample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ex in examples:
            fh.write(ex.model_dump_json() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the ReplyWise synthetic dataset.")
    parser.add_argument("--n", type=int, default=220, help="total examples (150-300 recommended)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--test-frac", type=float, default=0.15, help="fraction held out as test set")
    args = parser.parse_args()

    examples = build_dataset(args.n, args.seed)
    random.seed(args.seed + 1)
    random.shuffle(examples)

    n_test = max(10, int(len(examples) * args.test_frac))
    test = examples[:n_test]
    train = examples[n_test:]

    write_jsonl(train, DATA_DIR / "synthetic_emails.jsonl")
    write_jsonl(test, DATA_DIR / "test_emails.jsonl")

    print(f"Wrote {len(train)} training examples -> {DATA_DIR / 'synthetic_emails.jsonl'}")
    print(f"Wrote {len(test)} test examples     -> {DATA_DIR / 'test_emails.jsonl'}")
    by_cat: Dict[str, int] = {}
    for ex in examples:
        by_cat[ex.category.value] = by_cat.get(ex.category.value, 0) + 1
    print("Per-category counts:")
    for cat, cnt in sorted(by_cat.items()):
        print(f"  {cat:22s} {cnt}")


if __name__ == "__main__":
    main()
