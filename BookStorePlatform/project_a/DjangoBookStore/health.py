from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def health(request):
    """Health check: reports whether the database and the cache respond.

    Returns 200 with {"status": "ok"} when everything works,
    503 with {"status": "error"} when any dependency is down.
    """
    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')  # самый простой запрос: БД отвечает?
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'error'

    try:
        cache.set('health_check', '1', 10)  # записать и прочитать: кеш работает?
        checks['cache'] = 'ok' if cache.get('health_check') == '1' else 'error'
    except Exception:
        checks['cache'] = 'error'

    healthy = all(value == 'ok' for value in checks.values())
    return JsonResponse(
        {'status': 'ok' if healthy else 'error', **checks},
        status=200 if healthy else 503,
    )
