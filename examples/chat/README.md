# Long-polling Example

An example demonstrating the usage of `molten.StreamingResponse` to
build a simple chat application.

## Usage

Install molten with `pip install -e '.[dev]'` then run the app with:

    $ gunicorn -k gevent --worker-connections 128 app:app

## Example requests

In one terminal tab run

    $ curl http://127.1:8000/envelopes/Jim

then run the following in another tab

    $ curl -F'username=Joe' -F'message=Hi all!' http://127.1:8000/envelopes
    $ curl -F'username=Joe' -F'message=Hi Jim!' -F'recipient=Jim' http://127.1:8000/envelopes
