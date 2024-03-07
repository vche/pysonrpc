import pytest
import sys
import json
from unittest.mock import ANY, call, patch, Mock
from pysonrpc.cli import main as cli_main
from pysonrpc.jsonrpc import Method

TEST_HOST="http://1.2.3.4:1234"

@pytest.fixture
def mock_exit(monkeypatch):
    exit = Mock()
    monkeypatch.setattr(sys, "exit", exit)
    return exit


@patch("pysonrpc.cli.pysonrpc.JsonRpcEndpoint")
def test_cli_list_raw(mock_endpoint, monkeypatch, mock_exit):
    test_args = [
        "pysonrpc",
        "--version",
        "-r", TEST_HOST,
        "list",
        "--raw",
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    mock_endpoint().methods = {}

    cli_main()
    mock_endpoint.assert_called_with(
        TEST_HOST,
        user=None,
        password=None,
        auto_detect=False,
        schema_path=None,
        schema_method=None,
        json_file=None,
    )
    mock_exit.assert_called_with(0)


@pytest.mark.parametrize("short", [True, False])
@patch("pysonrpc.cli.pysonrpc.JsonRpcEndpoint")
def test_cli_list_filter(mock_endpoint, short, monkeypatch, mock_exit):
    test_args = [
        "pysonrpc",
        "--version",
        "-r", TEST_HOST,
        "list",
        "--filter",
        "some.cool",
    ]
    if short:
        test_args.append("--short")
    monkeypatch.setattr(sys, "argv", test_args)
    mock_endpoint().methods = {
        "some.cool.thing":
            Method(name="some.cool.thing"),
        "some.bad.withparam": 
            Method(name="some.bad.withparam", properties = {"params": [{ "name": "param1"},{ "name": "param2"}]}),
        "some.cool.alsowithparams":
            Method(name="some.cool.alsowithparams", properties = {"params": [{ "name": "param4"},{ "name": "param5"}]}),
    }

    cli_main()
    mock_endpoint.assert_called_with(
        TEST_HOST,
        user=None,
        password=None,
        auto_detect=False,
        schema_path=None,
        schema_method=None,
        json_file=None,
    )
    mock_exit.assert_called_with(0)
 

@pytest.mark.parametrize(
    "method, params, expanded", [
        ("some.method", None, {}),
        ("other.method", '{"movieid": 1419}', {"movieid": 1419}),
    ]
)
@patch("pysonrpc.cli.pysonrpc.JsonRpcEndpoint")
def test_cli_run_raw(mock_endpoint, method, params, expanded, monkeypatch, mock_exit):
    test_args = [
        "pysonrpc",
        "--version",
        "-r", TEST_HOST,
        "run",
        "--raw",
        "-m",
        method,
    ]
    if params:
        test_args.append("-p")
        test_args.append(params)
    monkeypatch.setattr(sys, "argv", test_args)
    mock_endpoint().methods = {}
    mock_endpoint().run_method.return_value = {}

    cli_main()
    mock_endpoint.assert_called_with(
        TEST_HOST,
        user=None,
        password=None,
        auto_detect=False,
        schema_path=None,
        schema_method=None,
        json_file=None,
    )

    mock_endpoint().run_method.assert_called_with(method, **expanded, raw=True)
    mock_exit.assert_called_with(0)


@pytest.mark.parametrize("debug", [True, False])
@patch("pysonrpc.cli.pysonrpc.JsonRpcEndpoint")
def test_cli_invalid_command(mock_endpoint, debug, monkeypatch, mock_exit):
    test_args = [
        "pysonrpc",
        "-d",
        "-r", TEST_HOST,
        "bad",
    ]
    if not debug:
        test_args.pop(1)
    monkeypatch.setattr(sys, "argv", test_args)
    mock_endpoint().methods = {}

    cli_main()
    mock_endpoint.assert_called_with(
        TEST_HOST,
        user=None,
        password=None,
        auto_detect=False,
        schema_path=None,
        schema_method=None,
        json_file=None,
    )

    mock_exit.assert_called_with(1)


@pytest.mark.parametrize("debug", [True, False])
@patch("pysonrpc.cli.pysonrpc.JsonRpcEndpoint")
def test_cli_invalid_cli(mock_endpoint, debug, monkeypatch, mock_exit):
    test_args = [
        "pysonrpc",
        "-d",
        "-r", TEST_HOST,
        "bad",
    ]
    if not debug:
        test_args.pop(1)
    monkeypatch.setattr(sys, "argv", test_args)
    mock_endpoint.side_effect = Exception()

    cli_main()
    mock_exit.assert_called_with(2)