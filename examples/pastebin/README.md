# Pastebin Example

A simple pastebin built with molten.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl http://127.1:8000
    $ curl --data-binary @example.txt http://127.1:8000
    $ curl http://127.1:8000/bc742daa-1d3c-46bb-a0b7-5338868256f7
