from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.entregador import StatusEntregadorEnum, VeiculoEnum

NomeEntregador = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class EntregadorBase(BaseModel):
    nome: NomeEntregador
    veiculo: VeiculoEnum


class EntregadorCreate(EntregadorBase):
    pass


class EntregadorUpdate(EntregadorBase):
    pass


class EntregadorStatusUpdate(BaseModel):
    status: StatusEntregadorEnum


class EntregadorRead(EntregadorBase):
    id: UUID
    status: StatusEntregadorEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
