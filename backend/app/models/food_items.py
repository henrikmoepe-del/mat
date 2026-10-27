"""Food items (US-18) and their images (US-19): the domain class and its rules.

`FoodItem` is what the admin edits. `parse_form()` turns the admin form into one and lists what's wrong, in the same
(key, args) format as orders.parse_checkout(). Storage is in repositories/food_items.py, image files in image_store.py.
"""
import re
import unicodedata
from dataclasses import asdict, dataclass, field

from werkzeug.datastructures import MultiDict

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_PRICE_NOK = 100_000
MAX_MIN_ORDER_QTY = 9999  # same sanity limit as the cart (cart.MAX_QUANTITY)

IMAGE_STATUSES = ("pending", "approved", "rejected")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# File signatures ("magic bytes"), so a renamed file that isn't a picture is refused whatever its name says.
IMAGE_SIGNATURES = (
    ("jpg", lambda head: head.startswith(b"\xff\xd8\xff")),
    ("png", lambda head: head.startswith(b"\x89PNG\r\n\x1a\n")),
    ("webp", lambda head: head[:4] == b"RIFF" and head[8:12] == b"WEBP"),
)
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

TEXT_FIELDS = ("name_no", "name_en", "description_no", "description_en")


@dataclass
class FoodItem:
    """A dish on the menu. Text in Norwegian and English; prices in whole NOK per portion."""
    name_no: str
    name_en: str
    description_no: str
    description_en: str
    price_nok: int
    min_order_qty: int
    published: bool = False
    event_types: list[str] = field(default_factory=list)  # :EventType ids (SUITS)
    allergens: list[str] = field(default_factory=list)  # :Allergen codes (CONTAINS_ALLERGEN)
    diets: list[str] = field(default_factory=list)  # :Diet codes (FITS_DIET)
    id: str | None = None

    @classmethod
    def from_record(cls, record: dict) -> "FoodItem":
        return cls(**{name: record[name] for name in cls.__dataclass_fields__ if name in record})

    def properties(self) -> dict:
        """The node's own properties; the id and the relationships are stored separately."""
        data = asdict(self)
        for name in ("id", "event_types", "allergens", "diets"):
            del data[name]
        return data

    def as_form(self) -> MultiDict:
        """The values for the edit form, in the same shape as a submitted form."""
        form = MultiDict({name: getattr(self, name) for name in TEXT_FIELDS})
        form["price_nok"] = str(self.price_nok)
        form["min_order_qty"] = str(self.min_order_qty)
        if self.published:
            form["published"] = "1"
        for name in ("event_types", "allergens", "diets"):
            form.setlist(name, list(getattr(self, name)))
        return form


def _parse_int(value, lowest: int, highest: int) -> int | None:
    try:
        number = int(str(value).strip())
    except ValueError:
        return None
    return number if lowest <= number <= highest else None


def parse_form(form, event_type_ids: set[str], allergen_codes: set[str],
               diet_codes: set[str]) -> tuple[FoodItem, list[tuple[str, dict]]]:
    """Read the admin's food item form (US-18). Unknown event types, allergens and diets are ignored."""
    errors = []
    text = {name: form.get(name, "").strip() for name in TEXT_FIELDS}
    if not text["name_no"] or not text["name_en"]:
        errors.append(("food_name_required", {}))
    if any(len(text[name]) > MAX_NAME_LENGTH for name in ("name_no", "name_en")):
        errors.append(("text_too_long", {"max": MAX_NAME_LENGTH}))
    if any(len(text[name]) > MAX_DESCRIPTION_LENGTH for name in ("description_no", "description_en")):
        errors.append(("text_too_long", {"max": MAX_DESCRIPTION_LENGTH}))
    price = _parse_int(form.get("price_nok", ""), 0, MAX_PRICE_NOK)
    if price is None:
        errors.append(("food_price_invalid", {"max": MAX_PRICE_NOK}))
    min_qty = _parse_int(form.get("min_order_qty", ""), 1, MAX_MIN_ORDER_QTY)
    if min_qty is None:
        errors.append(("food_min_qty_invalid", {"max": MAX_MIN_ORDER_QTY}))
    event_types = [e for e in form.getlist("event_types") if e in event_type_ids]
    if not event_types:
        errors.append(("food_event_type_required", {}))
    item = FoodItem(**text, price_nok=price or 0, min_order_qty=min_qty or 1,
                    published=form.get("published") == "1", event_types=event_types,
                    allergens=[a for a in form.getlist("allergens") if a in allergen_codes],
                    diets=[d for d in form.getlist("diets") if d in diet_codes])
    return item, errors


def slug(text: str) -> str:
    """A readable id from a name: "Bløtkake med bær" -> "blotkake-med-baer"."""
    text = text.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60].strip("-") or "dish"


def free_id(base: str, taken: set[str]) -> str:
    """`base`, or `base-2`, `base-3`, … if that's taken."""
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def image_type(filename: str, head: bytes) -> str | None:
    """The image's file type ("jpg", "png", "webp") if the name and the content both say it's a picture we accept."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in IMAGE_EXTENSIONS:
        return None
    return next((kind for kind, matches in IMAGE_SIGNATURES if matches(head)), None)


def image_error(filename: str, data: bytes) -> str | None:
    """Why an uploaded file can't be used as a food picture, or None."""
    if not filename or not data:
        return "image_required"
    if len(data) > MAX_IMAGE_BYTES:
        return "image_too_large"
    if image_type(filename, data[:16]) is None:
        return "image_wrong_type"
    return None
