import json
import logging
import sys
import traceback
from argparse import ArgumentParser, Namespace
from typing import Optional

from prettytable import PrettyTable

import pysonrpc

log = logging.getLogger(__name__)


def command_list(cli: pysonrpc.JsonRpcEndpoint, args: Namespace):
    if args.filter:
        met_list = [met for met in cli.methods.values() if args.filter in met.fullname]
    else:
        met_list = cli.methods.values()
    if args.raw:
        fullprops = {met.fullname: met.properties for met in met_list}
        print(json.dumps(fullprops, indent=2))
    else:
        cols = ["Method", "Parameters"] if args.short else ["Method", "Parameters", "Description"]
        tab = PrettyTable(cols)
        tab.align = "l"
        for met in met_list:
            row = [met.fullname, met.param_list()]
            if not args.short:
                row.append(met.description)
            tab.add_row(row)
        print(tab)


def command_run(cli: pysonrpc.JsonRpcEndpoint, args: Namespace):
    params = json.loads(args.params)
    result = cli.run_method(args.method, **params, raw=args.raw)
    print(json.dumps(result, indent=2))


def _setup_logging(level: int = logging.INFO, filename: Optional[str] = None) -> None:
    """Configure standard logging."""
    logging.basicConfig(
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s", level=level, filename=filename
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="RPC client")

    parser.add_argument("--version", "-v", help="Display version", default=False, action="store_true")
    parser.add_argument("--url", "-r", help="Host url, e.g 'http://192.168.0.1:8080'", required=True)
    parser.add_argument("--user", "-u", help="username if using basic authentication", default=None)
    parser.add_argument("--password", "-p", help="Password if using basic authentication", default=None)
    parser.add_argument("--debug", "-d", default=False, action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--schema-discover",
        "-a",
        default=None,
        action="store_true",
        help="Auto discover rpc methods schema at the endpoint url",
    )
    parser.add_argument(
        "--schema-discover-path",
        "-ap",
        default=None,
        help="Auto discover rpc methods schema from this path (relative to the endpoint url)",
    )
    parser.add_argument(
        "--schema-discover-method",
        "-am",
        default=None,
        help="Auto discover rpc methods schema by calling this json rpc method",
    )
    parser.add_argument("--method-file", "-f", help="Discover methods from given json file", default=None)
    # json_file
    # auto_discover
    subparsers = parser.add_subparsers(help="commands", dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List available methods")
    list_parser.add_argument("--raw", "-j", default=False, action="store_true", help="Display full description")
    list_parser.add_argument("--short", "-s", default=False, action="store_true", help="Only display name and params")
    list_parser.add_argument("--filter", "-f", default=None, help="Filter RPC methods names to print")
    list_parser.set_defaults(func=command_list)

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a method")
    run_parser.add_argument("--method", "-m", default=None, help="RPC method to execute", required=True)
    run_parser.add_argument(
        "--params", "-p", default="{}", help="Optional parameters for the method as json, e.g: '{id:1, name:\"test\"}'"
    )
    run_parser.add_argument("--raw", "-j", default=False, action="store_true", help="Raw json response")
    run_parser.set_defaults(func=command_run)

    args = parser.parse_args()
    args.log_level = logging.DEBUG if args.debug else logging.INFO

    return args


def main() -> None:
    """Main entry point."""
    commands = {"list"}

    args = _parse_args()
    _setup_logging(level=args.log_level)

    if args.version:
        print(f"pysonrpc version {pysonrpc.__version__}", file=sys.stderr)

    try:
        cli = pysonrpc.JsonRpcEndpoint(
            args.url,
            user=args.user,
            password=args.password,
            auto_detect=args.schema_discover,
            schema_path=args.schema_discover_path,
            schema_method=args.schema_discover_method,
            json_file=args.method_file,
        )

        if args.func:
            args.func(cli, args)
        else:
            raise pysonrpc.JsonRpcClientError(f"No processing defined for command {args.command}")

        sys.exit(0)
    except pysonrpc.JsonRpcClientError as e:
        print(f"Client error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(2)
