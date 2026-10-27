"""HTML pages for the public menu (US-01), its pictures (US-19) and language switch (US-02)."""
from flask import Blueprint, current_app, redirect, render_template, request, send_from_directory, session
from flask_login import current_user

from ..i18n import LANGUAGES
from ..models.repositories import customers, menu
from ..urls import safe_next

bp = Blueprint("menu", __name__)


@bp.get("/")
def index():
    return render_template("menu.html", event_types=menu.menu_by_event_type())


@bp.post("/language/<lang>")
def set_language(lang: str):
    if lang in LANGUAGES:
        session["lang"] = lang
        if current_user.is_authenticated and not current_user.is_staff:
            customers.set_language(current_user.email, lang)  # US-02: saved on the account
    return redirect(safe_next(request.form.get("next")))


@bp.get("/uploads/<name>")
def upload(name: str):
    """Food pictures uploaded by the admin (models/image_store.py). Names are random, so pending pictures can only be
    seen by someone who was shown the link: the admin."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name, max_age=7 * 24 * 3600)
