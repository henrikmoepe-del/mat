"""Cypher queries for the admin's food items (US-18) and their images (US-19)."""
from ..db import run
from ..food_items import FoodItem, free_id, slug

OPTIONS_QUERY = """
RETURN COLLECT { MATCH (e:EventType) RETURN e {.id, .name_no, .name_en} ORDER BY e.min_guests, e.id } AS event_types,
       COLLECT { MATCH (a:Allergen) RETURN a {.*} ORDER BY a.code } AS allergens,
       COLLECT { MATCH (d:Diet) RETURN d {.*} ORDER BY d.code } AS diets
"""

LIST_QUERY = """
MATCH (f:FoodItem)
RETURN f {
    .id, .name_no, .name_en, .price_nok, .min_order_qty, .published,
    event_types: COLLECT { MATCH (f)-[:SUITS]->(e:EventType) RETURN e {.id, .name_no, .name_en}
                           ORDER BY e.min_guests, e.id },
    approved_images: COUNT { (f)-[:HAS_IMAGE]->(:Image {status: 'approved'}) },
    pending_images: COUNT { (f)-[:HAS_IMAGE]->(:Image {status: 'pending'}) }
} AS item
ORDER BY f.name_no, f.id
"""

GET_QUERY = """
MATCH (f:FoodItem {id: $id})
RETURN f {
    .*,
    event_types: COLLECT { MATCH (f)-[:SUITS]->(e:EventType) RETURN e.id },
    allergens: COLLECT { MATCH (f)-[:CONTAINS_ALLERGEN]->(a:Allergen) RETURN a.code },
    diets: COLLECT { MATCH (f)-[:FITS_DIET]->(d:Diet) RETURN d.code },
    images: COLLECT { MATCH (f)-[:HAS_IMAGE]->(i:Image) RETURN i {.*} ORDER BY i.uploaded_at DESC },
    ordered: EXISTS { (:Order)-[:CONTAINS]->(f) }
} AS item
"""

TAKEN_IDS_QUERY = """
MATCH (f:FoodItem) WHERE f.id = $base OR f.id STARTS WITH $base + '-'
RETURN collect(f.id) AS ids
"""

# Event types, allergens and diets are checked against OPTIONS_QUERY first, so MERGE only finds existing nodes.
LINKS = """
FOREACH (eid IN $event_types | MERGE (e:EventType {id: eid}) MERGE (f)-[:SUITS]->(e))
FOREACH (code IN $allergens | MERGE (a:Allergen {code: code}) MERGE (f)-[:CONTAINS_ALLERGEN]->(a))
FOREACH (code IN $diets | MERGE (d:Diet {code: code}) MERGE (f)-[:FITS_DIET]->(d))
"""

CREATE_QUERY = """
CREATE (f:FoodItem {id: $id})
SET f += $props
""" + LINKS + """
RETURN f.id AS id
"""

# Prices are copied onto each order line when an order is placed, so changing them here leaves orders as they were.
UPDATE_QUERY = """
MATCH (f:FoodItem {id: $id})
SET f += $props
WITH f
OPTIONAL MATCH (f)-[old:SUITS|CONTAINS_ALLERGEN|FITS_DIET]->()
DELETE old
WITH DISTINCT f
""" + LINKS + """
RETURN f.id AS id
"""

SET_PUBLISHED_QUERY = """
MATCH (f:FoodItem {id: $id}) SET f.published = $published RETURN f.id AS id
"""

# Dishes on an order are kept, so the order's history stays readable; the admin unpublishes them instead.
DELETE_QUERY = """
MATCH (f:FoodItem {id: $id}) WHERE NOT EXISTS { (:Order)-[:CONTAINS]->(f) }
OPTIONAL MATCH (f)-[:HAS_IMAGE]->(i:Image)
WITH f, collect(i) AS images, collect(i.path) AS paths
FOREACH (i IN images | DETACH DELETE i)
DETACH DELETE f
RETURN paths
"""

ADD_IMAGE_QUERY = """
MATCH (f:FoodItem {id: $food_id})
CREATE (f)-[:HAS_IMAGE]->(i:Image {id: $image_id, path: $path, status: 'pending', uploaded_at: datetime()})
RETURN i.id AS id
"""

REVIEW_IMAGE_QUERY = """
MATCH (:FoodItem {id: $food_id})-[:HAS_IMAGE]->(i:Image {id: $image_id})
WHERE i.status <> $status
SET i.status = $status, i.reviewed_at = datetime()
RETURN i.id AS id
"""

DELETE_IMAGE_QUERY = """
MATCH (:FoodItem {id: $food_id})-[:HAS_IMAGE]->(i:Image {id: $image_id})
WITH i, i.path AS path
DETACH DELETE i
RETURN path
"""


def options() -> dict:
    """The event types, allergens and diets the admin can choose from."""
    return run(OPTIONS_QUERY)[0]


def list_all() -> list[dict]:
    """Every food item, published or not, with its event types and image counts."""
    return [r["item"] for r in run(LIST_QUERY)]


def get(food_id: str) -> tuple[FoodItem | None, dict]:
    """The item, plus what the edit page shows besides the form: its images and whether it's on an order."""
    rows = run(GET_QUERY, id=food_id)
    if not rows:
        return None, {}
    record = rows[0]["item"]
    return FoodItem.from_record(record), {"images": record["images"], "ordered": record["ordered"]}


def _links(item: FoodItem) -> dict:
    return {"event_types": item.event_types, "allergens": item.allergens, "diets": item.diets}


def create(item: FoodItem) -> str:
    """Store a new item and return its id, made from the English name (like the sample dishes' ids)."""
    base = slug(item.name_en or item.name_no)
    taken = set(run(TAKEN_IDS_QUERY, base=base)[0]["ids"])
    food_id = free_id(base, taken)
    run(CREATE_QUERY, id=food_id, props=item.properties(), **_links(item))
    return food_id


def update(food_id: str, item: FoodItem) -> bool:
    return bool(run(UPDATE_QUERY, id=food_id, props=item.properties(), **_links(item)))


def set_published(food_id: str, published: bool) -> bool:
    return bool(run(SET_PUBLISHED_QUERY, id=food_id, published=published))


def delete(food_id: str) -> list[str] | None:
    """Delete the item and its images; returns the image paths so their files can be removed. None if the item is
    gone or is on an order."""
    rows = run(DELETE_QUERY, id=food_id)
    return rows[0]["paths"] if rows else None


def add_image(food_id: str, image_id: str, path: str) -> bool:
    """A new image starts as pending: it's shown on the menu only after the admin approves it."""
    return bool(run(ADD_IMAGE_QUERY, food_id=food_id, image_id=image_id, path=path))


def review_image(food_id: str, image_id: str, status: str) -> bool:
    return bool(run(REVIEW_IMAGE_QUERY, food_id=food_id, image_id=image_id, status=status))


def delete_image(food_id: str, image_id: str) -> str | None:
    rows = run(DELETE_IMAGE_QUERY, food_id=food_id, image_id=image_id)
    return rows[0]["path"] if rows else None
