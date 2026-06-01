# MOEX AI Analyst Bot

## Project Status

Current stage:

- Stage 1 ✅ Architecture
- Stage 2 ✅ pyproject.toml
- Stage 3 ✅ Settings & Logging
- Stage 4 ✅ Docker Infrastructure
- Stage 5 ✅ Database Layer
- Stage 6 ✅ MOEX ISS Integration
- Stage 7 ✅ Analysis Engine
- Stage 8 ✅ Alert Engine

Not implemented yet:

- Stage 9 ⏳ Telegram Bot
- Stage 10 ⏳ Scheduler
- Stage 11 ⏳ Notifications
- Stage 12 ⏳ AI Narrator (Qwen)

---

# Project Goal

Build a production-grade Telegram market analyst for the Russian stock market.

Supported instruments:

- IMOEX
- UWGN
- SNGS
- SGZH
- VTBR
- IRKT (Яковлев)

Supported timeframes:

- 1H
- 4H
- 1D

The system should:

- fetch market data from MOEX ISS API
- calculate indicators
- detect market structure
- calculate probabilities
- generate alerts
- send Telegram notifications

The MVP must work fully without any LLM.

AI integration is planned only for V2.

---

# Architecture Rules

The project follows Clean Architecture.

Dependency direction:

Infrastructure
↓
Application
↓
Domain

Allowed:

presentation -> application
infrastructure -> application
application -> domain

Forbidden:

domain -> infrastructure
domain -> presentation
application -> infrastructure

Any new code must preserve these rules.

---

# Technology Stack

Python 3.13

FastAPI

Aiogram 3

PostgreSQL 17

Redis 7

SQLAlchemy 2

Alembic

Docker

Docker Compose

APScheduler

Pydantic v2

Loguru

httpx

tenacity

uv package manager

---

# Folder Structure

src/moex_analyst/

core/
application/
domain/
infrastructure/
presentation/
scheduler/
di/

---

# Configuration

Implemented:

- .env.example
- settings.py
- db_settings.py
- logging.py

Important:

Secrets use SecretStr.

Loguru masks secrets.

Settings use pydantic-settings.

No global Settings() instance.

Logging is initialized lazily.

---

# Docker

Implemented:

Dockerfile

docker-compose.yml

Services:

- postgres
- redis
- api
- bot
- scheduler

Healthchecks enabled.

Named volumes enabled.

Non-root user inside containers.

Infrastructure validated via:

docker compose config

---

# Database Layer

Implemented:

- Declarative Base
- Async Engine
- Async Session Factory
- Unit of Work
- Repository Base
- Alembic

Important:

No global engine.

No global session.

Repositories never commit.

Only UnitOfWork commits.

Alembic is isolated from application settings.

Alembic depends only on DB\_\_\* variables.

Alembic must never require:

- BOT\_\_TOKEN
- REDIS\_\_\*

---

# MOEX Integration

Implemented.

Location:

infrastructure/moex

Contains:

- DTOs
- Client
- Services
- Parser
- Mapper
- Retry logic
- Rate limiter

Important:

Column mapping is done by field name.

Never rely on column order from ISS.

Timezone is normalized to UTC.

4H candles are aggregated from 1H candles.

Aggregation rules:

Open = first candle

High = max(high)

Low = min(low)

Close = last candle

Volume = sum(volume)

---

# Domain Market

Domain models exist.

Important:

Domain models are independent from MOEX DTOs.

Use mapping layer.

Never pass infrastructure DTOs into domain services.

---

# Analysis Engine

Implemented.

Location:

domain/analysis

Capabilities:

- Trend Detection
- Market Structure Detection
- Support Detection
- Resistance Detection
- EMA20
- EMA50
- RSI14
- ATR14
- Volume Analysis
- Probability Engine

Output:

AnalysisResult

AnalysisResult contains:

- trend
- structure
- supports
- resistances
- indicator snapshot
- probabilities

---

# Probability Engine

Deterministic.

No AI.

Uses:

Trend

Structure

Volume

Momentum

Volatility

Returns:

- bullish probability
- bearish probability
- sideways probability

Probabilities always sum to 100.

---

# Alert Engine

Implemented.

Location:

domain/alerts

Input:

AnalysisResult

Output:

list[Alert]

Pure functions only.

No database.

No Telegram.

No external services.

Supported alert types:

- SUPPORT_BREAKDOWN
- RESISTANCE_BREAKOUT
- TREND_CHANGE
- EMA20_CROSS_EMA50
- RSI_OVERBOUGHT
- RSI_OVERSOLD
- VOLUME_SPIKE
- MARKET_STRUCTURE_CHANGE
- STRONG_BULLISH_SIGNAL
- STRONG_BEARISH_SIGNAL

Alert engine is deterministic and idempotent.

Coverage:

100%

---

# Technical Debt

Future improvement:

AnalysisResult should contain:

- last_close
- last_high
- last_low
- last_volume

Currently some alert rules use EMA20 as a proxy for current price.

Keep current behavior unchanged until V2.

---

# Testing Rules

Project uses:

pytest

pytest-asyncio

coverage

mypy --strict

ruff

Requirements:

All new code must include tests.

Do not reduce coverage.

Do not disable mypy rules.

Do not disable ruff rules.

---

# Current Priority

Stage 9

Implement Telegram Bot.

Requirements:

Aiogram 3

Polling mode only.

Commands:

/start
/help
/analyze <ticker>
/market
/best
/worst
/watchlist

Use existing:

- MOEX layer
- Analysis Engine
- Alert Engine

No fake services.

No stubs.

No TODOs.

No placeholders.

---

# Rules For Future Development

Before generating code:

1. Read the entire repository.
2. Explain how the new code fits into the architecture.
3. Preserve Clean Architecture.
4. Preserve existing tests.
5. Preserve strict typing.
6. Preserve async-first design.

Never rewrite existing architecture without justification.

Never introduce domain -> infrastructure dependencies.

Never introduce synchronous I/O into async flows.
