from io import BytesIO

from molten import Headers, UploadedFile


def test_uploaded_files_are_representable():
    # Given that I have an uploaded file
    uploaded_file = UploadedFile("a.txt", Headers(), BytesIO())

    # When I call repr on it
    # Then I should get back a valid repr
    assert repr(uploaded_file)


def test_uploaded_files_can_be_saved_to_file_like_objects():
    # Given that I have an uploaded file
    uploaded_file = UploadedFile("a.txt", Headers(), BytesIO(b"data"))

    # When I save it to an in-memory buffer
    output = BytesIO()
    uploaded_file.save(output)

    # Then the data should be copied to that buffer
    assert output.getvalue() == b"data"


def test_uploaded_files_can_be_saved_to_paths():
    # Given that I have an uploaded file
    uploaded_file = UploadedFile("a.txt", Headers(), BytesIO(b"data"))

    # When I save it to a path on disk
    filename = "tests/http/fixtures/uploaded_file_output"
    uploaded_file.save(filename)

    # Then the data should be copied to that file
    with open(filename, "rb") as f:
        assert f.read() == b"data"
