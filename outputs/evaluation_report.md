# ReplyWise AI — Evaluation Report

- **Examples evaluated:** 33
- **Average final score:** 0.870 / 1.00
- **Pass rate:** 90.9% (threshold 0.70)

## Score by category

| Category | Count | Avg score | Pass rate |
|---|---:|---:|---:|
| complaint_escalation | 2 | 0.853 | 100% |
| customer_support | 3 | 0.849 | 100% |
| event_logistics | 4 | 0.667 | 25% |
| follow_up | 4 | 0.789 | 100% |
| invoice_payment | 6 | 0.988 | 100% |
| partnership | 2 | 0.970 | 100% |
| project_update | 3 | 0.902 | 100% |
| recruiting | 3 | 0.858 | 100% |
| sales_demo | 2 | 0.785 | 100% |
| scheduling | 4 | 0.981 | 100% |

## Common failure types

- **missing required facts**: 3

## Best examples

### `ex-0211` — invoice_payment — score 0.994 (PASS)
- **Incoming:** Hello, We received invoice INV-1919 for $8,750 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, Hana — Northwind Labs
- **Generated:** Hi Hana, Thanks for flagging invoice INV-1919. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $8,750. A revised copy is attached, and payment terms remain net-30. Please let me know …
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=1.00, facts=1.00, intent=0.97, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0140` — invoice_payment — score 0.993 (PASS)
- **Incoming:** Hello, We received invoice INV-4283 for $3,600 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, Priya — Fernpath
- **Generated:** Hi Priya, Thanks for flagging invoice INV-4283. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $3,600. A revised copy is attached, and payment terms remain net-30. Please let me know…
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=0.99, facts=1.00, intent=0.97, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0190` — scheduling — score 0.993 (PASS)
- **Incoming:** Hi Carlos, Could we find 30 minutes this week to discuss onboarding? I'm fairly flexible but afternoons work best for me. Let me know what suits you. Thanks, Hana
- **Generated:** Hi Hana, Happy to meet about onboarding. Wednesday at 2:00 PM works well on my end — I'll send a calendar invite with a video link. If that time doesn't suit you, just share a couple of afternoon slots and I'll adjust. Best, Carlos
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=0.96, facts=1.00, intent=1.00, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0193` — invoice_payment — score 0.992 (PASS)
- **Incoming:** Hello, We received invoice INV-2347 for $3,600 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, James — Brightpath
- **Generated:** Hi James, Thanks for flagging invoice INV-2347. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $3,600. A revised copy is attached, and payment terms remain net-30. Please let me know…
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=0.99, facts=1.00, intent=0.97, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0172` — scheduling — score 0.992 (PASS)
- **Incoming:** Hi James, Could we find 30 minutes this week to discuss onboarding? I'm fairly flexible but afternoons work best for me. Let me know what suits you. Thanks, Mei
- **Generated:** Hi Mei, Happy to meet about onboarding. Friday at 2:00 PM works well on my end — I'll send a calendar invite with a video link. If that time doesn't suit you, just share a couple of afternoon slots and I'll adjust. Best, James
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=0.96, facts=1.00, intent=1.00, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

## Worst examples

### `ex-0115` — event_logistics — score 0.639 (FAIL)
- **Incoming:** Hi, I'm finalizing details for the team offsite. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Ben
- **Generated:** Hi Ben, Confirmed for the team offsite: we're expecting attendees, and the start time is. Please plan for dietary accommodations. I'll share the final rooming and agenda by. Let me know if the caterer needs anything else from us. Best, [Nam…
- **Why:** Final score 0.64 (FAIL, threshold 0.70). Poor fact coverage (0%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.88, facts=0.00, intent=0.72, tone=1.00, help=0.70, safety=1.00, mni_violation=0.00

### `ex-0077` — event_logistics — score 0.640 (FAIL)
- **Incoming:** Hi, I'm finalizing details for the workshop. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Elena
- **Generated:** Hi Elena, Confirmed for the workshop: we're expecting attendees, and the start time is. Please plan for dietary accommodations. I'll share the final rooming and agenda by. Let me know if the caterer needs anything else from us. Best, Sarah
- **Why:** Final score 0.64 (FAIL, threshold 0.70). Poor fact coverage (0%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.85, facts=0.00, intent=0.77, tone=1.00, help=0.70, safety=1.00, mni_violation=0.00

### `ex-0160` — event_logistics — score 0.642 (FAIL)
- **Incoming:** Hi, I'm finalizing details for the customer summit. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Omar
- **Generated:** Hi Omar, Confirmed for the customer summit: we're expecting attendees, and the start time is. Please plan for dietary accommodations. I'll share the final rooming and agenda by. Let me know if the caterer needs anything else from us. Best, …
- **Why:** Final score 0.64 (FAIL, threshold 0.70). Poor fact coverage (0%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.86, facts=0.00, intent=0.76, tone=1.00, help=0.70, safety=1.00, mni_violation=0.00

### `ex-0162` — follow_up — score 0.718 (PASS)
- **Incoming:** Hi Omar, Just following up on my application I sent about 7 days ago. I haven't heard back and wanted to check whether you need anything else from me. Thanks, Sofia
- **Generated:** Hi Sofia, Thanks for the nudge and apologies for the delay on your application. It's currently with our team for review, and I expect to have a clear answer for you by Friday. Nothing further is needed from you right now — I'll follow up as…
- **Why:** Final score 0.72 (PASS, threshold 0.70). Poor fact coverage (33%); key details are absent. No ungrounded specifics detected. Reply drifts from the sender's core intent.
- **Metrics:** sim=0.99, facts=0.33, intent=0.45, tone=1.00, help=0.80, safety=1.00, mni_violation=0.00

### `ex-0047` — event_logistics — score 0.746 (PASS)
- **Incoming:** Hi, I'm finalizing details for the customer summit. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Mei
- **Generated:** Hi Mei, Confirmed for the customer summit: we're expecting [number] attendees, and the start time is [time]. Please plan for [number] vegetarian and [number] gluten-free meals. I'll share the final rooming and agenda by [day]. Let me know i…
- **Why:** Final score 0.75 (PASS, threshold 0.70). Poor fact coverage (33%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.94, facts=0.33, intent=0.70, tone=1.00, help=0.80, safety=1.00, mni_violation=0.00
