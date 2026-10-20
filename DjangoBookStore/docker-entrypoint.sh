#!/bin/sh

if [ -z "$DATABASE_URL" ] && [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo 'Waiting for postgres...'
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.5
  done
  echo 'PostgreSQL started'
fi

if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput

  if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput || true
  fi

  if [ "$LOAD_DEMO_DATA" = "1" ]; then
    python manage.py shell -c "import sys; from books.models import Book; sys.exit(0 if Book.objects.exists() else 1)" || python manage.py generate_books
  fi
fi

exec "$@"