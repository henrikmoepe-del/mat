# Decisions log

Add one dated line per decision: what was decided, who decided, and the source or meeting.
Format: `- YYYY-MM-DD – <decision> (decided by <who>; source: <file or meeting>)`

- 2026-10-27 – Frontend uses Flask templates (server-rendered), not a separate JavaScript app. (decided by team; source: team decision)
- 2026-10-27 – Login is basic: register and log in with a unique e-mail and password. Password reset by e-mail is not implemented in this version, because it needs an e-mail service. Deviates from `basic_desc.txt` (password retrieval/reset), which is deferred. (decided by team; source: team decision)
- 2026-10-27 – The interface is available in both Norwegian and English. (decided by team; source: team decision, `current_IT_landscape.txt`)
- 2026-10-27 – Minimum guests per event type use placeholder values (corporate lunch 8, birthday 10, confirmation 15, christmas party 20, conference 30, wedding 50) until the product owner confirms them. (decided by team; source: `docs/diagrams/README.md`)
- 2026-10-27 – Deposits are out of scope for this version, but the design must allow adding them later. (decided by team; source: team decision; resolves the Ingrid vs Sunniva/Fjordtek tension for now)
- 2026-10-27 – Corporate accounts are included: a company account with several users ordering, and orders above the company's approval limit must be approved by the company's approver. (decided by team; source: team decision, Fjordtek interview)
- 2026-10-27 – Kitchen and driver screens are included. (decided by team; source: team decision, Mateo interview, flowcharts)
- 2026-10-27 – Checkout asks for the event time (when the food should be ready), so drivers and the kitchen can plan the day (US-30). Allowed times 06:00–23:00 are a placeholder until Ingrid confirms opening hours. Customers can change the time until the 5-day lock. Orders placed before this have no time. (decided by Eirik M; source: feature 7 review, PR #14)
- 2026-10-27 – PIN login for kitchen and driver staff works only on devices an admin has approved (a long-lived cookie, revocable under Admin → Devices), not by IP address, because drivers use mobile data. (decided by Eirik M; source: feature 7 review, PR #14)
- 2026-10-27 – Backend folders show Model–View–Controller: `app/models/` (domain classes, rules, all Neo4j access), `app/views/` (templates), `app/controllers/` (blueprints, JSON API in `controllers/api/`). (proposed in plan, to be confirmed by team; source: oblig 4 technical requirements, `docs/plans/2026-10-27-mvc-folders.md`)
- 2026-10-27 – Admin manages food items (US-18). Items on an order can't be deleted, only hidden, so order history stays readable. (proposed in plan, to be confirmed by team; source: `docs/plans/2026-10-27-food-items-admin.md`)
- 2026-10-27 – Food pictures are uploaded (JPG/PNG/WebP, max 5 MB), not AI-generated: no external service or API key needed. New pictures are pending until the admin approves them. (proposed in plan, to be confirmed by team; source: oblig 4 A2, US-19, `docs/plans/2026-10-27-food-images.md`)
- 2026-10-27 – The seed script creates synthetic test accounts (admin, kitchen, driver, two customers); `--no-accounts` skips them on a real server. (proposed in plan, to be confirmed by team; source: oblig 4 "Running it", `docs/plans/2026-10-27-seed-accounts.md`)
