# Plan: admin manages food items (A1, US-18)

**Status:** implemented · **Source:** oblig 4 A1; US-18; `basic_desc.txt` admin "Food items"; Mateo interview (menus
change about four times a year)

## Goal

The admin adds, edits and removes food items: name and description (Norwegian and English), price in NOK, minimum
order quantity, event types, allergens, diets and whether the item is published. Until now items only came from the
seed script.

## Design (MVC)

- **Model** `app/models/food_items.py`: `FoodItem` dataclass (the domain class), `parse_form()` that validates the form
  and returns `(FoodItem, errors)` in the same `(key, args)` format as `orders.parse_checkout()`, and `slug()` /
  `free_id()` for readable ids like the seeded ones (`layer-cake`, `layer-cake-2`).
- **Model** `app/models/repositories/food_items.py`: `options()`, `list_all()`, `get()`, `create()`, `update()`,
  `set_published()`, `delete()`. Event types, allergens and diets are relationships (`SUITS`, `CONTAINS_ALLERGEN`,
  `FITS_DIET`), replaced as a whole on update.
- **Controller** `app/controllers/food_items.py`: blueprint `food_items` at `/admin/food-items`, all routes
  `staff_required("admin")`.
- **Views** `admin_food_items.html` (list with publish/hide buttons) and `admin_food_item.html` (form; on edit also
  pictures and delete). A "Food items" link in the admin header. All text in `i18n.py` in both languages.

## Rules

- Both names are required (max 100 characters); descriptions max 500.
- Price: whole NOK, 0–100 000. Minimum order: 1–9 999 (the cart's sanity limit).
- At least one event type. Unknown event types, allergens and diets in the form are ignored.
- Changing a price doesn't change orders: prices are already copied onto each order line (data model, design choice 1).
- Unpublished items disappear from the menu and the cart at once (existing queries filter on `published: true`).
- **Delete** needs a confirmation tick and is refused for items on an order, so order history stays readable; the
  page tells the admin to hide the item instead. Deleting removes the item's pictures (nodes and files) too.

## Tests

- Unit (`tests/test_food_items.py`, fake driver): form validation cases, round trip `as_form()` → `parse_form()`,
  slugs, access (customer/kitchen get 403), list, create (id collision), invalid form re-shown with the admin's input
  and status 400, edit form pre-filled, update, 404s, publish/hide, delete with and without the tick, item on an order.
- Integration (`tests/integration/test_neo4j_food_items.py`): the real Cypher for create/update/publish/delete, the
  menu reflecting the changes, and an item on an order not being deleted.

## Left out

- Editing recipes/ingredients (prep list sample data) on this page.
- Food origin per item (Ingrid's wish): would be `(:Ingredient)-[:SUPPLIED_BY]->(:Supplier)`, see data model.
