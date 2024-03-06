import pytest
import json
# from copy import deepcopy
from unittest.mock import ANY, call, patch, Mock
from pysonrpc.jsonrpc import JsonRpcClient, JsonRpcEndpoint, JsonRpcClientError, JsonRpcServerError, Method


# @pytest.fixture
# def cli():
#     return RadarrCli(TEST_HOST, TEST_APIKEY)

TEST_URL="http://127.0.0.1:8080/path"
TEST_HEADERS={'Content-Type': 'application/json'}
TEST_METH_PATH="jsonrpc"
TEST_METH_NAME="introspect"
TEST_METH_FILE="test/methods.json"

TEST_METH_LIST_1 ={
	"methods": {
		"some.method": {
			"description": "some method description",
			"params": [
				{ "name": "param1", "required": True, "type": "string" },
				{ "name": "param3", "required": True, "type": "int" },
				{ "$ref": "some.type", "name": "param2" }
			],
			"returns": {
				"properties": {
					"addon": { "$ref": "Addon.Details", "required": True },
					"limits": { "$ref": "List.LimitsReturned", "required": True }
				},
				"type": "object"
			},
			"type": "method"
		},
		"some.method2": {
			"description": "some method2 description",
			"params": [
			],
			"type": "method"
		},
		"some.method3": {
		},
    }
}

TEST_METH_LIST_2 ={
	"methods": {
		"some2.method": {
			"description": "some method description",
			"params": [
				{ "name": "param1", "required": True, "type": "string" },
				{ "name": "param3", "required": True, "type": "int" },
				{ "$ref": "some.type", "name": "param2" }
			],
			"returns": {
				"properties": {
					"addon": { "$ref": "Addon.Details", "required": True },
					"limits": { "$ref": "List.LimitsReturned", "required": True }
				},
				"type": "object"
			},
			"type": "method"
		},
		"some2.method2": {
			"description": "some method2 description",
			"params": [
			],
			"type": "method"
		},
		"some2.method3": {
		},
    }
}
TEST_METH_NLIST_1 = list(TEST_METH_LIST_1['methods'].keys())
TEST_METH_NLIST_2 = list(TEST_METH_LIST_2['methods'].keys())
TEST_METH_NLIST_3 = ["Some3.Method1", "Some3.Method2"]


def mock_response(code, data_dict):
    resp = Mock()
    resp.status_code = code
    resp.json.side_effect = data_dict
    return resp

def mock_endpoint(mock_post, mock_get, url=None, **kwargs):
    return JsonRpcEndpoint(
        url or TEST_URL,
        user=kwargs.get("user"),
        password=kwargs.get("password"),
        schema=kwargs.get("schema"),
        auto_detect=kwargs.get("auto_detect", False),
        schema_path=kwargs.get("schema_path"),
        schema_method=kwargs.get("schema_method"),
        json_file=kwargs.get("json_file"),
    )

@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_no_auth(mock_post, mock_get):
    mock_get.return_value = mock_response(200, ["some response"])
    cli = mock_endpoint(mock_post, mock_get)
    assert cli.methods == {}
    assert cli.client.get() == "some response"
    mock_get.assert_called_with(TEST_URL, headers=TEST_HEADERS, auth=None)


@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_auth(mock_post, mock_get):
    mock_get.return_value = mock_response(200, ["some response"])     
    cli = mock_endpoint(mock_post, mock_get, user="user", password="pass")
    assert cli.client.get() == "some response"
    mock_get.assert_called_with(TEST_URL, headers=TEST_HEADERS, auth=cli.client._auth)
    assert cli.client._auth.username == "user"
    assert cli.client._auth.password == "pass"


@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_get_error(mock_post, mock_get):
    mock_get.side_effect = Exception("error")
    cli = mock_endpoint(mock_post, mock_get)
    with pytest.raises(JsonRpcClientError):
        cli.client.get()


@pytest.mark.parametrize(
    "auto, path, method, file, expect", [
    (True, None, None, None, TEST_METH_LIST_1['methods'].keys()),
    (False, TEST_METH_PATH, None, None, TEST_METH_NLIST_1),
    (False, None, TEST_METH_NAME, None, TEST_METH_NLIST_2),
    (False, None, None, TEST_METH_FILE, TEST_METH_NLIST_3),
    (True, TEST_METH_PATH, TEST_METH_NAME, TEST_METH_FILE, TEST_METH_NLIST_2+TEST_METH_NLIST_3),
    (True, TEST_METH_PATH, None, TEST_METH_FILE, TEST_METH_NLIST_1+TEST_METH_NLIST_3),
])
@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_schema(mock_post, mock_get, auto, path, method, file, expect):
    mock_get.return_value = mock_response(200, [TEST_METH_LIST_1])
    mock_post.return_value = mock_response(200, [{ JsonRpcClient.JSONRPC_KEY_RESP_RESULT: TEST_METH_LIST_2}])
    cli = mock_endpoint(mock_post, mock_get, auto_detect=auto, schema_path=path, schema_method=method, json_file=file)

    for key in expect:
        assert key in cli.methods.keys()
    assert len(expect) == len(cli.methods)

@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_attribute_method(mock_post, mock_get):
    methods = {
	    "methods": {
            "some.cool.thing": {},
            "some.bad.withparam": {"params": [{ "name": "param1"},{ "name": "param2"}]},
            "some.cool.alsowithparams": {"params": [{ "name": "param4"},{ "name": "param5"}]},
        }
    }
    pl = { JsonRpcClient.JSONRPC_KEY_RESP_RESULT: "data"}
    mock_post.return_value = mock_response(200, [pl, pl, pl, pl])
    cli = mock_endpoint(mock_post, mock_get, schema=methods)

    assert cli.some.cool.thing() == {"result": "data"}
    assert cli.some.cool.thing(raw = False) == "data"
    assert cli.some.bad.withparam(param1="a", param2="b") == {"result": "data"}
    assert cli.some.cool.alsowithparams(param4="c", param5="d", raw = False) == "data"

    pl1 = { "jsonrpc": "2.0", "method": "some.cool.thing", "params": {}, "id": ANY}
    pl2 = { "jsonrpc": "2.0", "method": "some.bad.withparam", "params": {"param1": "a", "param2": "b"}, "id": ANY}
    pl3 = { "jsonrpc": "2.0", "method": "some.cool.alsowithparams", "params": {"param4": "c", "param5": "d"}, "id": ANY}
    calls = [
        call(TEST_URL, headers=TEST_HEADERS, json=pl1, auth=None),
        call(TEST_URL, headers=TEST_HEADERS, json=pl2, auth=None),
        call(TEST_URL, headers=TEST_HEADERS, json=pl3, auth=None),
    ]
    mock_post.assert_has_calls(calls, any_order=True)

    with pytest.raises(AttributeError):
        cli.some.notcool.thing()


@pytest.mark.parametrize(
    "sideffect, exc", [
    (Exception(), JsonRpcClientError),
    ([None], JsonRpcServerError),
    ([mock_response(200, json.JSONDecodeError("ee", "ee", 21))], JsonRpcServerError),
])
@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_method_error(mock_post, mock_get, sideffect, exc):
    pl = { JsonRpcClient.JSONRPC_KEY_RESP_RESULT: "data"}
    # mock_post.side_effect = Exception() // JsonRpcClientError
    # mock_post.side_effect = [None] // JsonRpcServerError 
    # mock_post.return_value = mock_response(200, json.JSONDecodeError("ee", "ee", 21))
    mock_post.side_effect = sideffect
    cli = mock_endpoint(mock_post, mock_get)
    with pytest.raises(exc):
        cli.run_method("method")


@patch("pysonrpc.jsonrpc.requests.get")
@patch("pysonrpc.jsonrpc.requests.post")
def test_client_run_method(mock_post, mock_get):
    pl = { JsonRpcClient.JSONRPC_KEY_RESP_RESULT: "data"}
    mock_post.return_value = mock_response(200, [pl, pl, pl, pl])
    cli = mock_endpoint(mock_post, mock_get)

    assert cli.run_method("method", raw = True) == {"result": "data"}
    assert cli.run_method("some.cool.thing", raw = False) == "data"
    assert cli.run_method("some.bad.withparam", param1="a", param2="b") == {"result": "data"}

    pl1 = { "jsonrpc": "2.0", "method": "method", "params": {}, "id": ANY}
    pl3 = { "jsonrpc": "2.0", "method": "some.cool.thing", "params": {}, "id": ANY}
    pl2 = { "jsonrpc": "2.0", "method": "some.bad.withparam", "params": {"param1": "a", "param2": "b"}, "id": ANY}
    calls = [
        call(TEST_URL, headers=TEST_HEADERS, json=pl1, auth=None),
        call(TEST_URL, headers=TEST_HEADERS, json=pl2, auth=None),
        call(TEST_URL, headers=TEST_HEADERS, json=pl3, auth=None),
    ]
    mock_post.assert_has_calls(calls, any_order=True)
