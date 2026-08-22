from __future__ import annotations

import argparse
import json


def build_parser():

    parser = argparse.ArgumentParser(
        prog="research-agent"
    )

    sub = parser.add_subparsers(
        dest="command"
    )


    run = sub.add_parser(
        "run"
    )

    run.add_argument(
        "--hypothesis",
        required=True,
    )

    run.add_argument(
        "--target",
        required=True,
    )


    return parser



def main():

    parser = build_parser()

    args = parser.parse_args()


    if args.command == "run":

        output = {
            "status": "READY",
            "hypothesis_id":
                args.hypothesis,
            "target":
                args.target,
        }


        print(
            json.dumps(
                output,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
