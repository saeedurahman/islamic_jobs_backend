release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn deeni_jobs.wsgi --bind 0.0.0.0:$PORT --log-file -
