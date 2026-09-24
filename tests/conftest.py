import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

# Configure the app for an isolated SQLite database *before* it is imported.
_TMP_DIR = tempfile.mkdtemp(prefix="campus-hub-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP_DIR, "test.db").replace("\\", "/")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["OPENROUTESERVICE_API_KEY"] = ""  # never call the real geocoding API from tests

import app as campus_app  # noqa: E402
import seed as campus_seed  # noqa: E402

campus_app.app.config.update(
    TESTING=True,
    UPLOAD_FOLDER=_TMP_DIR,
    ITEM_UPLOAD_FOLDER=_TMP_DIR,
)

# Seeded accounts use a cheap hash in tests so logging in stays fast.
_FAST_DEMO_HASH = generate_password_hash(campus_seed.DEMO_PASSWORD, method="pbkdf2:sha256:1000")
campus_seed.generate_password_hash = lambda password, method=None: _FAST_DEMO_HASH


@pytest.fixture()
def app():
    with campus_app.app.app_context():
        campus_app.db.drop_all()
        campus_app.initialize_database()
        yield campus_app.app
        campus_app.db.session.remove()


@pytest.fixture()
def seeded(app):
    campus_seed.seed()
    return app


def login(client, email, password=campus_seed.DEMO_PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


@pytest.fixture()
def demo_client(seeded):
    client = seeded.test_client()
    login(client, "demo@campushub.test")
    return client


@pytest.fixture()
def other_client(seeded):
    client = seeded.test_client()
    login(client, "maliha@campushub.test")
    return client
