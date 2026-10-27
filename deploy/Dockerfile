# ============================================================================
# MediFlow - Dockerfile (Multi-Stage & Hardened para OCI Compute Always Free)
# Hackathon ONE G10 - Grupo 10: MediFlow
# Responsável: Ingrid Soares (Infra OCI, Redes, Segurança & Deploy)
# Compatível com arquiteturas x86_64 (VM.Standard.E2.1.Micro) e ARM64 (VM.Standard.A1.Flex)
# ============================================================================

FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ----------------------------------------------------------------------------
# Estágio Final de Execução (Runtime Slim & Usuário Não-Root)
# ----------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

LABEL maintainer="Equipe g10-Brasil27 <MediFlow Hackathon ONE>" \
      description="Agente Autônomo MediFlow - Triagem, Extração e Roteamento Clínico"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 mediflow \
    && useradd --uid 10001 --gid mediflow --shell /bin/bash --create-home mediflow

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=mediflow:mediflow . /app

USER mediflow

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
