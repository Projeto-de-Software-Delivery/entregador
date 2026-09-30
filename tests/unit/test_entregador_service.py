from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import EntregadorNotFoundError
from app.models.entregador import Entregador, StatusEntregadorEnum, VeiculoEnum
from app.schemas.entregador import EntregadorCreate, EntregadorStatusUpdate, EntregadorUpdate
from app.services.entregador_service import EntregadorService


class FakeEntregadorRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Entregador] = {}

    def create(self, entregador: Entregador) -> Entregador:
        now = datetime.now(UTC)
        entregador.id = uuid4()
        entregador.created_at = now
        entregador.updated_at = now
        self.items[entregador.id] = entregador
        return entregador

    def list(self) -> list[Entregador]:
        return list(self.items.values())

    def get_by_id(self, entregador_id: UUID) -> Entregador | None:
        return self.items.get(entregador_id)

    def save(self, entregador: Entregador) -> Entregador:
        entregador.updated_at = datetime.now(UTC)
        self.items[entregador.id] = entregador
        return entregador

    def delete(self, entregador: Entregador) -> None:
        del self.items[entregador.id]


def make_service() -> tuple[EntregadorService, FakeEntregadorRepository]:
    repository = FakeEntregadorRepository()
    return EntregadorService(repository), repository


def create_sample_entregador(service: EntregadorService) -> Entregador:
    payload = EntregadorCreate(nome="Ana Silva", veiculo=VeiculoEnum.MOTO)
    return service.create_entregador(payload)


def test_criar_entregador() -> None:
    service, _repository = make_service()

    entregador = create_sample_entregador(service)

    assert entregador.id is not None
    assert entregador.nome == "Ana Silva"
    assert entregador.veiculo == VeiculoEnum.MOTO
    assert entregador.status == StatusEntregadorEnum.DISPONIVEL


def test_buscar_entregador() -> None:
    service, _repository = make_service()
    created = create_sample_entregador(service)

    found = service.get_entregador(created.id)

    assert found.id == created.id


def test_atualizar_entregador() -> None:
    service, _repository = make_service()
    created = create_sample_entregador(service)
    payload = EntregadorUpdate(nome="Bruno Souza", veiculo=VeiculoEnum.CARRO)

    updated = service.update_entregador(created.id, payload)

    assert updated.nome == "Bruno Souza"
    assert updated.veiculo == VeiculoEnum.CARRO
    assert updated.status == StatusEntregadorEnum.DISPONIVEL


def test_deletar_entregador() -> None:
    service, repository = make_service()
    created = create_sample_entregador(service)

    service.delete_entregador(created.id)

    assert created.id not in repository.items


def test_alterar_status() -> None:
    service, _repository = make_service()
    created = create_sample_entregador(service)
    payload = EntregadorStatusUpdate(status=StatusEntregadorEnum.EM_ENTREGA)

    updated = service.update_status(created.id, payload)

    assert updated.status == StatusEntregadorEnum.EM_ENTREGA


def test_erro_ao_buscar_id_inexistente() -> None:
    service, _repository = make_service()

    with pytest.raises(EntregadorNotFoundError):
        service.get_entregador(uuid4())


def test_erro_ao_alterar_status_de_id_inexistente() -> None:
    service, _repository = make_service()
    payload = EntregadorStatusUpdate(status=StatusEntregadorEnum.INDISPONIVEL)

    with pytest.raises(EntregadorNotFoundError):
        service.update_status(uuid4(), payload)
