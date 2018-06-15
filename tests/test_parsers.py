from io import BytesIO
from random import randint

import pytest

from molten import (
    FieldTooLarge, FileTooLarge, Headers, MultiPartParser, ParseError, TooManyFields, UploadedFile
)


class FlakyStream:
    def __init__(self, stream):
        self._stream = stream

    def read(self, n):
        return self._stream.read(randint(1, n))


def test_multipart_parser_raises_400_if_boundary_is_missing():
    with pytest.raises(ParseError):
        parser = MultiPartParser()
        parser.parse(
            content_type="multipart/form-data",
            content_length="0",
            body_file=BytesIO(),
        )


@pytest.mark.parametrize("fixture,expected", [
    ("multipart_parsing_empty.dat", {}),
    ("multipart_parsing_fields_only.dat", {"x": "42", "y": "20"}),

    (
        "multipart_parsing_no_disposition.dat",
        ParseError("content-disposition header is missing"),
    ),

    (
        "multipart_parsing_no_name.dat",
        ParseError("content-disposition header without a name")
    ),

    (
        "multipart_parsing_no_terminator.dat",
        ParseError("unexpected end of input"),
    ),

    (
        "multipart_parsing_multiple_files.dat",
        [
            ("f", UploadedFile("a.txt", Headers({
                "content-disposition": 'multipart/form-data; name="f"; filename="a.txt"',
                "content-length": "1",
            }), BytesIO(b"a"))),
            ("f", UploadedFile("b.txt", Headers({
                "content-disposition": 'multipart/form-data; name="f"; filename="b.txt"',
                "content-length": "1",
            }), BytesIO(b"b"))),
            ("f", UploadedFile("c.txt", Headers({
                "content-disposition": 'multipart/form-data; name="f"; filename="c.txt"',
                "content-length": "1",
            }), BytesIO(b"c"))),
        ],
    ),

    (
        "multipart_parsing_line_breaks.dat",
        [
            ("f", UploadedFile("a.txt", Headers({
                "content-disposition": 'multipart/form-data; name="f"; filename="a.txt"',
                "content-length": "7",
            }), BytesIO(b"a\r\nb\r\nc"))),
        ],
    ),

    (
        "multipart_parsing_long_file.dat",
        [
            ("file", UploadedFile("blob1.dat", Headers({
                "content-disposition": 'multipart/form-data; name="file"; filename="blob1.dat"',
                "content-length": "1000000",
            }), None)),
            ("file", UploadedFile("blob2.dat", Headers({
                "content-disposition": 'multipart/form-data; name="file"; filename="blob2.dat"',
                "content-length": "1000000",
            }), None)),
            ("file", UploadedFile("blob3.dat", Headers({
                "content-disposition": 'multipart/form-data; name="file"; filename="blob3.dat"',
                "content-length": "1000000",
            }), None)),
        ],
    ),
])
def test_multipart_parsing(fixture, expected):
    with open(f"tests/fixtures/{fixture}", "rb") as f:
        boundary = f.readline().decode()
        data = f.read().replace(b"\n", b"\r\n")

    # These tests use a small bufsize in addition to a FlakyStream in
    # order to attempt to catch boundary parsing errors.
    parser = MultiPartParser(bufsize=128)
    content_type = f"multipart/form-data; boundary={boundary}"
    content_length = len(data)
    stream = FlakyStream(BytesIO(data))

    if isinstance(expected, Exception):
        with pytest.raises(type(expected)) as e_data:
            parser.parse(content_type, content_length, stream)

        assert e_data.value.message == expected.message
        return

    result = parser.parse(content_type, content_length, stream)

    if isinstance(expected, dict):
        assert dict(result) == expected

    else:
        for (lname, lvalue), (rname, rvalue) in zip(result, expected):
            assert lname == rname

            if isinstance(lvalue, str):
                assert lvalue == rvalue

            else:
                assert lvalue.filename == rvalue.filename
                assert list(lvalue.headers) == list(rvalue.headers)

                if rvalue.stream is not None:
                    assert lvalue.read() == rvalue.read()


def test_multipart_parsing_fails_if_given_invalid_content_length():
    # Given that I have a multipart parser
    parser = MultiPartParser()

    # When I call it with a longer content length than the input
    # Then an HTTPError should be raised
    with pytest.raises(ParseError) as e_data:
        parser.parse("multipart/form-data; boundary=--abc", 100, BytesIO())

    assert e_data.value.message == "unexpected end of input"


def test_multipart_parsing_fails_if_given_too_many_fields():
    # Given that I have a multipart parser that accepts at most one field
    parser = MultiPartParser(max_num_fields=1)

    # When I call it with an input that contains multiple fields
    with open("tests/fixtures/multipart_parsing_fields_only.dat", "rb") as f:
        boundary = f.readline().decode()
        data = f.read().replace(b"\n", b"\r\n")
        stream = BytesIO(data)

    # Then TooManyFields should be raised
    with pytest.raises(TooManyFields):
        content_type = f"multipart/form-data; boundary={boundary}"
        parser.parse(content_type, len(data), stream)


def test_multipart_parsing_fails_if_given_files_that_are_too_large():
    # Given that I have a multipart parser that accepts files that are at most 10k large
    parser = MultiPartParser(max_file_size=10 * 1024)

    # When I call it with an input that contains files larger than that
    with open("tests/fixtures/multipart_parsing_long_file.dat", "rb") as f:
        boundary = f.readline().decode()
        data = f.read().replace(b"\n", b"\r\n")
        stream = BytesIO(data)

    # Then FileTooLarge should be raised
    with pytest.raises(FileTooLarge):
        content_type = f"multipart/form-data; boundary={boundary}"
        parser.parse(content_type, len(data), stream)


def test_multipart_parsing_fails_if_given_fields_that_are_too_large():
    # Given that I have a multipart parser that accepts fileds that are at most 100 chars large
    parser = MultiPartParser(max_field_size=100)

    # When I call it with an input that contains a field larger than that
    with open("tests/fixtures/multipart_parsing_long_field.dat", "rb") as f:
        boundary = f.readline().decode()
        data = f.read().replace(b"\n", b"\r\n")
        stream = BytesIO(data)

    # Then FileTooLarge should be raised
    with pytest.raises(FieldTooLarge):
        content_type = f"multipart/form-data; boundary={boundary}"
        parser.parse(content_type, len(data), stream)
