# Dramatiq Example

An example demonstrating the [dramatiq] integration.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`, then run dramatiq workers with `dramatiq app`.
You'll also need a running RabbitMQ server.

## Example requests

    $ curl http://127.1:8000/add/1/2
    $ curl http://127.1:8000/results/latest


[dramatiq]: https://dramatiq.io
