#!/bin/sh

echo 'Waiting for postgres...'
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done
echo 'PostgreSQL started'
if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"