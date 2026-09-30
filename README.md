# delivery-entregador

Microsservico FastAPI responsavel pelo cadastro e disponibilidade de entregadores
em uma aplicacao academica de delivery baseada em microsservicos.

## Stack

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- PostgreSQL
- Pydantic v2 / pydantic-settings
- Alembic
- Pytest + pytest-cov
- Docker / Docker Compose
- GitHub Actions

## Estrutura

```text
app/
  core/            configuracao, logging e excecoes
  database/        base declarativa e sessao SQLAlchemy
  models/          modelos ORM
  schemas/         contratos Pydantic
  repositories/    acesso a dados
  services/        regras de caso de uso
  routers/         endpoints HTTP
tests/
  unit/            testes do service
  integration/     testes de API
alembic/           migrations
```

## Configuracao local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Para rodar o app fora do Docker contra um PostgreSQL publicado localmente, ajuste
o `DATABASE_URL` para usar `localhost` como host do banco.

## Rodar com Docker Compose

```powershell
docker compose up --build
```

O Compose sobe PostgreSQL e API, executa `alembic upgrade head` e expoe a API em
`http://localhost:8000`.

## Rodar localmente sem container da API

Suba o PostgreSQL:

```powershell
docker compose up -d postgres
```

Configure a URL local do banco:

```powershell
$env:DATABASE_URL="postgresql+psycopg://delivery_user:delivery_password@localhost:5432/delivery_entregador"
```

Execute migrations e inicie a API:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

## Testes e cobertura

```powershell
pytest
```

O comando gera cobertura no terminal e falha se ficar abaixo de 80%.
Os testes usam SQLite em memoria com `StaticPool` para serem previsiveis e nao
dependerem de um PostgreSQL externo. Em desenvolvimento e producao, o banco alvo
e PostgreSQL.

## Endpoints principais

- `GET /health`
- `POST /entregadores`
- `GET /entregadores`
- `GET /entregadores/{id}`
- `PUT /entregadores/{id}`
- `DELETE /entregadores/{id}`
- `PATCH /entregadores/{id}/status`

## Escopo atual

Esta primeira versao implementa apenas CRUD de entregadores e alteracao de
status. RabbitMQ, notificacoes, Auth0, tracking, corrida e mapas ficaram fora do
escopo de proposito.
