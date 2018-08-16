# Websockets Example

This example demonstrates the usage of `molten.contrib.websockets` to
build a basic chatroom app.

## Usage

Install molten with `poetry develop` then install gunicorn and gevent
with `pip install gunicorn gevent`.  Run the server:

    $ gunicorn -k gevent app:app

Finally, `open chat.html` in a browser and talk to yourself.
