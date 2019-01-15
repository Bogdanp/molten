# Serverless Example

An example demonstrating the usage of molten with [serverless].

## Usage

Install molten with `pip install -e '.[dev]'`, then install werkzeug
by running `pip install werkzeug`.  Finally, install `serverless` and
`serverless-wsgi` via `npm install -g serverless serverless-wsgi` and
run the app with `sls wsgi serve`.

## Example requests

    $ curl http://127.1:5000/hello/Jim


[serverless]: https://serverless.com/
