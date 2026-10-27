import io
import re

import pytest
from werkzeug.datastructures import MultiDict

from app.models import food_items
from app.models.food_items import FoodItem
from app.models.repositories import food_items as food_repo
from tests.conftest import log_in_staff

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
OPTIONS = {
    "event_types": [{"id": "wedding", "name_no": "Bryllup", "name_en": "Wedding"},
                    {"id": "birthday", "name_no": "Bursdag", "name_en": "Birthday"}],
    "allergens": [{"code": "milk", "name_no": "Melk", "name_en": "Milk"}],
    "diets": [{"code": "vegetarian", "name_no": "Vegetar", "name_en": "Vegetarian"}],
}


def valid_form(**changes):
    form = MultiDict({"name_no": "Bløtkake", "name_en": "Layer cake", "description_no": "Med bær",
                      "description_en": "With berries", "price_nok": "85", "min_order_qty": "10", "published": "1"})
    form.setlist("event_types", ["wedding", "unknown"])
    form.setlist("allergens", ["milk", "peanut"])
    form.setlist("diets", ["vegetarian"])
    for key, value in changes.items():
        form.setlist(key, value if isinstance(value, list) else [value])
    return form


def parse(form):
    return food_items.parse_form(form, {"wedding", "birthday"}, {"milk"}, {"vegetarian"})


# --- rules (US-18, US-19) --------------------------------------------------------

def test_parse_form_builds_a_food_item_and_ignores_unknown_choices():
    item, errors = parse(valid_form())
    assert errors == []
    assert item == FoodItem("Bløtkake", "Layer cake", "Med bær", "With berries", 85, 10, True,
                            ["wedding"], ["milk"], ["vegetarian"])
    assert item.properties() == {"name_no": "Bløtkake", "name_en": "Layer cake", "description_no": "Med bær",
                                 "description_en": "With berries", "price_nok": 85, "min_order_qty": 10,
                                 "published": True}


@pytest.mark.parametrize("changes,error", [
    ({"name_en": " "}, "food_name_required"),
    ({"name_no": "x" * 101}, "text_too_long"),
    ({"description_en": "x" * 501}, "text_too_long"),
    ({"price_nok": "-1"}, "food_price_invalid"),
    ({"price_nok": "12.50"}, "food_price_invalid"),
    ({"price_nok": "100001"}, "food_price_invalid"),
    ({"min_order_qty": "0"}, "food_min_qty_invalid"),
    ({"event_types": ["unknown"]}, "food_event_type_required"),
])
def test_parse_form_errors(changes, error):
    _, errors = parse(valid_form(**changes))
    assert [key for key, _ in errors] == [error]


def test_unticked_published_means_hidden():
    form = valid_form()
    del form["published"]
    item, _ = parse(form)
    assert item.published is False


def test_as_form_round_trips():
    item, _ = parse(valid_form())
    again, errors = parse(item.as_form())
    assert (again, errors) == (item, [])


@pytest.mark.parametrize("name,expected", [
    ("Layer cake", "layer-cake"),
    ("Bløtkake med bær & krem", "blotkake-med-baer-krem"),
    ("Pâté", "pate"),
    ("!!!", "dish"),
])
def test_slug(name, expected):
    assert food_items.slug(name) == expected


def test_free_id():
    assert food_items.free_id("cake", set()) == "cake"
    assert food_items.free_id("cake", {"cake", "cake-2"}) == "cake-3"


@pytest.mark.parametrize("filename,data,error", [
    ("cake.png", PNG, None),
    ("cake.JPEG", JPEG, None),
    ("cake.webp", b"RIFF\x00\x00\x00\x00WEBPVP8 ", None),
    ("", PNG, "image_required"),
    ("cake.png", b"", "image_required"),
    ("cake.gif", PNG, "image_wrong_type"),  # extension we don't accept
    ("cake.png", b"<script>alert(1)</script>", "image_wrong_type"),  # not a picture, whatever the name says
])
def test_image_error(filename, data, error):
    assert food_items.image_error(filename, data) == error


def test_image_too_large():
    assert food_items.image_error("cake.png", PNG + b"\x00" * food_items.MAX_IMAGE_BYTES) == "image_too_large"


def test_image_type_comes_from_the_content():
    assert food_items.image_type("photo.png", JPEG[:16]) == "jpg"


# --- fake database -------------------------------------------------------------

class FoodStore:
    """Fake Neo4j for the food item pages: one item, its images and whether it's on an order."""

    def __init__(self):
        self.item = {"id": "layer-cake", "name_no": "Bløtkake", "name_en": "Layer cake", "description_no": "",
                     "description_en": "", "price_nok": 85, "min_order_qty": 10, "published": True,
                     "event_types": ["wedding"], "allergens": ["milk"], "diets": []}
        self.images = []
        self.ordered = False
        self.created = None
        self.updated = None
        self.deleted = False

    def __call__(self, query, params):
        if query == food_repo.OPTIONS_QUERY:
            return [OPTIONS]
        if query == food_repo.LIST_QUERY:
            return [{"item": {**self.item, "event_types": OPTIONS["event_types"][:1], "approved_images": 0,
                              "pending_images": len(self.images)}}]
        if query == food_repo.GET_QUERY:
            if self.deleted or params["id"] != self.item["id"]:
                return []
            return [{"item": {**self.item, "images": self.images, "ordered": self.ordered}}]
        if query == food_repo.TAKEN_IDS_QUERY:
            return [{"ids": [self.item["id"]]}]
        if query == food_repo.CREATE_QUERY:
            self.created = params
            return [{"id": params["id"]}]
        if query == food_repo.UPDATE_QUERY:
            self.updated = params
            return [{"id": params["id"]}] if params["id"] == self.item["id"] else []
        if query == food_repo.SET_PUBLISHED_QUERY:
            self.item["published"] = params["published"]
            return [{"id": params["id"]}]
        if query == food_repo.DELETE_QUERY:
            if self.ordered:
                return []
            self.deleted = True
            return [{"paths": [i["path"] for i in self.images]}]
        if query == food_repo.ADD_IMAGE_QUERY:
            self.images.append({"id": params["image_id"], "path": params["path"], "status": "pending",
                                "uploaded_at": None})
            return [{"id": params["image_id"]}]
        if query == food_repo.REVIEW_IMAGE_QUERY:
            for image in self.images:
                if image["id"] == params["image_id"]:
                    image["status"] = params["status"]
                    return [{"id": image["id"]}]
            return []
        if query == food_repo.DELETE_IMAGE_QUERY:
            for image in self.images:
                if image["id"] == params["image_id"]:
                    self.images.remove(image)
                    return [{"path": image["path"]}]
            return []
        return []


@pytest.fixture
def uploads(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def store(client, driver, uploads):
    client.application.config["UPLOAD_FOLDER"] = str(uploads)
    store = FoodStore()
    log_in_staff(client, driver, fallback=store)
    return store


def flashes(client):
    with client.session_transaction() as s:
        return [message for _, message in s.get("_flashes", [])]


# --- access ---------------------------------------------------------------------

def test_food_item_pages_are_for_admins_only(client, driver):
    assert client.get("/admin/food-items").status_code == 302  # to the staff login
    log_in_staff(client, driver, "kitchen")
    assert client.get("/admin/food-items").status_code == 403
    assert client.post("/admin/food-items/new", data=valid_form()).status_code == 403


# --- pages (US-18) -----------------------------------------------------------------

def test_list_shows_published_and_hidden_items(client, store):
    html = client.get("/admin/food-items").get_data(as_text=True)
    assert "Bløtkake" in html and "Publisert" in html and "Bryllup" in html
    assert 'href="/admin/food-items/new"' in html


def test_admin_nav_links_to_food_items(client, store):
    assert 'href="/admin/food-items"' in client.get("/admin/orders").get_data(as_text=True)


def test_new_item_form(client, store):
    html = client.get("/admin/food-items/new").get_data(as_text=True)
    assert 'name="name_no"' in html and 'value="wedding"' in html and 'value="milk"' in html
    assert 'name="image"' not in html  # pictures are added once the item exists


def test_create_item(client, store):
    res = client.post("/admin/food-items/new", data=valid_form(name_en="Layer cake"))
    assert res.status_code == 302
    assert res.headers["Location"] == "/admin/food-items/layer-cake-2#images"  # "layer-cake" is taken
    assert store.created["props"]["price_nok"] == 85
    assert store.created["event_types"] == ["wedding"] and store.created["allergens"] == ["milk"]


def test_invalid_item_is_shown_again_with_errors(client, store):
    res = client.post("/admin/food-items/new", data=valid_form(price_nok="abc"))
    assert res.status_code == 400
    html = res.get_data(as_text=True)
    assert "Prisen må være et helt tall" in html
    assert 'value="Bløtkake"' in html  # what the admin typed is kept
    assert store.created is None


def test_edit_form_is_filled_in(client, store):
    html = client.get("/admin/food-items/layer-cake").get_data(as_text=True)
    assert 'value="Bløtkake"' in html and 'value="85"' in html
    assert re.search(r'value="wedding"\s+checked', html) and not re.search(r'value="birthday"\s+checked', html)
    assert 'name="image"' in html


def test_update_item(client, store):
    res = client.post("/admin/food-items/layer-cake", data=valid_form(price_nok="95"))
    assert res.status_code == 302 and res.headers["Location"] == "/admin/food-items"
    assert store.updated["id"] == "layer-cake" and store.updated["props"]["price_nok"] == 95


def test_unknown_item_is_404(client, store):
    assert client.get("/admin/food-items/nope").status_code == 404
    assert client.post("/admin/food-items/nope", data=valid_form()).status_code == 404


def test_publish_and_hide(client, store):
    client.post("/admin/food-items/layer-cake/published", data={"published": "0"})
    assert store.item["published"] is False
    res = client.post("/admin/food-items/layer-cake/published", data={"published": "1", "back": "edit"})
    assert store.item["published"] is True
    assert res.headers["Location"] == "/admin/food-items/layer-cake"


def test_delete_needs_the_confirmation_tick(client, store):
    client.post("/admin/food-items/layer-cake/delete")
    assert not store.deleted
    assert "Kryss av" in flashes(client)[0]


def test_delete_removes_the_item_and_its_picture_files(client, store, uploads):
    client.post("/admin/food-items/layer-cake/images", data={"image": (io.BytesIO(PNG), "cake.png")},
                content_type="multipart/form-data")
    assert len(list(uploads.iterdir())) == 1
    res = client.post("/admin/food-items/layer-cake/delete", data={"confirm": "yes"})
    assert res.headers["Location"] == "/admin/food-items"
    assert store.deleted and list(uploads.iterdir()) == []


def test_item_on_an_order_cannot_be_deleted(client, store):
    store.ordered = True
    html = client.get("/admin/food-items/layer-cake").get_data(as_text=True)
    assert "kan ikke slettes" in html and 'name="confirm"' not in html
    client.post("/admin/food-items/layer-cake/delete", data={"confirm": "yes"})
    assert not store.deleted


# --- pictures (US-19) ----------------------------------------------------------------

def upload(client, data=PNG, name="cake.png"):
    return client.post("/admin/food-items/layer-cake/images", data={"image": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def test_upload_saves_a_pending_picture(client, store, uploads):
    res = upload(client)
    assert res.headers["Location"] == "/admin/food-items/layer-cake#images"
    [image] = store.images
    assert image["status"] == "pending"
    [saved] = list(uploads.iterdir())
    assert saved.suffix == ".png" and saved.read_bytes() == PNG
    assert image["path"] == f"/uploads/{saved.name}"


def test_pending_picture_is_previewed_with_approve_and_reject(client, store):
    upload(client)
    html = client.get("/admin/food-items/layer-cake").get_data(as_text=True)
    assert store.images[0]["path"] in html
    assert "Venter på godkjenning" in html and "Godkjenn" in html and "Avvis" in html


def test_uploaded_picture_is_served(client, store):
    upload(client)
    res = client.get(store.images[0]["path"])
    assert res.status_code == 200 and res.data == PNG


def test_upload_refuses_files_that_are_not_pictures(client, store, uploads):
    upload(client, b"MZ\x90\x00 not a picture", "cake.png")
    assert store.images == [] and not uploads.exists()
    assert "JPG-, PNG-" in flashes(client)[0]


def test_approve_reject_and_delete_picture(client, store, uploads):
    upload(client)
    image_id = store.images[0]["id"]
    client.post(f"/admin/food-items/layer-cake/images/{image_id}/review", data={"status": "approved"})
    assert store.images[0]["status"] == "approved"
    client.post(f"/admin/food-items/layer-cake/images/{image_id}/review", data={"status": "rejected"})
    assert store.images[0]["status"] == "rejected"
    assert client.post(f"/admin/food-items/layer-cake/images/{image_id}/review",
                       data={"status": "published"}).status_code == 400
    client.post(f"/admin/food-items/layer-cake/images/{image_id}/delete")
    assert store.images == [] and list(uploads.iterdir()) == []


def test_uploads_cannot_escape_the_upload_folder(client, store):
    assert client.get("/uploads/..%2Fapp%2Fconfig.py").status_code == 404
