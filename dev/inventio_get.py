#! /usr/bin/env python
"""Get response from Inventio API and format as json."""

from __future__ import annotations

import argparse
import json
import sys

import requests
import xmltodict


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def get(url) -> dict:
    return xmltodict.parse(requests.get(url).content)


def main(argv: str | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="complete url query")
    parser.add_argument("-c", "--company", help="company")
    parser.add_argument("-t", "--type", help="the 'type' of endpoint")
    parser.add_argument("-k", "--token", help="endpoint token")
    parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        help="pretty format as indented json",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="limit the response from the API",
    )

    args = parser.parse_args(argv)
    exit_code = 0

    if not bool(args.url) ^ bool(
        args.company and args.type and args.token,
    ):  # xor (^) means choose one
        msg = "Too many arguments. Supply only --url, or all of --company, --type, and --token"
        raise ValueError(msg)

    limit_str = f"&limit={args.limit}" if args.limit else ""

    url = (
        args.url
        or f"https://app.cloud.inventio.it/{args.company}/smartapi/?type={args.type}&token={args.token}{limit_str}"
    )
    log(f"getting from {url!r}")

    content_json = get(url)

    if "error" in content_json:
        log(f"error: {content_json}")
        exit_code = 1

    try:
        print(
            json.dumps(
                content_json,
                **({"indent": 2, "default": str} if args.pretty else {}),
            ),
        )

    except json.JSONDecodeError as e:
        log(f"failed to parse result json: {e}")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
