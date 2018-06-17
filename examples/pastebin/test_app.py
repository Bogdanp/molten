from app import app
from molten import testing

client = testing.TestClient(app)


def test_app_can_upload_pastes():
    # When I submit a new paste
    response = client.post(
        app.reverse_uri("upload"),
        body=b"example",
    )

    # Then I should get back a successful response
    assert response.status_code == 200

    # When I try to get the paste
    paste_uri = response.json()
    paste_id = paste_uri.split("/")[-1]
    response = client.get(app.reverse_uri("get_paste", paste_id=paste_id))

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.data == "example"
