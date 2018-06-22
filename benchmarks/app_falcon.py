from falcon import API


class Index:
    def on_get(self, req, resp):
        resp.media = {"message": "hello!"}


class Hello:
    def on_get(self, req, resp, name, age):
        resp.media = f"Hi {name}! I hear you're {age} years old."


class Echo:
    def on_post(self, req, resp):
        resp.media = req.media


app = API()
app.add_route("/", Index())
app.add_route("/hello/{name}/{age:int}", Hello())
app.add_route("/echo", Echo())
