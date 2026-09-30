"""create entregadores table

Revision ID: 20260930_0001
Revises:
Create Date: 2026-09-30 13:50:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260930_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "MOTO",
        "CARRO",
        "BICICLETA",
        name="veiculo_entregador_enum",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "DISPONIVEL",
        "INDISPONIVEL",
        "EM_ENTREGA",
        name="status_entregador_enum",
    ).create(bind, checkfirst=True)

    op.create_table(
        "entregadores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column(
            "veiculo",
            postgresql.ENUM(
                "MOTO",
                "CARRO",
                "BICICLETA",
                name="veiculo_entregador_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "DISPONIVEL",
                "INDISPONIVEL",
                "EM_ENTREGA",
                name="status_entregador_enum",
                create_type=False,
            ),
            server_default=sa.text("'DISPONIVEL'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entregadores_status", "entregadores", ["status"])
    op.alter_column("entregadores", "status", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_entregadores_status", table_name="entregadores")
    op.drop_table("entregadores")
    postgresql.ENUM(name="status_entregador_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="veiculo_entregador_enum").drop(bind, checkfirst=True)
