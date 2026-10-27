from neo4j.exceptions import ConstraintError

from app import create_app
from scripts import seed
from tests.conftest import FakeDriver


def test_seed_accounts_creates_admin_staff_and_customers_once():
    driver = FakeDriver()
    created = []

    def handler(query, params):
        if "CREATE (s:Staff" in query or "CREATE (c:Customer" in query:
            if params["email"] == "admin@ektemat.test":
                raise ConstraintError("already exists")  # unique e-mail constraint
            assert "password" not in params and params["hash"].startswith("scrypt:")  # only the hash is stored
            created.append((params["email"], params.get("role")))
            return [{"s": params, "c": params}]
        return []
    driver.handler = handler
    with create_app({"TESTING": True, "NEO4J_DRIVER": driver}).app_context():
        emails = seed.seed_accounts()
    assert "admin@ektemat.test" not in emails  # already there: left as it is
    assert ("kjokken@ektemat.test", "kitchen") in created and ("sjafor@ektemat.test", "driver") in created
    assert {"kari@kunde.test", "alex@customer.test"} <= set(emails)


def test_sample_accounts_include_an_admin():
    assert any(role == "admin" for _, _, role, _ in seed.SAMPLE_STAFF)
    assert len(seed.SAMPLE_CUSTOMERS) >= 2
