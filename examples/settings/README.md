# Settings Example

This app demonstrates usage of `molten.contrib.toml_settings`.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

Run the app with `ENVIRONMENT=prod gunicorn app:app` to load
production settings.

## Example requests

    $ curl http://127.1:8000
