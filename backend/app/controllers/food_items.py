"""Admin pages for food items (US-18) and their images (US-19). Staff with role "admin" only."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from werkzeug.datastructures import MultiDict

from ..auth import staff_required
from ..i18n import t
from ..models import food_items, image_store
from ..models.repositories import food_items as food_repo

bp = Blueprint("food_items", __name__, url_prefix="/admin/food-items")
admin_only = staff_required("admin")


@bp.get("")
@admin_only
def item_list():
    return render_template("admin_food_items.html", items=food_repo.list_all())


def _parse(form):
    choices = food_repo.options()
    item, errors = food_items.parse_form(
        form, {e["id"] for e in choices["event_types"]}, {a["code"] for a in choices["allergens"]},
        {d["code"] for d in choices["diets"]})
    return item, errors, choices


def _render_form(values, choices, errors=(), food_id=None, extra=None, status=200):
    return render_template("admin_food_item.html", values=values, choices=choices, errors=errors, food_id=food_id,
                           images=(extra or {}).get("images", []), ordered=(extra or {}).get("ordered", False),
                           limits=food_items), status


@bp.route("/new", methods=["GET", "POST"])
@admin_only
def new():
    if request.method == "GET":
        return _render_form(MultiDict({"min_order_qty": "1"}), food_repo.options())
    item, errors, choices = _parse(request.form)
    if errors:
        return _render_form(request.form, choices, errors, status=400)
    food_id = food_repo.create(item)
    flash(t("food_created", name=item.name_no), "success")
    # Straight to the edit page, where the pictures are added.
    return redirect(url_for("food_items.edit", food_id=food_id, _anchor="images"))


@bp.route("/<food_id>", methods=["GET", "POST"])
@admin_only
def edit(food_id: str):
    current, extra = food_repo.get(food_id)
    if current is None:
        abort(404)
    if request.method == "GET":
        return _render_form(current.as_form(), food_repo.options(), food_id=food_id, extra=extra)
    item, errors, choices = _parse(request.form)
    if errors:
        return _render_form(request.form, choices, errors, food_id=food_id, extra=extra, status=400)
    if not food_repo.update(food_id, item):
        abort(404)
    flash(t("food_saved", name=item.name_no), "success")
    return redirect(url_for("food_items.item_list"))


@bp.post("/<food_id>/published")
@admin_only
def set_published(food_id: str):
    published = request.form.get("published") == "1"
    if not food_repo.set_published(food_id, published):
        abort(404)
    flash(t("food_published" if published else "food_unpublished"), "success")
    if request.form.get("back") == "edit":
        return redirect(url_for("food_items.edit", food_id=food_id))
    return redirect(url_for("food_items.item_list"))


@bp.post("/<food_id>/delete")
@admin_only
def delete(food_id: str):
    current, extra = food_repo.get(food_id)
    if current is None:
        abort(404)
    if request.form.get("confirm") != "yes":
        flash(t("food_delete_confirm_missing"), "error")
        return redirect(url_for("food_items.edit", food_id=food_id))
    paths = None if extra["ordered"] else food_repo.delete(food_id)
    if paths is None:
        flash(t("food_on_orders"), "error")
        return redirect(url_for("food_items.edit", food_id=food_id))
    for path in paths:
        image_store.delete(path)
    flash(t("food_deleted", name=current.name_no), "success")
    return redirect(url_for("food_items.item_list"))


@bp.post("/<food_id>/images")
@admin_only
def upload_image(food_id: str):
    """US-19: the new picture is saved as pending; the admin sees it on the edit page and approves it there."""
    upload = request.files.get("image")
    data = upload.read(food_items.MAX_IMAGE_BYTES + 1) if upload else b""
    error = food_items.image_error(upload.filename if upload else "", data)
    if error:
        flash(t(error, mb=food_items.MAX_IMAGE_BYTES // (1024 * 1024)), "error")
        return redirect(url_for("food_items.edit", food_id=food_id, _anchor="images"))
    image_id, path = image_store.save(data, food_items.image_type(upload.filename, data[:16]))
    if not food_repo.add_image(food_id, image_id, path):
        image_store.delete(path)
        abort(404)
    flash(t("image_uploaded"), "success")
    return redirect(url_for("food_items.edit", food_id=food_id, _anchor="images"))


@bp.post("/<food_id>/images/<image_id>/review")
@admin_only
def review_image(food_id: str, image_id: str):
    status = request.form.get("status", "")
    if status not in ("approved", "rejected"):
        abort(400)
    if food_repo.review_image(food_id, image_id, status):
        flash(t("image_" + status), "success")
    return redirect(url_for("food_items.edit", food_id=food_id, _anchor="images"))


@bp.post("/<food_id>/images/<image_id>/delete")
@admin_only
def delete_image(food_id: str, image_id: str):
    path = food_repo.delete_image(food_id, image_id)
    if path is None:
        abort(404)
    image_store.delete(path)
    flash(t("image_deleted"), "success")
    return redirect(url_for("food_items.edit", food_id=food_id, _anchor="images"))
