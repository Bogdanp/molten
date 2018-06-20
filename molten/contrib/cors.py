# This file is a part of molten.
#
# Copyright (C) 2018 CLEARTYPE SRL <bogdan@cleartype.io>
#
# molten is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# molten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    from wsgicors import CORS
except ImportError:  # pragma: no cover
    raise ImportError("'wsgicors' package missing. Run 'pip install wsgicors'.")


def make_cors_mixin(**options):
    """Generate a CORS mixin class with custom options.  All keyword
    arguments are passed to wsgicors.CORS.
    """
    class CORSMixin:
        def __call__(self, environ, start_response, exc_info=None):
            cors = CORS(super().__call__, **options)
            return cors(environ, start_response)

    return CORSMixin


#: A generic CORS mixin for molten apps.
CORSMixin = make_cors_mixin(headers="*", methods="*", maxage="86400", origin="*")
