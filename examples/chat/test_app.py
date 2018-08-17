import json

from app import app
from molten import testing

client = testing.TestClient(app)


def test_users_can_broadcast_messages():
    # Given that I am receiving envelopes
    receiver_response = client.get(app.reverse_uri("receive_envelopes", username="Jim"))

    # When I broadcast a message
    broadcast_response = client.post(app.reverse_uri("send_envelope"), json={
        "username": "John",
        "message": "Hi all!",
    })

    # Then that request should succeed
    assert broadcast_response.status_code == 204

    # And the recipient should get the new envelope
    envelope = json.loads(next(receiver_response.stream))
    assert envelope == {"type": "envelope", "content": {"username": "John", "message": "Hi all!"}}

    # When I DM the recipient a message
    dm_response = client.post(app.reverse_uri("send_envelope"), json={
        "recipient": "Jim",
        "username": "John",
        "message": "Hi Jim!",
    })

    # Then that request should succeed
    assert dm_response.status_code == 204

    # And the recipient should get the new envelope
    envelope = json.loads(next(receiver_response.stream))
    assert envelope == {"type": "envelope", "content": {"username": "John", "message": "Hi Jim!"}}
