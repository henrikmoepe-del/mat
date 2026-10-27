# Plans

Every larger feature is planned before it is built: in Claude Code **plan mode** the agent reads the code and the
user stories and proposes a plan, the team reviews and adjusts it, and the agreed plan is committed here before
implementation starts (team rule in `CLAUDE.md`).

File name: `YYYY-MM-DD-<feature>.md`. Each plan has the goal and source, the design (which files in models, views
and controllers), the rules and edge cases, the tests, and what is left out. When the feature is done, set
**Status** to *implemented* and note anything that changed on the way.

| Plan | Feature | Status |
|---|---|---|
| [2026-10-27-mvc-folders.md](2026-10-27-mvc-folders.md) | Folder structure that shows Model–View–Controller | implemented |
| [2026-10-27-food-items-admin.md](2026-10-27-food-items-admin.md) | A1: admin manages food items (US-18) | implemented |
| [2026-10-27-food-images.md](2026-10-27-food-images.md) | A2: upload, preview and approve pictures (US-19) | implemented |
| [2026-10-27-seed-accounts.md](2026-10-27-seed-accounts.md) | Seed script creates an admin and test customers | implemented |
