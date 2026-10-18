# Milestone 1 verification — 17 October 2026

- **23 automated tests passed** against temporary SQLite databases (22.29 seconds in the final run).
- React/TypeScript production build passed after final formatting and layout changes.
- `alembic upgrade head` applied the initial schema; `alembic check` reported no unrepresented model changes.
- Dependency installation reported zero npm audit vulnerabilities at installation time. This is not a full security audit.
- One known test-only dependency warning: Starlette deprecates its current HTTPX adapter. No failed tests.

Covered behavior: general/referral intake, ownership and manager-only assignment, cross-salesperson isolation, immutable referral attribution, stale and concurrent write rejection, scoped/expired tracking, hashed tokens, session expiry/logout, mutation protection, input limits, unknown fields, rate limits, manager draft restrictions, verified-product requirements, duplicate/invalid quote lines, server totals, source snapshots, price changes across versions, PDF authentication, archive path traversal rejection, evidence hashes and idempotent seeding.

Browser checks on the built app:

1. Manager login and enquiry list.
2. Assign Demo · Lotus Mart to Arjun with an audit reason.
3. Arjun login and access to that enquiry.
4. Create draft v1: four units of PT-NC140D3-N(D2), 4 mm lens, **₹14,000 demo equipment subtotal**.
5. Submit fictional Demo · Cedar House through Priya's referral form.
6. Follow its private tracking link; verify Priya is the assigned salesperson.
7. Check the catalogue's source links and demo-price labels.
8. Inspect desktop width 1440 and phone width 390. Fix and verify a page-level horizontal overflow issue; enquiry tables retain their intended internal scrolling.
9. No browser warning/error logs in the tested flow.

The demo database deliberately retains the walkthrough results: five enquiries, one saved draft, and the manager assignment event. The screenshot `screenshots/manager-workspace.jpg` shows that state. No actual customer was contacted and no external quotation was sent.

The local preview server was used for verification and stopped after testing. Start it again with `Start-VisionAssist.cmd`.

Not verified: PostgreSQL execution or data migration, public deployment, real pricing/availability, email/SMS delivery, appointments, uploads, site visits, quotation release/customer response, or AI. These are not implemented in milestone 1.
