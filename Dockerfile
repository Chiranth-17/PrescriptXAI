FROM python:3.12-slim AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /build
# The CPU local version satisfies the pinned torch public version without CUDA packages.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.14.1
COPY dist/prescriptxai-0.2.0-py3-none-any.whl ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "/build/prescriptxai-0.2.0-py3-none-any.whl[api,dashboard]"

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 prescriptxai \
    && useradd --create-home --uid 10001 --gid prescriptxai operator \
    && mkdir -p /work/data /work/artifacts /work/configs \
    && chown -R operator:prescriptxai /work
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
USER 10001:10001
EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8)"
CMD ["prescriptxai", "serve", "--config", "configs/default.yaml"]
