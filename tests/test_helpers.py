import pytest

from molten import HTTP_301, HTTP_302, HTTP_307, HTTP_308
from molten.helpers import RedirectType, redirect


@pytest.mark.parametrize("location,redirect_type,use_modern_codes,expected_status", [
    ("https://example.com", RedirectType.TEMPORARY, False, HTTP_302),
    ("https://example.com", RedirectType.TEMPORARY, True, HTTP_307),
    ("https://example.com", RedirectType.PERMANENT, False, HTTP_301),
    ("https://example.com", RedirectType.PERMANENT, True, HTTP_308),
])
def test_redirect(location, redirect_type, use_modern_codes, expected_status):
    response = redirect(location, redirect_type=redirect_type, use_modern_codes=use_modern_codes)
    assert response.status == expected_status
    assert response.headers["Location"] == location
