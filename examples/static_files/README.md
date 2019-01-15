# Static Files Example

An example demonstrating how [whitenoise] and molten can work together
to serve static content.

## Usage

Install molten with `pip install -e '.[dev]'` then `pip install
whitenoise` and run the app with `gunicorn app:app`.

## Example requests

    $ curl http://127.1:8000/static/app.css

[whitenoise]: http://whitenoise.evans.io/en/stable/
