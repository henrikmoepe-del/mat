"""Ekte Mat backend: Flask app factory.

Model-View-Controller: models/ holds the domain rules and all data access (Neo4j), views/ the Jinja templates and
controllers/ the Flask blueprints (HTML pages, and the JSON API in controllers/api/)."""
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from . import auth, cli, i18n
from .config import Config
from .controllers.account import bp as account_page_bp
from .controllers.admin import bp as admin_page_bp
from .controllers.cart import bp as cart_page_bp
from .controllers.food_items import bp as food_items_page_bp
from .controllers.kitchen import driver_bp as driver_page_bp
from .controllers.kitchen import kitchen_bp as kitchen_page_bp
from .controllers.menu import bp as menu_page_bp
from .controllers.orders import bp as orders_page_bp
from .controllers.outbox import bp as outbox_page_bp
from .controllers.api.event_types import bp as event_types_bp
from .controllers.api.health import bp as health_bp
from .models import cart, db


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="views")
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)
    i18n.init_app(app)
    auth.init_app(app)
    cli.init_app(app)
    app.register_blueprint(menu_page_bp)
    app.register_blueprint(cart_page_bp)
    app.register_blueprint(account_page_bp)
    app.register_blueprint(orders_page_bp)
    app.register_blueprint(admin_page_bp)
    app.register_blueprint(food_items_page_bp)
    app.register_blueprint(kitchen_page_bp)
    app.register_blueprint(driver_page_bp)
    if app.config["DEV_OUTBOX"]:
        app.register_blueprint(outbox_page_bp)
    app.context_processor(lambda: {"cart_count": cart.item_count()})

    # Every form must send csrf_token(). JSON calls that change data use the admin's session cookie, so they must
    # send the token too, in an X-CSRFToken header.
    CSRFProtect(app)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(event_types_bp, url_prefix="/api/event-types")
    return app
