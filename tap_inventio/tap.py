"""Inventio tap class."""

from __future__ import annotations

from collections import Counter

from singer_sdk import Tap
from singer_sdk import typing as th
from singer_sdk.exceptions import ConfigValidationError

from tap_inventio import streams
from tap_inventio.client import normalise_name


class TapInventio(Tap):
    """Inventio tap class.

    Endpoints and companies are specified like so:
    ```
    {
    "endpoints": [
    {
    "endpoint": "GLENTRY",
    "companies": {
    "COMPANY1": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
    "COMPANY2": "{ACLKLLKE-BD90-4293-ALKF-DCBB1E521B54}",
    "COMPANY3": "{5B3C070F-BD90-4293-84BB-1451AFLKAFKL}"
    }
    },
    {
    "endpoint": "DIMENSIONSETENTRY",
    "companies": {
    "COMPANY1": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
    "COMPANY3": "{5B3C070F-BD90-4293-84BB-1451AFLKAFKL}"
    },
    "limit": 1
    }
    ],
    "limit": 100
    }
    ```
    """

    name = "tap-inventio"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "endpoints",
            th.ArrayType(
                th.ObjectType(
                    th.Property("endpoint", th.StringType, required=True),
                    th.Property(
                        "companies",
                        th.ObjectType(additional_properties=th.StringType),
                        required=True,
                    ),
                    th.Property("limit", th.IntegerType, required=False),
                    additional_properties=True,  # Some streams need additional config
                ),
            ),
            required=True,
            secret=True,  # Flag config as protected.
            description="A mapping of (endpoints -> (companies -> keys))",
        ),
        th.Property(
            "user_agent",
            th.StringType,
            description="user agent to present as",
        ),
        th.Property(
            "limit",
            th.IntegerType,
            description="number of records to get from each endpoint",
        ),
        th.Property(
            "start_date",
            th.DateType,
            description="earliest day to retrieve (only applicable for AccountScheduleResult)",
        ),
    ).to_dict()

    def _validate_config(
        self,
        *,
        raise_errors: bool = True,
        warnings_as_errors: bool = False,
    ) -> tuple[list[str], list[str]]:
        warnings, errors = super()._validate_config(
            raise_errors=raise_errors,
            warnings_as_errors=warnings_as_errors,
        )

        endpoint_counts = Counter(
            normalise_name(conf["endpoint"]) for conf in self.config["endpoints"]
        )

        for endpoint, count in endpoint_counts.most_common():
            if count > 1 and endpoint is not None:
                errors.append(
                    f"endpoint {endpoint!r} was configured more than once! ({count} times)",
                )

        for configured_endpoint in endpoint_counts:
            if configured_endpoint not in [
                normalise_name(stream.name) for stream in streams.STREAMS
            ]:
                warnings.append(
                    f"endpoint {configured_endpoint} was "
                    f"configured but is not available from this tap",
                )

        if errors:
            error_str = ";\n".join(errors)
            msg = f"Config validation failed: {error_str}"
            raise ConfigValidationError(msg)

        return warnings, errors

    def discover_streams(self) -> list[streams.InventioStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        available_streams_names = {
            normalise_name(endpoint["endpoint"])
            for endpoint in self.config["endpoints"]
        }
        return [
            stream(self)
            for stream in streams.STREAMS
            if normalise_name(stream.name) in available_streams_names or True
        ]


if __name__ == "__main__":
    TapInventio.cli()
