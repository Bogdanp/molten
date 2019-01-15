# Uploads Example

An example showing usage of `multipart/form-data` file uploads.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with
`gunicorn app:app`.

## Example requests

    $ curl -Ffile=@filename http://127.1:8000/upload
    $ curl -Ff=@filename http://127.1:8000/upload-one
