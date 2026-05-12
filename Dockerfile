FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local

RUN useradd --create-home appuser
USER appuser

RUN mkdir -p /app/music /app/downloads /app/organized

ENTRYPOINT ["slskd-transform"]
CMD ["search"]
