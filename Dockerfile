# syntax=docker/dockerfile:1

# =============================================================================
# MOEX AI Analyst — multi-stage image
#
# One image runs all three processes (api / bot / scheduler); the process is
# selected by the compose `command`. Built with uv; runs as a non-root user.
# =============================================================================

# --- Stage 1: builder --------------------------------------------------------
# uv's official image bundles uv on top of python:3.13 (bookworm-slim), so the
# resulting .venv interpreter path matches the runtime base below.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1) Resolve & install runtime dependencies first (cached layer). `uv.lock*`
#    is a glob: included when committed, skipped when absent.
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# 2) Install the project itself (separate layer, invalidated only on source
#    changes). README.md is required by the build backend (project readme).
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# --- Stage 2: runtime --------------------------------------------------------
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Non-root user (fixed uid/gid for predictable file ownership).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home appuser

WORKDIR /app

# Copy the pre-built virtualenv and source, owned by the non-root user.
COPY --from=builder --chown=appuser:app /app/.venv /app/.venv
COPY --from=builder --chown=appuser:app /app/src /app/src
COPY --from=builder --chown=appuser:app /app/pyproject.toml /app/README.md ./

USER appuser

EXPOSE 8000

# Default process; overridden per-service in docker-compose.yml.
CMD ["moex-bot"]
