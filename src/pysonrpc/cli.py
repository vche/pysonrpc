import logging
import json
import sys
import traceback
from argparse import ArgumentParser, Namespace
from prettytable import PrettyTable
from typing import Dict, List, Optional

import pysonrpc

log = logging.getLogger(__name__)


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
    parser.add_argument("--method-discover", "-a", default=None, action="store_true", help="Auto discover rpc methods at the specified endpoint url")
    parser.add_argument("--method-discover-path", default=None, help="Specifies a path after the specified endpoint url to query for methods auto discovery")
    parser.add_argument("--method-file", "-f", help="Discover methods from given json file", default=None)
    # json_file
    # auto_discover
    subparsers = parser.add_subparsers(help='commands', dest='command', required=True)

    list_parser = subparsers.add_parser('list', help='List available methods')
    list_parser.add_argument("--full", "-f", default=False, action="store_true", help="Display full description")
    list_parser.add_argument("--method", "-m", default=None, help="Print help for this RPC method only")

    run_parser = subparsers.add_parser('run', help='Execute a method')
    run_parser.add_argument("--method", "-m", default=None, help="RPC method to execute", required=True)
    run_parser.add_argument("--params", "-p", default='{}', help="Optional parameters for the method as json, e.g: '{id:1, name:\"test\"}'")
    run_parser.add_argument("--raw", "-j", default=False, action="store_true", help="Raw json response")

    args = parser.parse_args()
    args.log_level = logging.DEBUG if args.debug else logging.INFO

    return args


def main() -> None:
    """Main entry point."""

    args = _parse_args()
    _setup_logging(level=args.log_level)

    if args.version:
        print(f"pysonrpc version {pysonrpc.__version__}", file=sys.stderr)

    try:
        args.method_discover
        args.method_file
        args.method_discover_path
        cli = pysonrpc.JsonRpcEndpoint(
            args.url,
            user=args.user,
            password=args.password,
            auto_detect=args.method_discover,
            schema_path=args.method_discover_path,
            json_file=args.method_file,
        )

        if args.command == "list":
            if args.full:
                fullprops = {cli.methods[met].fullname: cli.methods[met].properties for met in cli.methods}
                print(json.dumps(fullprops, indent=2))
            else:
                tab = PrettyTable(['Method', 'Parameters', 'Description'])
                tab.align = "l"
                met_list = [cli.methods.get(args.method)] if args.method else cli.methods.values()
                for met in met_list:
                    tab.add_row([met.fullname, met.param_list(), met.description])
                print(tab)

        elif args.command == "run":
            params = json.loads(args.params)
            result=cli.run_method(args.method, **params, raw=args.raw)

            # TODO:
            # check commands like refresh, and get movies and shit
            # better way for parameters ?
            # add a list arg for a method only
            #
            # create kodi wrapper
            # split in a json rpc pkg ?
            # try json definition file and class
            # push both pkg on pip
            # update pyd and panda menu

            # result=cli.Favourites.GetFavourites(raw=args.raw)
            print(json.dumps(result, indent=2))

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
