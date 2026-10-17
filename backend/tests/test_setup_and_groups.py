"""First-run setup (token, steps, the API guard) and group rules. Test database."""
import pytest
from sqlalchemy import select

from app.core import groups, setup as setup_state
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import verify_password
from app.main import app
from app.models.access import AppSetting
from app.models.user import User

PW = "correct horse battery"


@pytest.fixture
def setup_on(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SETUP_ENABLED", True)
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    (tmp_path / "storage").mkdir()
    setup_state._required = True
    yield tmp_path
    setup_state._required = False


async def admin_user(db):
    return (await db.execute(select(User).where(User.username == "admin"))).scalar_one()


async def test_bootstrap_creates_the_admin_once_and_rotates_the_token(db, setup_on):
    first = await setup_state.bootstrap(db)
    second = await setup_state.bootstrap(db)
    assert first and second and first != second
    admin = await admin_user(db)
    assert admin.is_superuser is True
    assert await groups.is_member(db, admin.id, groups.ADMIN) and await groups.is_member(db, admin.id, groups.USER)
    assert not verify_password(PW, admin.hashed_password)  # no usable password until step one
    assert len((await db.execute(select(User).where(User.username == "admin"))).scalars().all()) == 1


async def test_the_token_is_stored_only_as_a_hash(db, setup_on):
    token = await setup_state.bootstrap(db)
    stored = (await db.get(AppSetting, setup_state.TOKEN_KEY)).value
    assert token not in str(stored) and len(stored["hash"]) == 64


async def test_the_guard_holds_the_api_closed_until_setup_is_done(client, db, setup_on):
    await setup_state.bootstrap(db)
    r = client.get("/api/v2/sources/installed")
    assert r.status_code == 503 and r.json()["setup_required"] is True and r.json()["setup_url"] == "/setup"
    assert client.get("/api/v2/setup/status").json()["required"] is True
    assert client.get("/api/v1/health").status_code != 503


async def test_wrong_token_and_wrong_step_are_refused(client, db, setup_on):
    token = await setup_state.bootstrap(db)
    bad = client.post("/api/v2/setup/admin-password", json={"token": "x" * 40, "password": PW})
    assert bad.status_code == 403
    early = client.post("/api/v2/setup/first-user", json={"token": token, "username": "anna",
                                                          "email": "a@x.test", "password": PW})
    assert early.status_code == 409


async def test_full_setup_flow_then_the_api_opens(client, db, setup_on):
    token = await setup_state.bootstrap(db)
    assert client.post("/api/v2/setup/admin-password", json={"token": token, "password": "short"}).status_code == 422
    assert client.post("/api/v2/setup/admin-password", json={"token": token, "password": PW}).json()["step"] == "first_user"

    created = client.post("/api/v2/setup/first-user", json={
        "token": token, "username": "anna", "email": "anna@x.test", "password": PW, "role": "admin"})
    assert created.status_code == 201, created.text
    assert created.json()["roles"] == ["admin", "user"]
    assert client.post("/api/v2/setup/provider", json={"token": token, "module": None}).json()["step"] == "library"

    outside = client.post("/api/v2/setup/library", json={"token": token, "name": "Main", "path": "/etc"})
    assert outside.status_code == 422
    inside = client.post("/api/v2/setup/library", json={"token": token, "name": "Main", "path": "manga"})
    assert inside.status_code == 200, inside.text
    assert inside.json()["library"]["path"].endswith("/manga")

    done = client.post("/api/v2/setup/finish", json={"token": token})
    assert done.status_code == 200 and done.json()["required"] is False
    assert setup_state.required() is False
    assert client.get("/api/v2/setup/status").status_code == 410 or client.post(
        "/api/v2/setup/finish", json={"token": token}).status_code == 410
    assert (await db.get(AppSetting, setup_state.TOKEN_KEY)) is None
    assert await setup_state.bootstrap(db) is None  # a restart after completion issues no token


async def test_a_provider_step_without_the_host_says_so(client, db, setup_on, monkeypatch):
    token = await setup_state.bootstrap(db)
    assert client.post("/api/v2/setup/admin-password", json={"token": token, "password": PW}).status_code == 200
    assert client.post("/api/v2/setup/first-user", json={"token": token, "username": "bob", "email": "b@x.test",
                                                         "password": PW, "role": "user"}).status_code == 201
    monkeypatch.setattr(settings, "EXTENSION_HOST_TOKEN", None)
    r = client.post("/api/v2/setup/provider", json={"token": token, "module": "en/mangakatana"})
    assert r.status_code == 503 and "skip" in r.json()["detail"]


async def test_library_path_is_created_inside_the_root(client, db, setup_on):
    import os
    token = await setup_state.bootstrap(db)
    client.post("/api/v2/setup/admin-password", json={"token": token, "password": PW})
    client.post("/api/v2/setup/first-user", json={"token": token, "username": "cyd", "email": "c@x.test",
                                                  "password": PW, "role": "user"})
    client.post("/api/v2/setup/provider", json={"token": token, "module": None})
    r = client.post("/api/v2/setup/library", json={"token": token, "name": "Shelf", "path": "deep/new"})
    assert r.status_code == 200 and os.path.isdir(setup_on / "storage" / "deep" / "new")


async def test_the_last_admin_cannot_be_removed_and_users_keep_the_user_group(db):
    anna = User(username="anna2", email="anna2@x.test", hashed_password="x", is_active=True)
    db.add(anna)
    await db.flush()
    await groups.set_role(db, anna, "admin")
    await db.flush()
    assert anna.is_superuser is True
    with pytest.raises(groups.GroupError):
        await groups.remove(db, anna, groups.ADMIN)  # the only admin
    with pytest.raises(groups.GroupError):
        await groups.remove(db, anna, groups.USER)
    bo = User(username="bo2", email="bo2@x.test", hashed_password="x", is_active=True)
    db.add(bo)
    await db.flush()
    await groups.join_default(db, bo)
    await groups.set_role(db, bo, "admin")
    await groups.remove(db, anna, groups.ADMIN)  # there is a second admin now
    assert anna.is_superuser is False and await groups.is_member(db, anna.id, groups.USER)



async def test_admin_can_change_roles_and_the_last_admin_is_protected(client, db):
    root = User(username="root3", email="root3@x.test", hashed_password="x", is_active=True)
    other = User(username="other3", email="other3@x.test", hashed_password="x", is_active=True)
    db.add_all([root, other])
    await db.flush()
    await groups.join_default(db, root)
    await groups.set_role(db, root, "admin")
    await groups.join_default(db, other)
    await db.commit()
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": root.id, "is_superuser": True})()
    try:
        listed = client.get("/api/v2/admin/users").json()["items"]
        assert {u["username"] for u in listed} >= {"root3", "other3"}
        promoted = client.put(f"/api/v2/admin/users/{other.id}/role", json={"role": "admin"})
        assert promoted.status_code == 200 and promoted.json()["roles"] == ["admin", "user"]
        demoted_root = client.put(f"/api/v2/admin/users/{root.id}/role", json={"role": "user"})
        assert demoted_root.status_code == 200  # other is an admin now, so root can step down
        last = client.put(f"/api/v2/admin/users/{other.id}/role", json={"role": "user"})
        assert last.status_code == 409  # root is no longer an admin, so other is the last one
        assert client.put(f"/api/v2/admin/users/{other.id}/role", json={"role": "boss"}).status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_regular_users_cannot_use_admin_routes(client, db):
    u = User(username="plain4", email="plain4@x.test", hashed_password="x", is_active=True)
    db.add(u)
    await db.flush()
    await groups.join_default(db, u)
    await db.commit()
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": u.id, "is_superuser": False})()
    try:
        assert client.get("/api/v2/admin/users").status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_an_unwritable_library_folder_is_a_clear_error(client, db, setup_on, monkeypatch):
    token = await setup_state.bootstrap(db)
    client.post("/api/v2/setup/admin-password", json={"token": token, "password": PW})
    client.post("/api/v2/setup/first-user", json={"token": token, "username": "dee", "email": "d@x.test",
                                                  "password": PW, "role": "user"})
    client.post("/api/v2/setup/provider", json={"token": token, "module": None})

    def refuse(*a, **k):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr("os.makedirs", refuse)
    r = client.post("/api/v2/setup/library", json={"token": token, "name": "Shelf", "path": "x"})
    assert r.status_code == 422 and "Permission denied" in r.json()["detail"]
    # the step did not advance, so the wizard can be retried
    assert (await setup_state.current_step(db)) == "library"
