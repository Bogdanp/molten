from gevent.monkey import patch_all; patch_all()  # noqa

from app import app
from molten.contrib.websockets import BinaryMessage, TextMessage, WebsocketsTestClient

client = WebsocketsTestClient(app)


def test_non_websocket_connections_to_websocket_endpoints_fail():
    # Given that I have a websocket handler
    # When I request it without requesting a connection upgrade
    response = client.get(app.reverse_uri("echo"))

    # Then I should get back a 400
    assert response.status_code == 400


def test_echo_endpoint_echos_messages_back():
    with client.connect(app.reverse_uri("echo")) as sock:
        sock.send(TextMessage("hi!"))
        assert sock.receive(timeout=1).get_text() == "hi!"

        sock.send(BinaryMessage(b"hi!"))
        assert sock.receive(timeout=1).get_data() == b"hi!"
