from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.entregador_repository import EntregadorRepository
from app.schemas.entregador import (
    EntregadorCreate,
    EntregadorRead,
    EntregadorStatusUpdate,
    EntregadorUpdate,
)
from app.services.entregador_service import EntregadorService

router = APIRouter(prefix="/entregadores", tags=["entregadores"])

DbSession = Annotated[Session, Depends(get_db)]


def get_entregador_service(db: DbSession) -> EntregadorService:
    repository = EntregadorRepository(db)
    return EntregadorService(repository)


ServiceDep = Annotated[EntregadorService, Depends(get_entregador_service)]


@router.post("", response_model=EntregadorRead, status_code=status.HTTP_201_CREATED)
def create_entregador(payload: EntregadorCreate, service: ServiceDep) -> EntregadorRead:
    return service.create_entregador(payload)


@router.get("", response_model=list[EntregadorRead])
def list_entregadores(service: ServiceDep) -> list[EntregadorRead]:
    return service.list_entregadores()


@router.get("/{entregador_id}", response_model=EntregadorRead)
def get_entregador(entregador_id: UUID, service: ServiceDep) -> EntregadorRead:
    return service.get_entregador(entregador_id)


@router.put("/{entregador_id}", response_model=EntregadorRead)
def update_entregador(
    entregador_id: UUID,
    payload: EntregadorUpdate,
    service: ServiceDep,
) -> EntregadorRead:
    return service.update_entregador(entregador_id, payload)


@router.delete("/{entregador_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entregador(entregador_id: UUID, service: ServiceDep) -> Response:
    service.delete_entregador(entregador_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{entregador_id}/status", response_model=EntregadorRead)
def update_status(
    entregador_id: UUID,
    payload: EntregadorStatusUpdate,
    service: ServiceDep,
) -> EntregadorRead:
    return service.update_status(entregador_id, payload)
