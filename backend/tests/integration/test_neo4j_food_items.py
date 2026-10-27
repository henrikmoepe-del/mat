"""Runs the food item and image Cypher (US-18, US-19) against a local Neo4j. Opt-in, because it writes sample data:

    RUN_NEO4J_TESTS=1 .venv/bin/python -m pytest tests/integration
"""
import os

import pytest

from app import create_app
from app.models.db import run
from app.models.food_items import FoodItem
from app.models.repositories import food_items as food_repo
from app.models.repositories.menu import menu_by_event_type
from scripts.seed import seed

pytestmark = pytest.mark.skipif(os.getenv("RUN_NEO4J_TESTS") != "1", reason="set RUN_NEO4J_TESTS=1 to run")


def cleanup():
    run("MATCH (f:FoodItem) WHERE f.id STARTS WITH 'it-test-dish' "
        "OPTIONAL MATCH (f)-[:HAS_IMAGE]->(i:Image) DETACH DELETE f, i")


@pytest.fixture
def app_ctx():
    app = create_app()
    with app.app_context():
        seed()
        cleanup()
        yield app
        cleanup()


def dish(**changes):
    values = dict(name_no="IT-test-dish", name_en="IT test dish", description_no="Test", description_en="Test",
                  price_nok=100, min_order_qty=5, published=False, event_types=["birthday"], allergens=["milk"],
                  diets=[])
    values.update(changes)
    return FoodItem(**values)


def menu_ids(event_type: str) -> set[str]:
    return {i["id"] for e in menu_by_event_type() if e["id"] == event_type for i in e["items"]}


def test_options_come_from_the_seeded_lists(app_ctx):
    options = food_repo.options()
    assert {"wedding", "birthday"} <= {e["id"] for e in options["event_types"]}
    assert "milk" in {a["code"] for a in options["allergens"]}
    assert "vegan" in {d["code"] for d in options["diets"]}


def test_create_update_publish_and_delete(app_ctx):
    food_id = food_repo.create(dish())
    assert food_id == "it-test-dish"
    assert food_repo.create(dish()) == "it-test-dish-2"  # the id stays unique

    item, extra = food_repo.get(food_id)
    assert item == dish(id=food_id)
    assert extra == {"images": [], "ordered": False}
    assert food_id not in menu_ids("birthday")  # not published yet

    assert food_repo.update(food_id, dish(price_nok=120, published=True, event_types=["wedding"], allergens=[],
                                          diets=["vegan"]))
    item, _ = food_repo.get(food_id)
    assert (item.price_nok, item.event_types, item.allergens, item.diets) == (120, ["wedding"], [], ["vegan"])
    assert food_id in menu_ids("wedding") and food_id not in menu_ids("birthday")

    assert food_repo.set_published(food_id, False)
    assert food_id not in menu_ids("wedding")
    listed = next(i for i in food_repo.list_all() if i["id"] == food_id)
    assert listed["published"] is False and listed["pending_images"] == 0

    assert food_repo.delete(food_id) == []
    assert food_repo.get(food_id) == (None, {})


def test_images_are_shown_only_after_approval(app_ctx):
    food_id = food_repo.create(dish(published=True))
    assert food_repo.add_image(food_id, "it-test-image", "/uploads/it-test-image.png")
    menu_item = lambda: next(i for e in menu_by_event_type() if e["id"] == "birthday"  # noqa: E731
                             for i in e["items"] if i["id"] == food_id)
    assert menu_item()["image"] is None  # pending

    assert food_repo.review_image(food_id, "it-test-image", "approved")
    assert menu_item()["image"] == "/uploads/it-test-image.png"
    assert not food_repo.review_image(food_id, "it-test-image", "approved")  # no change

    assert food_repo.review_image(food_id, "it-test-image", "rejected")
    assert menu_item()["image"] is None

    assert food_repo.delete_image(food_id, "it-test-image") == "/uploads/it-test-image.png"
    _, extra = food_repo.get(food_id)
    assert extra["images"] == []


def test_dish_on_an_order_is_not_deleted(app_ctx):
    food_id = food_repo.create(dish())
    run("MATCH (f:FoodItem {id: $id}) CREATE (:Order {id: 'IT-TEST-ORDER'})-[:CONTAINS {quantity: 5}]->(f)",
        id=food_id)
    try:
        assert food_repo.get(food_id)[1]["ordered"] is True
        assert food_repo.delete(food_id) is None
        assert food_repo.get(food_id)[0] is not None
    finally:
        run("MATCH (o:Order {id: 'IT-TEST-ORDER'}) DETACH DELETE o")
