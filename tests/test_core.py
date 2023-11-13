"""Tests standard tap features using the built-in SDK tests library."""


from singer_sdk.testing import get_tap_test_class

from tap_inventio.tap import TapInventio

# Example tokens from inventio documentation
SAMPLE_CONFIG = {
    "endpoints": {
        "GLENTRY": {
            "companies": {
                "20220422122248574": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
            },
            "limit": 10,
        },
        "DIMENSIONSETENTRY": {
            "companies": {
                "20220422122248574": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
            },
            "limit": 1,
        },
        "CUSTOMER": {
            "companies": {
                "20220422122248574": "{5B3C070F-BD90-4293-84BB-DCBB1E521B54}",
            },
            "limit": 10,
        },
    },
}


# Run standard built-in tap tests from the SDK:
TestTapInventio = get_tap_test_class(
    tap_class=TapInventio,
    config=SAMPLE_CONFIG,
)
