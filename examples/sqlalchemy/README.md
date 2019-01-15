# SQLAlchemy Example

An example demonstrating the usage of `molten.contrib.sqlalchemy`.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl -F'name=mittens' http://127.1:8000/v1/kittens
    $ curl http://127.1:8000/v1/kittens
    $ curl http://127.1:8000/v1/kittens/1
