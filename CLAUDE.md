# Ekte Mat Online

Online ordering for Ekte Mat AS, a (fictional) catering company in Bergen (INFO212, oblig 4/5). Customers browse menus
by event type, fill a cart, order and ask questions. Ekte Mat staff manage food items, pictures, orders, payment status
and questions, and use kitchen and driver screens. Requirements: `docs/requirements/user_stories.md` (US-xx),
case material in `docs/context/` (read-only).

Use Flask for backend
Use Neo4j for data storage
Do not, under any circumstance, publish the Claude API key

## MVC layout (`backend/app/`)

- `models/` – domain classes and rules (`food_items.py`, `orders.py`, `cart.py`) and ALL data access:
  `models/repositories/` (Cypher, one module per feature), `models/db.py` (Neo4j driver), `models/image_store.py`.
- `views/` – Jinja2 templates (`base.html` + one per page). UI text goes in `i18n.py`, in Norwegian AND English.
- `controllers/` – Flask blueprints: HTML pages (`controllers/*.py`), JSON API (`controllers/api/`).
- Shared: `auth.py` (logins, `staff_required`/`customer_required`), `mail.py` (dev outbox), `jobs.py`, `cli.py`.

Controllers never run Cypher; they call `models/repositories`. Templates never query anything.

## Run and test (from `backend/`; details in `backend/README.md`)

```sh
docker compose --env-file .env -f ../docker-compose.yml up -d   # Neo4j
pip install -r requirements.txt
python -m scripts.seed      # constraints, sample menu, sample admin/staff/customers (dev only)
python run.py               # http://localhost:5001
python -m pytest            # unit tests, fake Neo4j driver, no database needed
RUN_NEO4J_TESTS=1 python -m pytest   # also the integration tests against the local Neo4j
```

## Team rules

- Plan larger features in plan mode first and commit the agreed plan to `docs/plans/YYYY-MM-DD-<feature>.md`.
- Every feature gets unit tests (`tests/`, fake driver) and, for new Cypher, an integration test (`tests/integration/`).
- Every `POST` form includes `csrf_token`. Admin pages use `staff_required("admin")`.
- Synthetic data only. Never commit `.env`, uploads (`backend/uploads/`) or any API key.
- Record decisions as dated lines in `docs/decisions.md`; keep `docs/diagrams/data_model.md` in step with the graph.
- Work on a branch, open a pull request, one teammate reviews before merging to `main`.
