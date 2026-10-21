FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt docker/constraints.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt -c constraints.txt

COPY server/ .
RUN cd DJANGO_SERVER && SECRET_KEY=collectstatic python manage.py collectstatic --noinput
