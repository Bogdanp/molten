# TODO API Example

This example uses DI, Components and middleware to build a simple TODO
management API.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl -H'authorization: secret' -d 'description=buy milk' http://127.1:8000/v1/todos/
    $ curl -H'authorization: secret' http://127.1:8000/v1/todos/
    $ curl -H'authorization: secret' http://127.1:8000/v1/todos/1
    $ curl -H'authorization: secret' -XDELETE http://127.1:8000/v1/todos/1
