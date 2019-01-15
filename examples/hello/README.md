# Hello World Example

An example showing usage of route parameters with molten.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl http://127.1:8000/hello/Jim/24
    $ curl http://127.1:8000/hello/Jim/invalid
