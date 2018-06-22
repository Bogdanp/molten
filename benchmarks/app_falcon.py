from falcon import API


class Index:
    def on_get(self, req, resp):
        resp.media = {"message": "hello!"}


class Hello:
    def on_get(self, req, resp, name, age):
        resp.media = f"Hi {name}! I hear you're {age} years old."


app = API()
app.add_route("/", Index())
app.add_route("/hello/{name}/{age:int}", Hello())
