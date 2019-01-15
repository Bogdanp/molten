FROM python:3.6

RUN pip install -U pip
RUN pip install gunicorn meinheld

ADD . /molten
WORKDIR /molten
RUN rm -r dist && python setup.py sdist
RUN pip install $(cat pyproject.toml | grep "^version = " | cut -d'"' -f2 | xargs printf "dist/molten-%s.tar.gz")
ENTRYPOINT ["gunicorn", "--workers=8", "--worker-class=meinheld.gmeinheld.MeinheldWorker", "-b0.0.0.0:8000", "--pythonpath=/molten/benchmarks", "app_molten:app"]
