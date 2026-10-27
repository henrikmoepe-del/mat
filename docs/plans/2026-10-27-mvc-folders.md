# Plan: folder structure that shows Model–View–Controller

**Status:** implemented · **Source:** oblig 4 technical requirements ("the three layers must be visible in your folder
structure")

## Goal

The code was already layered (Cypher only in `repositories/`, templates only render), but the folders were called
`pages/`, `routes/`, `repositories/` and `templates/`, and the domain rules (`cart.py`, `orders.py`) sat at the top of
`app/`. A reader should see Model, View and Controller straight away.

## Design

| Before | After | Layer |
|---|---|---|
| `app/repositories/` | `app/models/repositories/` | Model (data access) |
| `app/db.py` | `app/models/db.py` | Model (Neo4j driver) |
| `app/cart.py`, `app/orders.py` | `app/models/cart.py`, `app/models/orders.py` | Model (domain rules) |
| – | `app/models/food_items.py` (`FoodItem` class), `app/models/image_store.py` | Model (new, see the A1/A2 plans) |
| `app/templates/` | `app/views/` (`Flask(__name__, template_folder="views")`) | View |
| `app/pages/` | `app/controllers/` | Controller (HTML pages) |
| `app/routes/` | `app/controllers/api/` | Controller (JSON API) |

Shared modules stay in `app/`: `auth.py`, `i18n.py`, `mail.py`, `jobs.py`, `cli.py`, `config.py`, `urls.py`.

## Steps

1. Move the files; no code changes inside them except imports.
2. Rewrite imports with a script (`from ..repositories` → `from ..models.repositories`, `from .. import orders` →
   `from ..models import orders`, one more `.` in `controllers/api/`), also in `tests/` and `scripts/`.
3. Run the whole test suite before and after: the same tests must pass (179 before the move).
4. Update `backend/README.md` (Layout), `CLAUDE.md` and `app/__init__.py`'s docstring.

## Risks

- Import cycles: none expected, models never import controllers.
- Blueprint and endpoint names don't change, so `url_for(...)` in templates and tests keep working.
