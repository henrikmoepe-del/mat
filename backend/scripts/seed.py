"""Creates constraints and sample data. Safe to run more than once.

Run from the backend folder:  python -m scripts.seed

Event-type minimums are placeholder values (decision 2026-10-27). Food items are SAMPLE DATA: the first four come
from Mateo's autumn lunch menu draft (docs/context/05_reference), the rest are invented so every event type has dishes.
Ingredients and recipes are SAMPLE DATA too (amounts per portion invented for the prep list, US-29); Mateo should
replace them with real ones. Existing nodes are never overwritten (ON CREATE), so changes made by the admin survive
re-seeding, and a dish gets its sample recipe only while it has none.

Sample ACCOUNTS (an admin, kitchen and driver staff, and two test customers) are created too, with the test passwords
below, so the app can be tried straight away. They are synthetic, for development only: on a real server, seed with
`python -m scripts.seed --no-accounts` and create staff with `flask create-staff`. Existing accounts are left as they are.
"""
import argparse
import os

from app import auth, create_app
from app.models import image_store
from app.models.db import run
from app.models.repositories import customers, food_items as food_repo, staff

# One picture per sample dish: seed_images/<food item id>.jpg (free Pexels photos, credits in seed_images/CREDITS.md).
SEED_IMAGES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed_images")

EVENT_TYPES = [
    ("corporate-lunch", "Firmalunsj", "Corporate lunch", 8),
    ("birthday", "Bursdag", "Birthday", 10),
    ("confirmation", "Konfirmasjon", "Confirmation", 15),
    ("christmas-party", "Julebord", "Christmas party", 20),
    ("conference", "Konferanse", "Conference", 30),
    ("wedding", "Bryllup", "Wedding", 50),
]

# Allergens to label, from the lunch menu draft, plus egg.
ALLERGENS = [
    ("fish", "Fisk", "Fish"),
    ("milk", "Melk", "Milk"),
    ("gluten", "Gluten", "Gluten"),
    ("nuts", "Nøtter", "Nuts"),
    ("celery", "Selleri", "Celery"),
    ("mustard", "Sennep", "Mustard"),
    ("egg", "Egg", "Egg"),
]

DIETS = [
    ("vegetarian", "Vegetar", "Vegetarian"),
    ("vegan", "Vegansk", "Vegan"),
    ("gluten-free", "Glutenfri", "Gluten-free"),
    ("lactose-free", "Laktosefri", "Lactose-free"),
]

# id, name_no, name_en, description_no, description_en, price_nok, min_order_qty, event types, allergens, diets
FOOD_ITEMS = [
    ("fish-soup", "Fiskesuppe med Bergen-torsk", "Fish soup with Bergen cod",
     "Med rotgrønnsaker og surdeigsbrød.", "With root vegetables and sourdough bread.",
     189, 10, ["corporate-lunch", "conference"], ["fish", "milk", "gluten", "celery"], []),
    ("voss-lamb", "Saktekokt lam fra Voss", "Slow-cooked lamb from Voss",
     "Med byggotto.", "With barley risotto.",
     245, 10, ["conference", "confirmation", "christmas-party", "wedding"], ["milk", "gluten", "celery"], []),
    ("beetroot-salad", "Rødbete- og kikertsalat", "Beetroot and chickpea salad",
     "Med geitost fra Hardanger.", "With goat cheese from Hardanger.",
     165, 8, ["corporate-lunch", "birthday", "conference", "confirmation"], ["milk", "mustard"],
     ["vegetarian", "gluten-free"]),
    ("rakfisk", "Rakfisk-smaking", "Rakfisk tasting",
     "Sesongrett, kun i november.", "Seasonal, November only.",
     210, 10, ["christmas-party"], ["fish", "milk", "gluten"], []),
    ("pinnekjott", "Pinnekjøtt med kålrabistappe", "Pinnekjøtt with mashed swede",
     "Tradisjonell julemat.", "Traditional Norwegian Christmas dish.",
     295, 15, ["christmas-party"], ["milk", "celery"], ["gluten-free"]),
    ("layer-cake", "Bløtkake med bær", "Cream layer cake with berries",
     "Hjemmelaget, med sesongens bær.", "Home-made, with berries of the season.",
     85, 10, ["birthday", "confirmation", "wedding"], ["milk", "egg", "gluten"], ["vegetarian"]),
    ("wedding-menu", "Tre-retters bryllupsmeny", "Three-course wedding menu",
     "Forrett, hovedrett og dessert, servert.", "Starter, main course and dessert, served.",
     695, 40, ["wedding"], ["fish", "milk", "gluten", "nuts", "celery"], []),
    ("lentil-stew", "Vegansk linsegryte", "Vegan lentil stew",
     "Med urter og ris.", "With herbs and rice.",
     155, 8, ["corporate-lunch", "birthday", "conference"], ["celery"],
     ["vegan", "vegetarian", "gluten-free", "lactose-free"]),
    ("sandwich-platter", "Smørbrødfat", "Open sandwich platter",
     "Utvalg av påsmurt brød.", "A selection of open sandwiches.",
     129, 10, ["corporate-lunch", "conference", "confirmation"], ["fish", "milk", "egg", "gluten", "mustard"], []),
]

# id, name_no, name_en, unit (kg, l or pcs)
INGREDIENTS = [
    ("cod", "Torskefilet", "Cod fillet", "kg"),
    ("fish-stock", "Fiskekraft", "Fish stock", "l"),
    ("cream", "Fløte", "Cream", "l"),
    ("root-vegetables", "Rotgrønnsaker", "Root vegetables", "kg"),
    ("sourdough", "Surdeigsbrød", "Sourdough bread", "kg"),
    ("lamb", "Lammeskulder fra Voss", "Lamb shoulder from Voss", "kg"),
    ("barley", "Byggryn", "Pearl barley", "kg"),
    ("butter", "Smør", "Butter", "kg"),
    ("beetroot", "Rødbeter", "Beetroot", "kg"),
    ("chickpeas", "Kikerter", "Chickpeas", "kg"),
    ("goat-cheese", "Geitost fra Hardanger", "Goat cheese from Hardanger", "kg"),
    ("rakfisk", "Rakfisk", "Rakfisk", "kg"),
    ("potatoes", "Poteter", "Potatoes", "kg"),
    ("pinnekjott", "Pinnekjøtt", "Cured lamb ribs", "kg"),
    ("swede", "Kålrot", "Swede", "kg"),
    ("eggs", "Egg", "Eggs", "pcs"),
    ("flour", "Hvetemel", "Wheat flour", "kg"),
    ("berries", "Bær", "Berries", "kg"),
    ("smoked-salmon", "Røkelaks", "Smoked salmon", "kg"),
    ("beef", "Indrefilet av storfe", "Beef tenderloin", "kg"),
    ("lentils", "Linser", "Lentils", "kg"),
    ("rice", "Ris", "Rice", "kg"),
    ("bread", "Brød", "Bread", "kg"),
]

# food item id -> [(ingredient id, amount per portion in the ingredient's unit)]
RECIPES = {
    "fish-soup": [("cod", 0.12), ("fish-stock", 0.25), ("cream", 0.08), ("root-vegetables", 0.1), ("sourdough", 0.06)],
    "voss-lamb": [("lamb", 0.25), ("barley", 0.07), ("root-vegetables", 0.1), ("butter", 0.02)],
    "beetroot-salad": [("beetroot", 0.15), ("chickpeas", 0.08), ("goat-cheese", 0.04)],
    "rakfisk": [("rakfisk", 0.15), ("potatoes", 0.2), ("butter", 0.02)],
    "pinnekjott": [("pinnekjott", 0.4), ("swede", 0.25), ("potatoes", 0.2), ("butter", 0.03)],
    "layer-cake": [("eggs", 0.5), ("flour", 0.02), ("cream", 0.08), ("berries", 0.05)],
    "wedding-menu": [("smoked-salmon", 0.06), ("beef", 0.2), ("potatoes", 0.2), ("cream", 0.1), ("berries", 0.05),
                     ("eggs", 0.5)],
    "lentil-stew": [("lentils", 0.08), ("root-vegetables", 0.12), ("rice", 0.08)],
    "sandwich-platter": [("bread", 0.1), ("smoked-salmon", 0.04), ("eggs", 1), ("butter", 0.02)],
}

# Development only (see the docstring). e-mail, name, role, password
SAMPLE_STAFF = [
    ("admin@ektemat.test", "Ingrid Solheim (test)", "admin", "admin-passord-123"),
    ("kjokken@ektemat.test", "Mateo Rinaldi (test)", "kitchen", "kjokken-passord-123"),
    ("sjafor@ektemat.test", "Ola Sjåfør (test)", "driver", "sjafor-passord-123"),
]

# e-mail, name, phone, language, password
SAMPLE_CUSTOMERS = [
    ("kari@kunde.test", "Kari Nordmann", "+47 400 00 001", "no", "kunde-passord-123"),
    ("alex@customer.test", "Alex Smith", "+47 400 00 002", "en", "customer-password-123"),
]

CONSTRAINTS = [
    "CREATE CONSTRAINT event_type_id IF NOT EXISTS FOR (e:EventType) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT food_item_id IF NOT EXISTS FOR (f:FoodItem) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT customer_email IF NOT EXISTS FOR (c:Customer) REQUIRE c.email IS UNIQUE",
    "CREATE CONSTRAINT staff_email IF NOT EXISTS FOR (s:Staff) REQUIRE s.email IS UNIQUE",
    "CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE",
    "CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE",
    "CREATE CONSTRAINT allergen_code IF NOT EXISTS FOR (a:Allergen) REQUIRE a.code IS UNIQUE",
    "CREATE CONSTRAINT ingredient_id IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT diet_code IF NOT EXISTS FOR (d:Diet) REQUIRE d.code IS UNIQUE",
    "CREATE CONSTRAINT image_id IF NOT EXISTS FOR (i:Image) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT pin_device_token IF NOT EXISTS FOR (d:PinDevice) REQUIRE d.token_hash IS UNIQUE",
    # Not a constraint, but created the same way: the admin list and the kitchen and driver screens filter on these.
    "CREATE INDEX order_status_date IF NOT EXISTS FOR (o:Order) ON (o.status, o.event_date)",
]


def seed() -> None:
    for c in CONSTRAINTS:
        run(c)
    for id_, name_no, name_en, minimum in EVENT_TYPES:
        run(
            "MERGE (e:EventType {id: $id}) "
            "ON CREATE SET e.name_no = $no, e.name_en = $en, e.min_guests = $min",
            id=id_, no=name_no, en=name_en, min=minimum,
        )
    for label, rows in (("Allergen", ALLERGENS), ("Diet", DIETS)):
        for code, name_no, name_en in rows:
            run(
                f"MERGE (n:{label} {{code: $code}}) ON CREATE SET n.name_no = $no, n.name_en = $en",
                code=code, no=name_no, en=name_en,
            )
    for (id_, name_no, name_en, desc_no, desc_en, price, min_qty,
         event_types, allergens, diets) in FOOD_ITEMS:
        run(
            """
            MERGE (f:FoodItem {id: $id})
            ON CREATE SET f.name_no = $name_no, f.name_en = $name_en,
                          f.description_no = $desc_no, f.description_en = $desc_en,
                          f.price_nok = $price, f.min_order_qty = $min_qty, f.published = true,
                          f.just_created = true
            // Link only new items, so links the admin has changed aren't re-added.
            WITH f WHERE f.just_created
            REMOVE f.just_created
            FOREACH (eid IN $event_types |
                MERGE (e:EventType {id: eid}) MERGE (f)-[:SUITS]->(e))
            FOREACH (code IN $allergens |
                MERGE (a:Allergen {code: code}) MERGE (f)-[:CONTAINS_ALLERGEN]->(a))
            FOREACH (code IN $diets |
                MERGE (d:Diet {code: code}) MERGE (f)-[:FITS_DIET]->(d))
            """,
            id=id_, name_no=name_no, name_en=name_en, desc_no=desc_no, desc_en=desc_en,
            price=price, min_qty=min_qty, event_types=event_types, allergens=allergens, diets=diets,
        )
    for id_, name_no, name_en, unit in INGREDIENTS:
        run(
            "MERGE (i:Ingredient {id: $id}) ON CREATE SET i.name_no = $no, i.name_en = $en, i.unit = $unit",
            id=id_, no=name_no, en=name_en, unit=unit,
        )
    for food_id, uses in RECIPES.items():
        run(
            """
            MATCH (f:FoodItem {id: $id}) WHERE NOT EXISTS { (f)-[:USES]->() }
            UNWIND $uses AS use
            MATCH (i:Ingredient {id: use[0]})
            CREATE (f)-[:USES {per_portion: use[1]}]->(i)
            """,
            id=food_id, uses=[[ingredient, float(amount)] for ingredient, amount in uses],
        )


def seed_images() -> int:
    """Give each sample dish its approved picture, only while it has no picture at all; returns how many were added."""
    added = 0
    for item in FOOD_ITEMS:
        food_id, source = item[0], os.path.join(SEED_IMAGES, f"{item[0]}.jpg")
        if not os.path.exists(source) or run("MATCH (:FoodItem {id: $id})-[:HAS_IMAGE]->(i:Image) RETURN i.id", id=food_id):
            continue
        with open(source, "rb") as f:
            image_id, path = image_store.save(f.read(), "jpg")
        food_repo.add_image(food_id, image_id, path)
        food_repo.review_image(food_id, image_id, "approved")
        added += 1
    return added


def seed_accounts() -> list[str]:
    """Create the sample staff and customers that don't exist yet; returns the e-mails created."""
    created = []
    for email, name, role, password in SAMPLE_STAFF:
        if staff.create(email, auth.hash_password(password), name, role) is not None:
            created.append(email)
    for email, name, phone, language, password in SAMPLE_CUSTOMERS:
        if customers.create(email, auth.hash_password(password), name, phone, language) is not None:
            created.append(email)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Create constraints and sample data in Neo4j.")
    parser.add_argument("--no-accounts", action="store_true",
                        help="don't create the sample admin, staff and customer accounts (use this on a real server)")
    args = parser.parse_args()
    with create_app().app_context():
        seed()
        pictures = seed_images()
        created = [] if args.no_accounts else seed_accounts()
    print(f"Seeded {len(EVENT_TYPES)} event types, {len(ALLERGENS)} allergens, {len(DIETS)} diets, "
          f"{len(FOOD_ITEMS)} sample food items ({pictures} new pictures) and {len(INGREDIENTS)} sample ingredients.")
    if created:
        print(f"Created sample accounts (passwords in scripts/seed.py): {', '.join(created)}")


if __name__ == "__main__":
    main()
