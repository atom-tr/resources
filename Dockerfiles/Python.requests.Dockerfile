# syntax=docker/dockerfile:1
FROM dhi.io/python:3-debian13-dev AS build-stage
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /app/venv && pip install --no-cache-dir requests

FROM dhi.io/python:3-debian13-dev AS runtime-stage
LABEL image.description="Secure, minimal Python app using Requests and Distroless"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/venv/bin:$PATH"
WORKDIR /app
COPY --from=build-stage /app/venv /app/venv