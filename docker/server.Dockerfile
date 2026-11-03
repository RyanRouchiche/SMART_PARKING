FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt docker/constraints.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt -c constraints.txt

COPY server/ .
RUN cd DJANGO_SERVER && SECRET_KEY=collectstatic python manage.py collectstatic --noinput
