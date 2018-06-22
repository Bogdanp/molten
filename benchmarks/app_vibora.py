from vibora import Request, Vibora
from vibora.responses import JsonResponse

app = Vibora()


@app.route("/")
async def index() -> JsonResponse:
    return JsonResponse({"message": "hello!"})


@app.route("/hello/<name>/<age>")
async def hello(name: str, age: int) -> JsonResponse:
    return JsonResponse(f"Hi {name}! I hear you're {age} years old.")


@app.route("/echo", methods=["POST"])
async def echo(request: Request) -> JsonResponse:
    return JsonResponse(await request.json())


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8000)
