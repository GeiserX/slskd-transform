FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

# The base image ships ca-certificates 20250419, which still trusts the
# compromised eMudhra intermediates; the Debian update distrusts them.
RUN apt-get update \
 && apt-get install -y --no-install-recommends --only-upgrade ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local

RUN useradd --create-home appuser
USER appuser

RUN mkdir -p /app/music /app/downloads /app/organized

ENTRYPOINT ["slskd-transform"]
CMD ["search"]
