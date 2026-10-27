"""Image files for food items (US-19): saved in UPLOAD_FOLDER, served at /uploads/<name>.

The :Image node (repositories/food_items.py) stores the URL path; this module stores the bytes. File names are random,
so nothing the admin typed ends up in a path.
"""
import os
import uuid

from flask import current_app

URL_PREFIX = "/uploads/"


def folder() -> str:
    return current_app.config["UPLOAD_FOLDER"]


def save(data: bytes, extension: str) -> tuple[str, str]:
    """Write the file and return (image id, URL path)."""
    image_id = uuid.uuid4().hex
    os.makedirs(folder(), exist_ok=True)
    with open(os.path.join(folder(), f"{image_id}.{extension}"), "wb") as f:
        f.write(data)
    return image_id, f"{URL_PREFIX}{image_id}.{extension}"


def delete(path: str | None) -> None:
    """Remove the file behind a URL path from save(). Paths that aren't ours (e.g. sample data) are left alone."""
    if not path or not path.startswith(URL_PREFIX):
        return
    name = os.path.basename(path)
    try:
        os.remove(os.path.join(folder(), name))
    except FileNotFoundError:
        pass
