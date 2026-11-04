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
  messaging/       consumidor RabbitMQ dos eventos de pedido
tests/
  unit/            testes do service, handler e consumidor
  integration/     testes de API e de eventos com RabbitMQ real
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

## Eventos (RabbitMQ)

Alem da API HTTP (chamada de forma sincrona pelo `pedidos-lojas`), o servico
consome de forma assincrona os eventos que o `pedidos-lojas` publica no exchange
topic `pedidos`, numa fila propria (`entregador.pedidos`):

| Routing key | Efeito no entregador (`data.entregadorId`) |
|---|---|
| `entrega.aceita` | passa para `EM_ENTREGA` |
| `pedido.entregue` | volta para `DISPONIVEL` |

- Mensagem malformada e descartada (reject sem requeue) e logada; falha
  inesperada (ex.: banco fora) volta para a fila.
- Aplicar o mesmo evento duas vezes nao muda nada (idempotente).
- O consumidor roda numa thread junto da API e reconecta sozinho se o broker cair.

| Variavel | Padrao | Descricao |
|---|---|---|
| `RABBITMQ_URL` | *(vazio)* | URL AMQP, ex.: `amqp://guest:guest@rabbitmq:5672/%2F`. Vazio desliga o consumidor. |
| `RABBITMQ_EXCHANGE` | `pedidos` | Exchange topic dos eventos de pedido. |
| `RABBITMQ_QUEUE` | `entregador.pedidos` | Fila deste servico. |

No CI, `RABBITMQ_TEST_URL` aponta para um RabbitMQ de verdade e liga o teste de
integracao `tests/integration/test_eventos_rabbitmq.py` (sem a variavel, ele e pulado).

## Escopo atual

CRUD de entregadores, alteracao de status (HTTP) e consumo dos eventos de pedido
(RabbitMQ). Auth0 (validado no gateway), tracking e mapas ficaram fora do escopo.
