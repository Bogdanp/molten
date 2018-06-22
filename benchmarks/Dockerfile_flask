FROM python:3.6

RUN pip install gunicorn meinheld flask
ADD app_flask.py app.py
ENTRYPOINT ["gunicorn", "--workers=8", "--worker-class=meinheld.gmeinheld.MeinheldWorker", "-b0.0.0.0:8000", "app:app"]
