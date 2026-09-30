from uuid import uuid4

from fastapi.testclient import TestClient


def criar_entregador(client: TestClient, nome: str = "Ana Silva") -> dict[str, str]:
    response = client.post(
        "/entregadores",
        json={"nome": nome, "veiculo": "MOTO"},
    )
    assert response.status_code == 201
    return response.json()


def test_post_entregadores(client: TestClient) -> None:
    data = criar_entregador(client)

    assert data["id"]
    assert data["nome"] == "Ana Silva"
    assert data["veiculo"] == "MOTO"
    assert data["status"] == "DISPONIVEL"
    assert data["created_at"]
    assert data["updated_at"]


def test_get_entregadores(client: TestClient) -> None:
    criar_entregador(client, "Ana Silva")
    criar_entregador(client, "Bruno Souza")

    response = client.get("/entregadores")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_entregadores_por_id(client: TestClient) -> None:
    created = criar_entregador(client)

    response = client.get(f"/entregadores/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_put_entregadores(client: TestClient) -> None:
    created = criar_entregador(client)

    response = client.put(
        f"/entregadores/{created['id']}",
        json={"nome": "Carla Lima", "veiculo": "CARRO"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Carla Lima"
    assert data["veiculo"] == "CARRO"
    assert data["status"] == "DISPONIVEL"


def test_patch_entregadores_status(client: TestClient) -> None:
    created = criar_entregador(client)

    response = client.patch(
        f"/entregadores/{created['id']}/status",
        json={"status": "EM_ENTREGA"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "EM_ENTREGA"


def test_delete_entregadores(client: TestClient) -> None:
    created = criar_entregador(client)

    delete_response = client.delete(f"/entregadores/{created['id']}")
    get_response = client.get(f"/entregadores/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_get_inexistente_retorna_404(client: TestClient) -> None:
    response = client.get(f"/entregadores/{uuid4()}")

    assert response.status_code == 404


def test_payload_invalido_retorna_422(client: TestClient) -> None:
    response = client.post(
        "/entregadores",
        json={"nome": "", "veiculo": "AVIAO"},
    )

    assert response.status_code == 422


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
