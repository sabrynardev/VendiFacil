def test_category_crud_and_duplicate_validation(client, auth_headers):
    created = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "Importados", "description": "Produtos importados"},
    )
    assert created.status_code == 201, created.text

    duplicate = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "importados", "description": None},
    )
    assert duplicate.status_code == 409

    updated = client.put(
        f"/categories/{created.json()['id']}",
        headers=auth_headers,
        json={"name": "Importados e especiais", "description": "Seleção especial"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Importados e especiais"

    deleted = client.delete(f"/categories/{created.json()['id']}", headers=auth_headers)
    assert deleted.status_code == 204


def test_category_with_products_cannot_be_deleted(client, auth_headers):
    category = client.get("/categories", headers=auth_headers).json()[0]
    response = client.delete(f"/categories/{category['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert "produtos vinculados" in response.json()["detail"]
