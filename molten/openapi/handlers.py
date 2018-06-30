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

from typing import Any, Dict, List, Optional

from ..app import BaseApp
from .documents import Metadata, SecurityScheme, generate_openapi_document


class OpenAPIHandler:
    """Dynamically generates and serves OpenAPI v3 documents based on
    the current application object.  Once generated, the document is
    subsequently served from cache.

    Examples:

      >>> get_schema = OpenAPIHandler(
      ...   metadata=Metadata(title="Pet Store", version="0.1.0"),
      ...   security_schemes=[HTTPSecurityScheme("Bearer", "bearer")],
      ...   default_security_scheme="Bearer",
      ... )

    Parameters:
      metadata: Various meta-information about the current API.
      security_schemes: A list of security schemes used throughout the
        API.
    """

    __slots__ = [
        "metadata",
        "security_schemes",
        "default_security_scheme",
        "document",
    ]

    def __init__(
            self,
            metadata: Metadata,
            security_schemes: Optional[List[SecurityScheme]] = None,
            default_security_scheme: Optional[str] = None,
    ) -> None:
        self.metadata = metadata
        self.security_schemes = security_schemes or []
        self.default_security_scheme = default_security_scheme
        self.document: Optional[Dict[str, Any]] = None

    def __call__(self, app: BaseApp) -> Optional[Dict[str, Any]]:
        """Generates an OpenAPI v3 document.
        """
        if not self.document:
            self.document = generate_openapi_document(
                app,
                self.metadata,
                self.security_schemes,
                self.default_security_scheme,
            )

        return self.document
