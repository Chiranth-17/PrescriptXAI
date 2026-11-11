FROM python:3.12-slim AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /build
# The CPU local version satisfies the pinned torch public version without CUDA packages.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.14.1
COPY dist/*.whl ./
RUN --mount=type=cache,target=/root/.cache/pip \
    for wheel in /build/*.whl; do pip install "${wheel}[api,dashboard]"; done

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 prescriptxai \
    && useradd --create-home --uid 10001 --gid prescriptxai operator \
    && mkdir -p /work/data /work/artifacts /work/configs \
    && chown -R operator:prescriptxai /work
COPY --from=builder /opt/venv /opt/venv
COPY scripts/packaging/health.py /opt/prescriptxai-health.py
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp
WORKDIR /work
USER 10001:10001
EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD ["python", "/opt/prescriptxai-health.py"]
CMD ["prescriptxai", "serve", "--config", "configs/default.yaml"]
