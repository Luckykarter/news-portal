FROM python:3.9-slim as app
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY . /app

WORKDIR /app

ENV PYTHONPATH=/app

RUN python manage.py collectstatic --clear --noinput

EXPOSE 8000
