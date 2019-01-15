# Sessions Example

An example demonstrating the usage of `molten.contrib.sessions`.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl -c cookies 'http://127.0.0.1:8000/set-username?username=test'
    $ curl -b cookies 'http://127.0.0.1:8000/get-username'
