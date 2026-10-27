# Plan: seed script creates an admin and test customers

**Status:** implemented · **Source:** oblig 4 "Running it: a seed script creates sample food items, an admin and test
customers"

## Goal

After `python -m scripts.seed` the app can be tried at once: log in as admin, kitchen, driver or customer. Before, staff
had to be created by hand with `flask create-staff` and there were no customers.

## Design

- `SAMPLE_STAFF` (admin, kitchen, driver) and `SAMPLE_CUSTOMERS` (one Norwegian-speaking, one English-speaking) in
  `scripts/seed.py`, with `.test` e-mail addresses and test passwords. Synthetic data only.
- Created through the existing `repositories/staff.create()` and `customers.create()`, so passwords are hashed the same
  way as everywhere else. An account that already exists is skipped (unique e-mail constraint), never overwritten.
- `--no-accounts` skips them, for a real server, where staff are created with `flask create-staff`.
- `backend/README.md` lists the accounts; the passwords are in `scripts/seed.py`.

## Tests

`tests/test_seed.py`: creates the missing accounts, skips an existing one, stores only password hashes.
