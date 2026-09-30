import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base


class VeiculoEnum(StrEnum):
    MOTO = "MOTO"
    CARRO = "CARRO"
    BICICLETA = "BICICLETA"


class StatusEntregadorEnum(StrEnum):
    DISPONIVEL = "DISPONIVEL"
    INDISPONIVEL = "INDISPONIVEL"
    EM_ENTREGA = "EM_ENTREGA"


class Entregador(Base):
    __tablename__ = "entregadores"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    veiculo: Mapped[VeiculoEnum] = mapped_column(
        SQLEnum(VeiculoEnum, name="veiculo_entregador_enum"),
        nullable=False,
    )
    status: Mapped[StatusEntregadorEnum] = mapped_column(
        SQLEnum(StatusEntregadorEnum, name="status_entregador_enum"),
        nullable=False,
        default=StatusEntregadorEnum.DISPONIVEL,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
