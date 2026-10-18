# Small milestones, with acceptance criteria

## 1 — Enquiry to draft (implemented)

Customer general/referral enquiry, scoped tracking, staff sessions, manager assignment history, salesperson access, three verified catalogue models and immutable demo quotation drafts. All software runs locally without paid services.

## 2 — Reviewed quotations and customer response

Add maintained-price administration restricted to authorized staff with history; verify whether actual prices may be used. Keep demo data clearly segregated. Add explicit salesperson review/release, safe printable quotation output, version-specific customer access and accept/request-changes responses. A draft must never become public simply because it is saved. Revise/supersede without destroying earlier customer-visible versions. No paid email or messaging API; a copyable scoped link is the initial delivery method.

Acceptance: a salesperson reviews a draft, explicitly releases a version, personally shares the link, and the customer responds only to that version. Tests enforce ownership, expiry, immutability and price provenance.

## 3 — Appointment and site-visit workflow

Customer or salesperson requests a time; the other party confirms, declines or proposes a change. A requested appointment is not automatically confirmed. Log site visits separately with property-specific checklists, findings and next steps. Add size/type-limited uploads with randomized names, ownership checks and access-controlled storage. Customer photos are preliminary context; a visit checks lighting, sight lines, cable paths, mounting, power, network and coverage in person.

Acceptance: request → confirm → visit log, with time-zone handling, conflict checks and access controls. Uploads must not be publicly guessable or executed.

## 4 — Catalogue expansion and transparent rules

Review more of the 63 pending PDFs, preserving field-level source evidence. Add filters and rule-based recommendations only over verified fields, with reasons, unknowns and site-survey caveats. Do not equate illumination range with identification distance or promise coverage from a model alone. No fabricated DVR/NVR/storage compatibility, pricing, stock or installation assumptions.

Acceptance: every recommended attribute is traceable to the reviewed catalogue; missing facts produce a question or unknown, not an invented answer.

## 5 — Local AI assistance

Start with editable structured templates and deterministic extraction where useful. If the computer can run a suitable open-source model at ₹0 service cost, evaluate a local inference option. Model downloads, licensing, memory, speed and hallucination testing must be checked first. Do not make hardware purchases or activate paid inference. Keep a fully working no-model path.

AI may propose requirement fields, summarize visit notes and explain rule results. The salesperson verifies and edits its output. AI must never assert unverified product facts, set authoritative prices, assign leads or send quotations autonomously.

Acceptance: outputs cite input evidence, visibly distinguish unknowns, and require review before being saved as customer-facing content.

## Zero-cost demonstration and deployment

Use the local server on the existing laptop for college evaluation. The current launcher binds only to loopback. An institutional machine or local-network demo is an option only with explicit network and data-access setup; changing the bind address alone is not a secure deployment. A public host can be considered later only after verifying ₹0/no-card terms and preparing authentication, HTTPS, backups, limits and privacy controls. No hosting signup is needed for any current milestone.
