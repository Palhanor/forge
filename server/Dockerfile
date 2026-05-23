FROM docker:27-cli AS docker-cli

FROM python:3.12-slim

WORKDIR /app

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker

COPY pyproject.toml .
COPY forge_server/ forge_server/

RUN pip install --no-cache-dir .

ENV FORGE_DATA_DIR=/var/lib/forge/data
ENV FORGE_RELOAD=false

EXPOSE 8000

CMD ["forge-server"]
