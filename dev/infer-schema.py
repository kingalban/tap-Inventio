#! /usr/bin/env python
""" Natively infer the top level schema from of an Inventio stream

    Inventio records are commonly flat objects with string values.
    Any item which appears to only be null is assumed to possibly
    be a string
"""

from __future__ import annotations

import sys
import json
import argparse
from collections import defaultdict


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def serialize(obj):
    if isinstance(obj, set):
        return serialize(list(obj))

    if obj == ["null"]:
        # null by itself is not useful, add str by default
        return ["null", "string"]

    return obj


def get_record(line: str, *, is_singer_format=False) -> dict | None:
    try:
        record = json.loads(line)

        if not isinstance(record, dict):
            log(f"row doesn't look like a record: {line!r}")
            return None

        if not is_singer_format:
            return record

        if record.get("type") == "RECORD":
            return record.get("record")

    except json.JSONDecodeError as err:
        log(f"failed to pass {line!r}, error: {err}")

    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--pretty", action="store_true", help="pretty print schema"
    )
    parser.add_argument("-r", "--required", nargs="+", help="required keys")
    parser.add_argument(
        "-s",
        "--singer-style",
        action="store_true",
        help="are records coming straight from the tap? extract only record content",
    )

    args = parser.parse_args()

    properties = defaultdict(lambda: {"type": {"null"}})

    schema = {"type": "object", "properties": properties}

    for line in sys.stdin.read().split("\n"):
        if line:
            record = get_record(line, is_singer_format=args.singer_style)

            if not record:
                continue

            else:
                for key, value in record.items():
                    if isinstance(value, dict):
                        _type = "object"

                    elif isinstance(value, list):
                        _type = "array"

                    elif isinstance(value, (int, float)):
                        _type = "number"

                    elif isinstance(value, bool):
                        _type = "bool"

                    elif value is None:
                        _type = "null"

                    else:  # string is the default type
                        _type = "string"

                    schema["properties"][key]["type"].add(_type)

    if args.required:
        schema["required"] = {"company_name"} | set(args.required)
        for key in schema["required"]:
            if key not in schema["properties"]:
                raise ValueError(
                    f"required property {key!r} was not found in object keys {list(schema['properties'])}"
                )

    print(json.dumps(schema, default=serialize, indent=(2 if args.pretty else None)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
