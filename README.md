# MOEX AI Analyst

Telegram-based AI market analyst for the Moscow Exchange (MOEX).

Ingests market data from the MOEX ISS API, computes deterministic technical
analysis (indicators → market structure → probability), generates AI-assisted
commentary, and delivers it to Telegram users on demand and on schedule.

## Instruments & timeframes

- **Instruments:** `IMOEX`, `UWGN`, `SNGS`, `SGZH`, `VTBR`, `YAKOVLEV`
- **Timeframes:** `1H`, `4H` (aggregated from 1H — MOEX ISS has no native 4H), `1D`

## Stack

Python 3.13 · FastAPI · Aiogram 3 · PostgreSQL 17 · Redis · SQLAlchemy 2 ·
Alembic · APScheduler · Docker / Docker Compose.

## Architecture

Clean Architecture / DDD-inspired. Dependencies point **inward**.

```
src/app/
├── main.py                  # FastAPI app factory + lifespan (API process)
├── bot_entrypoint.py        # Aiogram bot process entrypoint
├── scheduler_entrypoint.py  # APScheduler process entrypoint
│
├── core/                    # cross-cutting: config, logging, errors, types
│
├── domain/                  # enterprise rules — pure Python, no I/O
│   ├── market/              # Instrument, Candle, Ticker, Timeframe, ...
│   ├── analysis/            # indicators, structure, probability, signals
│   └── subscription/        # User, Subscription, Alert, Watchlist
│
├── application/             # use cases (orchestration)
│   ├── ports/               # interfaces implemented by infrastructure
│   ├── dto.py               # input/output DTOs
│   └── use_cases/           # one class per use case
│
├── infrastructure/          # frameworks & drivers (implement ports)
│   ├── moex/                # MOEX ISS async client + parsing + services
│   ├── db/                  # SQLAlchemy 2 async: engine, models, repos, UoW
│   ├── cache/               # Redis adapter
│   ├── llm/                 # Anthropic (Claude) analyst adapter
│   └── telegram/            # Bot-API notifier (scheduler broadcasts)
│
├── presentation/
│   ├── api/                 # FastAPI routers (health, webhook)
│   └── bot/                 # Aiogram dispatcher, routers, middlewares, FSM
│
├── scheduler/               # APScheduler config + jobs
└── di/                      # composition root (dishka providers)
```

**Rule:** `domain` imports nothing from `application` / `infrastructure` /
`presentation`. ORM models live in `infrastructure/db/models` and are mapped
to/from domain entities — they are not the same objects.

## Processes

Three deployable processes from one codebase, sharing PostgreSQL and Redis:

| Process     | Entrypoint                   | Responsibility                          |
|-------------|------------------------------|-----------------------------------------|
| `api`       | `app.main:create_app`        | health, metrics, Telegram webhook       |
| `bot`       | `app.bot_entrypoint`         | interactive Aiogram dispatcher          |
| `scheduler` | `app.scheduler_entrypoint`   | ingestion + scheduled analysis & alerts |

## Local development

```bash
cp .env.example .env        # fill in BOT_TOKEN, ANTHROPIC_API_KEY, ...
docker compose up --build
```

Migrations run automatically on the API container start (or via
`docker compose run --rm api alembic upgrade head`).
