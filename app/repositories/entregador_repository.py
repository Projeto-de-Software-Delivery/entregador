from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entregador import Entregador


class EntregadorRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, entregador: Entregador) -> Entregador:
        self._db.add(entregador)
        self._db.commit()
        self._db.refresh(entregador)
        return entregador

    def list(self) -> list[Entregador]:
        statement = select(Entregador).order_by(Entregador.created_at.desc())
        return list(self._db.scalars(statement).all())

    def get_by_id(self, entregador_id: UUID) -> Entregador | None:
        return self._db.get(Entregador, entregador_id)

    def save(self, entregador: Entregador) -> Entregador:
        self._db.add(entregador)
        self._db.commit()
        self._db.refresh(entregador)
        return entregador

    def delete(self, entregador: Entregador) -> None:
        self._db.delete(entregador)
        self._db.commit()
