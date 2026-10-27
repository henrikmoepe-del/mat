# Plan: upload, preview and approve pictures (A2, US-19)

**Status:** implemented · **Source:** oblig 4 A2 ("upload a picture … the admin previews the result before it is
saved"); US-19; `basic_desc.txt` "Images"

## Goal

The admin uploads one or more pictures per food item and checks them before customers see them. The menu already
shows an item's oldest **approved** `:Image` (`repositories/menu.py`), but nothing could create one.

## Choice: upload, not AI generation

A2 allows either uploading or an AI/image-service prompt. We build upload: it needs no external service, no API key
(the key must never be published, `CLAUDE.md`) and no data leaving the EU/EEA. An AI prompt could later create a
*pending* picture through the same approval step.

## Design (MVC)

- **Model** `models/food_items.py`: `image_error()` / `image_type()`: JPG, PNG or WebP, at most 5 MB, checked by the
  file's first bytes as well as its name (a renamed script is refused).
- **Model** `models/image_store.py`: saves the bytes as `<random id>.<type>` in `UPLOAD_FOLDER` (default
  `backend/uploads/`, in `.gitignore`) and deletes them. Random names: nothing the admin typed ends up in a path.
- **Model** `models/repositories/food_items.py`: `add_image()` (status `pending`, `uploaded_at`), `review_image()`
  (`approved`/`rejected`, `reviewed_at`), `delete_image()`.
- **Controller** `controllers/food_items.py`: `POST /admin/food-items/<id>/images`, `…/images/<image_id>/review`,
  `…/images/<image_id>/delete`; `controllers/menu.py`: `GET /uploads/<name>` serves the files.
- **View** the edit page's "Pictures" section: every picture with its status and Approve / Reject / Delete; the upload
  form shows the chosen file in the browser before it is sent.

## The preview, twice

1. **Before upload:** the browser shows the chosen file (a few lines of JavaScript, no data sent).
2. **Before it is public:** after upload the picture is *pending*; the admin sees it on the edit page and approves it.
   Only then does it appear on the menu.

## Tests

- Unit: accepted and refused files (wrong extension, not a picture, empty, over 5 MB); upload stores a pending image and
  the file; the edit page shows it with Approve/Reject; the file is served; approve → reject → delete removes node and
  file; no path traversal through `/uploads/`.
- Integration: a pending picture isn't on the menu, an approved one is, a rejected one isn't.

## Left out

- Resizing/compressing pictures (would need Pillow); 5 MB limit for now.
- AI-generated pictures (see above).
