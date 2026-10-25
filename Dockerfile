FROM python:3.12-slim AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /build
COPY dist/*.whl ./
# The CPU local version satisfies the pinned torch public version without CUDA packages.
RUN pip install --no-cache-dir --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.14.1 \
    && pip install --no-cache-dir "$(find /build -maxdepth 1 -name '*.whl')[api,dashboard]"

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 operator \
    && mkdir -p /work/data /work/artifacts /work/configs \
    && chown -R operator:operator /work
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
USER 10001:10001
EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8)"
CMD ["prescriptxai", "serve", "--config", "configs/default.yaml"]
