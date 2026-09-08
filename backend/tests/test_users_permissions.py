def test_current_user_exposes_profile_permissions(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile_name"] == "Administrador"
    assert "users.manage" in payload["permissions"]
    assert "audit.view" in payload["permissions"]


def test_admin_creates_cashier_and_permissions_are_enforced(client, auth_headers):
    created = client.post(
        "/users",
        headers=auth_headers,
        json={
            "name": "Caixa da manhã",
            "email": "caixa.manha@example.com",
            "password": "caixa123",
            "role": "CAIXA",
            "active": True,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["profile_name"] == "Caixa"

    login = client.post("/auth/login", json={"email": "caixa.manha@example.com", "password": "caixa123"})
    cashier_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get("/products", headers=cashier_headers).status_code == 200
    assert client.get("/users", headers=cashier_headers).status_code == 403
    assert client.get("/reports", headers=cashier_headers).status_code == 403


def test_sensitive_operations_generate_audit_log(client, auth_headers):
    created = client.post(
        "/users",
        headers=auth_headers,
        json={
            "name": "Gerente Loja",
            "email": "gerente@example.com",
            "password": "gerente123",
            "role": "GERENTE",
            "active": True,
        },
    )
    assert created.status_code == 201, created.text

    entries = client.get("/audit", headers=auth_headers)

    assert entries.status_code == 200
    assert any(
        entry["entity_type"] == "USER"
        and entry["entity_id"] == str(created.json()["id"])
        and entry["action"] == "CREATE"
        for entry in entries.json()
    )


def test_profile_permission_update_is_persisted_and_audited(client, auth_headers):
    profiles = client.get("/profiles", headers=auth_headers).json()
    stock_profile = next(profile for profile in profiles if profile["code"] == "ESTOQUE")
    permission_codes = [permission["code"] for permission in stock_profile["permissions"] if permission["code"] != "products.manage"]

    updated = client.put(
        f"/profiles/{stock_profile['id']}/permissions",
        headers=auth_headers,
        json={"permission_codes": permission_codes},
    )
    assert updated.status_code == 200, updated.text
    assert "products.manage" not in {permission["code"] for permission in updated.json()["permissions"]}

    entries = client.get("/audit", headers=auth_headers).json()
    assert any(entry["entity_type"] == "PROFILE" and entry["action"] == "UPDATE_PERMISSIONS" for entry in entries)
