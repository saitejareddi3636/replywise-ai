# ReplyWise AI — Evaluation Report

- **Examples evaluated:** 33
- **Average final score:** 0.834 / 1.00
- **Pass rate:** 81.8% (threshold 0.70)

## Score by category

| Category | Count | Avg score | Pass rate |
|---|---:|---:|---:|
| complaint_escalation | 2 | 0.853 | 100% |
| customer_support | 3 | 0.849 | 100% |
| event_logistics | 4 | 0.670 | 50% |
| follow_up | 4 | 0.789 | 100% |
| invoice_payment | 6 | 0.988 | 100% |
| partnership | 2 | 0.970 | 100% |
| project_update | 3 | 0.902 | 100% |
| recruiting | 3 | 0.859 | 100% |
| sales_demo | 2 | 0.782 | 100% |
| scheduling | 4 | 0.683 | 0% |

## Common failure types

- **missing required facts**: 6
- **possible hallucination**: 4

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

### `ex-0193` — invoice_payment — score 0.992 (PASS)
- **Incoming:** Hello, We received invoice INV-2347 for $3,600 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, James — Brightpath
- **Generated:** Hi James, Thanks for flagging invoice INV-2347. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $3,600. A revised copy is attached, and payment terms remain net-30. Please let me know…
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=0.99, facts=1.00, intent=0.97, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0122` — invoice_payment — score 0.991 (PASS)
- **Incoming:** Hello, We received invoice INV-8372 for $5,000 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, Tom — Orbit Logistics
- **Generated:** Hi Tom, Thanks for flagging invoice INV-8372. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $5,000. A revised copy is attached, and payment terms remain net-30. Please let me know i…
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=1.00, facts=1.00, intent=0.95, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

### `ex-0074` — invoice_payment — score 0.991 (PASS)
- **Incoming:** Hello, We received invoice INV-7844 for $3,600 but the PO number is missing and one line item looks duplicated. Could you review before we process payment? Thanks, Sarah — Copperline
- **Generated:** Hi Sarah, Thanks for flagging invoice INV-7844. You're right — I've removed the duplicated line item and added your PO number, so the corrected total is $3,600. A revised copy is attached, and payment terms remain net-30. Please let me know…
- **Why:** Final score 0.99 (PASS, threshold 0.70). All required facts are present. No ungrounded specifics detected.
- **Metrics:** sim=1.00, facts=1.00, intent=0.94, tone=1.00, help=1.00, safety=1.00, mni_violation=0.00

## Worst examples

### `ex-0077` — event_logistics — score 0.556 (FAIL)
- **Incoming:** Hi, I'm finalizing details for the workshop. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Elena
- **Generated:** Hi Elena, To confirm the details for the workshop, could you please provide me with more information about the specific workshop you are referring to, such as the date or location? This will help me provide you with the most accurate inform…
- **Why:** Final score 0.56 (FAIL, threshold 0.70). Poor fact coverage (0%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.51, facts=0.00, intent=0.66, tone=1.00, help=0.70, safety=1.00, mni_violation=0.00

### `ex-0160` — event_logistics — score 0.642 (FAIL)
- **Incoming:** Hi, I'm finalizing details for the customer summit. Can you confirm the headcount, start time, and whether we need any dietary accommodations? Thanks, Omar
- **Generated:** Hi Omar, Confirmed for the customer summit: we're expecting attendees, and the start time is. Please plan for dietary accommodations. I'll share the final rooming and agenda by. Let me know if the caterer needs anything else from us. Best, …
- **Why:** Final score 0.64 (FAIL, threshold 0.70). Poor fact coverage (0%); key details are absent. No ungrounded specifics detected.
- **Metrics:** sim=0.86, facts=0.00, intent=0.76, tone=1.00, help=0.70, safety=1.00, mni_violation=0.00

### `ex-0163` — scheduling — score 0.667 (FAIL)
- **Incoming:** Hi Tom, Could we find 30 minutes this week to discuss the integration review? I'm fairly flexible but afternoons work best for me. Let me know what suits you. Thanks, Sofia
- **Generated:** Hi Sofia, Happy to meet about the integration review. Wednesday at 2:00 PM ET works well on my end — I'll send a calendar invite with a video link. If that time doesn't suit you, just share a couple of afternoon slots and I'll adjust. Best,…
- **Why:** Final score 0.67 (FAIL, threshold 0.70). Partial fact coverage (50%) — some required details are missing. Possible ungrounded specifics detected (safety 0%).
- **Metrics:** sim=0.93, facts=0.50, intent=0.86, tone=1.00, help=0.85, safety=0.00, mni_violation=0.00

### `ex-0153` — scheduling — score 0.676 (FAIL)
- **Incoming:** Hi Aisha, Could we find 30 minutes this week to discuss the Q3 roadmap? I'm fairly flexible but afternoons work best for me. Let me know what suits you. Thanks, James
- **Generated:** Hi James, Happy to meet about the Q3 roadmap. Wednesday at 3:00 PM PT works well on my end — I'll send a calendar invite with a video link. If that time doesn't suit you, just share a couple of afternoon slots and I'll adjust. Best, Aisha
- **Why:** Final score 0.68 (FAIL, threshold 0.70). Partial fact coverage (50%) — some required details are missing. Possible ungrounded specifics detected (safety 0%).
- **Metrics:** sim=0.96, facts=0.50, intent=0.88, tone=1.00, help=0.85, safety=0.00, mni_violation=0.00

### `ex-0172` — scheduling — score 0.695 (FAIL)
- **Incoming:** Hi James, Could we find 30 minutes this week to discuss onboarding? I'm fairly flexible but afternoons work best for me. Let me know what suits you. Thanks, Mei
- **Generated:** Hi Mei, Happy to meet about onboarding. Friday at 2:00 PM works well on my end — I'll send a calendar invite with a video link. If that time doesn't suit you, just share a couple of afternoon slots and I'll adjust. Best, James
- **Why:** Final score 0.69 (FAIL, threshold 0.70). Partial fact coverage (50%) — some required details are missing. Possible ungrounded specifics detected (safety 0%).
- **Metrics:** sim=0.96, facts=0.50, intent=1.00, tone=1.00, help=0.85, safety=0.00, mni_violation=0.00
