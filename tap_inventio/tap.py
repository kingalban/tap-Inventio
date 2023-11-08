"""Inventio tap class."""

from __future__ import annotations

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
        "endpoints": {
            "GLENTRY": {
                "companies": {
                    "COMPANY1": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
                    "COMPANY2": "{ACLKLLKE-BD90-4293-ALKF-DCBB1E521B54}",
                    "COMPANY3": "{5B3C070F-BD90-4293-84BB-1451AFLKAFKL}"
                }
            },
            "DIMENSIONSETENTRY": {
                "companies": {
                    "COMPANY1": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
                    "COMPANY3": "{5B3C070F-BD90-4293-84BB-1451AFLKAFKL}"
                },
                "limit": 1
            }
        },
        "limit": 100
    }
    ```
    """

    name = "tap-inventio"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "endpoints",
            th.ObjectType(
                *(
                    th.Property(stream.name, th.ObjectType(), required=False)
                    for stream in streams.STREAMS
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

        for endpoint_name, endpoint_config in self.config["endpoints"].items():
            if normalise_name(endpoint_name) not in [
                normalise_name(stream.name) for stream in streams.STREAMS
            ]:
                warnings.append(
                    f"endpoint {endpoint_config} was "
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
            normalise_name(endpoint_name) for endpoint_name in self.config["endpoints"]
        }
        return [
            stream(self)
            for stream in streams.STREAMS
            if normalise_name(stream.name) in available_streams_names or True
        ]


if __name__ == "__main__":
    TapInventio.cli()
