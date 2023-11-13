"""REST client handling, including InventioStream base class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, TypedDict

import xmltodict
from singer_sdk.exceptions import FatalAPIError
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk.streams import RESTStream

if TYPE_CHECKING:
    import requests
    from typing_extensions import NotRequired

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class EndpointConfig(TypedDict):
    """Basic shape of the configuration for each tap.

    'companies' is a dict mapping company names to tokens.
    """

    companies: dict[str, str]
    limit: NotRequired[int]


class PaginatorResponse(TypedDict):
    """Format of the paginator response. Each 'page' is a company token pair."""

    company_name: str
    token: str


def normalise_name(name: str) -> str | None:
    """Normalise endpoint names.

    eg: 'GLEntry-GET'   -> GLENTRY
        'ITEM-POST'     -> None (don't work with post endpoints).
    """
    if name.upper().endswith("-POST"):
        return None
    return name.upper().removesuffix("-GET")


class CompanyAPIPaginator(BaseAPIPaginator):
    """Paginates over a list of companies (yes, very odd).

    The inventio api doesn't have page-pagination,
    but we want to get data for many companies.
    """

    def __init__(self, start_value: dict[str, str]) -> None:
        """Create a new paginator.

        Args:
            start_value: Initial value.
        """
        self._companies_and_keys = iter(start_value.items())
        company_name, token = next(self._companies_and_keys)
        super().__init__({"company_name": company_name, "token": token})

    def get_next(
        self,
        response: requests.Response,  # noqa: ARG002
    ) -> PaginatorResponse | None:
        """Get the next pagination token or index from the API response.

        Args:
            response: API response object.

        Returns:
            The next page token or index. Return `None` from this method to indicate
                the end of pagination.
        """
        try:
            company_name, token = next(self._companies_and_keys)
            self._page_count += 1

        except StopIteration:
            return None

        else:
            return {"company_name": company_name, "token": token}


class InventioStream(RESTStream):
    """Inventio stream class."""

    # path is required by design of the RESTStream. it is not used
    path = None

    _current_company_name: str | None = None

    forced_replication_method = (
        "FULL_TABLE"  # Currently no stream has state implemented
    )

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # Note that '{company_name}' will be replaced by values found in
        # context and config by the function 'get_url()'
        # (and 'next_page_token' by 'prepare_request()')
        return "https://app.cloud.inventio.it/{company_name}/smartapi/"

    @property
    def schema_filepath(self) -> Path | None:
        """Get path to schema file.

        Returns:
            Path to a schema file for the stream or `None` if n/a.
        """
        return SCHEMAS_DIR / f"{self.name}.schema.json"

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    @property
    def endpoint_config(self) -> EndpointConfig | None:
        """The config that corresponds only to this endpoint (or None)."""
        for endpoint_name, config in self.config["endpoints"].items():
            if normalise_name(endpoint_name) == normalise_name(self.name):
                return config
        return None

    @property
    def selected_by_default(self) -> bool:
        """Selected by default in singer catalog if there is an available config."""
        return self.endpoint_config is not None

    def get_new_paginator(self) -> CompanyAPIPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide: https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        if self.endpoint_config:
            return CompanyAPIPaginator(self.endpoint_config["companies"])
        msg = f"failed to generate paginator because {self.name} was not configured"
        raise ValueError(msg)

    def get_url_params(
        self,
        context: dict | None,  # noqa: ARG002
        next_page_token: PaginatorResponse,
    ) -> dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The company_name and matching token

        Returns:
            A dictionary of URL query parameters.
        """
        # keep track of the company to label the rows
        self._current_company_name = next_page_token["company_name"]

        params: dict = {
            "type": f"{self.name}-GET",
            "token": next_page_token["token"],
        }

        if self.endpoint_config is None:
            msg = (
                f"failed to generate url params because {self.name} was not configured"
            )
            raise ValueError(msg)

        if limit := (self.endpoint_config.get("limit") or self.config.get("limit")):
            params["limit"] = limit

        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key

        return params

    def prepare_request(
        self,
        context: dict | None,
        next_page_token: PaginatorResponse,
    ) -> requests.PreparedRequest:
        """Prepare a request object for this stream.

        If partitioning is supported, the `context` object will contain the partition
        definitions. Pagination information can be parsed from `next_page_token` if
        `next_page_token` is not None.

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token, page number or any request argument to request the
                next page of data.

        Returns:
            Build a request with the stream's URL, path, query parameters,
            HTTP headers and authenticator.
        """
        http_method = self.rest_method
        # The 'next_page_token' actually contains the company_name
        url: str = self.get_url({**(context or {}), **next_page_token})
        params: dict | str = self.get_url_params(context, next_page_token)
        request_data = self.prepare_request_payload(context, next_page_token)
        headers = self.http_headers

        return self.build_prepared_request(
            method=http_method,
            url=url,
            params=params,
            headers=headers,
            json=request_data,
        )

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        json_response = xmltodict.parse(response.content)

        if "error" in json_response:
            # Inventio does NOT respect normal HTTP status codes, everything is 200
            response.reason = f"{json_response['error']}"
            self.path = self.name  # So the endpoint will be printed in the error
            raise FatalAPIError(self.response_error_message(response))

        if not self.records_jsonpath:
            msg = "'records_jsonpath' must be specified"
            raise NotImplementedError(msg)

        yield from extract_jsonpath(self.records_jsonpath, input=json_response)

    def post_process(
        self,
        row: dict,
        context: dict | None = None,  # noqa: ARG002
    ) -> dict | None:
        """As needed, append or transform raw data to match expected structure.

        Args:
            row: An individual record from the stream.
            context: The stream context.

        Returns:
            The updated record dictionary, or ``None`` to skip the record.
        """
        row["company_name"] = self._current_company_name
        return {key.replace("-", "_"): val for key, val in row.items()}
