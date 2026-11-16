# diss_market (KGi-DISS-I042): oTree app with a TypeScript front end.
#   stage 1  Node: type-checks, unit-tests and bundles the front end
#   stage 2  Python: runs oTree in production mode as a non-root user
# Build from this directory:  docker build -t diss-market .
ARG NODE_IMAGE=node:22-slim
ARG PYTHON_IMAGE=python:3.13-slim

FROM ${NODE_IMAGE} AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# build.mjs writes the bundle to ../_static/diss_market; a failing type check or unit test stops the image
RUN npm run typecheck && npm test && npm run build

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OTREE_PRODUCTION=1 \
    PORT=8000
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin otree \
    && mkdir -p /app/pools /app/data && chown -R otree:otree /app
COPY --chown=otree:otree settings.py ./
COPY --chown=otree:otree diss_market ./diss_market
COPY --chown=otree:otree diss_bandit ./diss_bandit
COPY --chown=otree:otree schedules ./schedules
COPY --chown=otree:otree --from=frontend /build/_static ./_static
USER otree
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/login', timeout=4)"
CMD ["sh", "-c", "exec otree prodserver ${PORT}"]
