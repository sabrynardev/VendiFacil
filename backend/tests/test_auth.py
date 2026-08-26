def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={"email": "admin@marketpulse.dev", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


def test_login_invalid_password(client):
    response = client.post(
        "/auth/login",
        json={"email": "admin@marketpulse.dev", "password": "senha-errada"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas."
