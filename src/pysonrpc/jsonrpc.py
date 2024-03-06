import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

import requests

log = logging.getLogger(__name__)


class JsonRpcError(Exception):
    pass


class JsonRpcClientError(JsonRpcError):
    pass


class JsonRpcServerError(JsonRpcError):
    pass


class JsonRpcClient:
    """Implementation of a json rpc client."""

    # RPC message config
    JSONRPC_VERSION = "2.0"
    JSONRPC_CONTENT = "application/json"

    # Defined error codes
    JSONRPC_PARSE_ERROR = -32700
    JSONRPC_INVALID_REQUEST = -32600
    JSONRPC_METHOD_NOT_FOUND = -32601
    JSONRPC_INVALID_PARAMS = -32602
    JSONRPC_INTERNAL_ERROR = -32603
    # SERVER_ERROR = -32000 to -32099

    # jsonrpc dictionnary keys
    JSONRPC_KEY = "jsonrpc"
    JSONRPC_KEY_ID = "id"
    JSONRPC_KEY_REQ_METHOD = "method"
    JSONRPC_KEY_REQ_PARAMS = "params"
    JSONRPC_KEY_RESP_RESULT = "result"
    JSONRPC_KEY_RESP_ERROR = "error"
    JSONRPC_KEY_RESP_ERROR_CODE = "code"
    JSONRPC_KEY_RESP_ERROR_MSG = "message"
    JSONRPC_KEY_RESP_ERROR_DATA = "data"

    def __init__(self, url, user: Optional[str] = None, password: Optional[str] = None) -> None:
        self._url = url
        self._auth = self._build_credentials(user, password)

    def _build_credentials(self, user: Optional[str], password: Optional[str]) -> Optional[Any]:
        """Build http basic auth credentials per default."""
        if user and password:
            return requests.auth.HTTPBasicAuth(user, password)
        return None

    def _random_id(self) -> str:
        return uuid.uuid4().hex

    def _build_jsonrpc_payload(
        self, method: str, params: Dict[str, Any] = {}, req_id: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """Create JSON-RPC payload."""
        return {
            self.JSONRPC_KEY: self.JSONRPC_VERSION,
            self.JSONRPC_KEY_REQ_METHOD: method,
            self.JSONRPC_KEY_REQ_PARAMS: params,
            self.JSONRPC_KEY_ID: req_id or self._random_id(),
        }

    def _parse_response(self, response: requests.Response, raw: bool = True) -> Dict[str, Any]:
        """Extract json result from response upon success or raise an exception."""
        if response is not None:
            if response.status_code == 200:
                try:
                    raw_json = response.json()
                    return raw_json if raw else self.jsonrpc_result(raw_json)
                except json.JSONDecodeError as e:
                    raise JsonRpcServerError(f"Invalid json response: {response.text}") from e

            raise JsonRpcServerError(f"Couldn't get data response code {response.status_code}: {response.reason}")
        raise JsonRpcServerError(f"Couldn't get response from server: {response}")

    def get(self, path: Optional[str] = None, headers: Dict[str, str] = {}) -> Dict[str, Any]:
        """Send a get requests to the server."""
        headers.update(
            {
                "Content-Type": self.JSONRPC_CONTENT,
            }
        )

        # Make the JSON-RPC request using the requests library
        url = f"{self._url}/{path}" if path else self._url
        log.debug(f"JSON RPC get to {url}")
        try:
            response = requests.get(url, headers=headers, auth=self._auth)
        except Exception as e:
            raise JsonRpcClientError(f"Request error: {e}") from e

        return self._parse_response(response)

    def request(
        self,
        method,
        params={},
        req_id: Optional[Union[int, str]] = None,
        headers: Dict[str, str] = {},
        raw: bool = True,
    ) -> Dict[str, Any]:
        """Sends a json rpc request, with optional headers and id and return the json result or the raw response."""
        payload = self._build_jsonrpc_payload(method, params, req_id)
        headers.update(
            {
                "Content-Type": self.JSONRPC_CONTENT,
            }
        )

        # Make the JSON-RPC request using the requests library
        log.debug(f"JSON RPC request to {self._url}: {payload}")
        try:
            response = requests.post(self._url, json=payload, headers=headers, auth=self._auth)

        except Exception as e:
            raise JsonRpcClientError(f"Request error: {e}") from e

        return self._parse_response(response, raw)

    def jsonrpc_error(
        self, error: int, message: str, data: Optional[Any] = None, req_id: Optional[int] = None
    ) -> Dict[str, Any]:
        error_message = {
            self.JSONRPC_KEY: self.JSONRPC_VERSION,
            self.JSONRPC_KEY_ID: req_id,
            self.JSONRPC_KEY_RESP_ERROR: {
                self.JSONRPC_KEY_RESP_ERROR_CODE: error,
                self.JSONRPC_KEY_RESP_ERROR_MSG: message,
            },
        }
        if data:
            error_message[self.JSONRPC_KEY_RESP_ERROR][self.JSONRPC_KEY_RESP_ERROR_DATA] = data  # type: ignore
        return error_message

    def jsonrpc_result(self, response: Dict[str, Any]) -> Dict[str, Any]:
        if self.JSONRPC_KEY_RESP_RESULT in response:
            return response[self.JSONRPC_KEY_RESP_RESULT]
        elif self.JSONRPC_KEY_RESP_ERROR in response and isinstance(response[self.JSONRPC_KEY_RESP_ERROR], dict):
            raise JsonRpcServerError(response[self.JSONRPC_KEY_RESP_ERROR].get(self.JSONRPC_KEY_RESP_ERROR_MSG))
        else:
            raise JsonRpcServerError(f"Invalid json rpc response: {response}")


class MethodContainer:
    """Base class to provides a method list and attributes for those method names."""

    _child_methods: Dict[str, Any] = {}

    @property
    def child_methods(self) -> Dict[str, Any]:
        return self._child_methods

    def _execute(self) -> Any:
        """Returns the element to assign to the class attribute with named this method."""
        return self

    def __getattr__(self, name: str) -> Any:
        """If the request attribute doesn't exist, check if it's a method name and get its element if it is."""
        if name in self.child_methods:
            return self.child_methods[name]._execute()
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class Method(MethodContainer):
    """Wraps a jsonrpc method description, information, and execution."""

    # JSON Schema properties
    PROP_DESC = "description"
    PROP_PARAMS = "params"
    PROP_RETURNS = "returns"
    PROP_PARAM_NAME = "name"
    NAMESPACE_SEP = "."

    def __init__(self, name, properties={}, exec: bool = True, client: Optional[JsonRpcClient] = None) -> None:
        self._fullname = name
        self._parents = name.split(self.NAMESPACE_SEP)
        self._name = self._parents.pop()
        self._properties = properties or {}
        self._exec = exec
        self._client = client

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}:{self.name}{self.param_list()}"

    def _execute(self) -> Any:
        """Overrides affectation to return itself if only a namespace, or the execution if a actual method."""
        return self.run if self._exec else self

    def run(self, *args, raw=True, **kwargs) -> Dict[str, Any]:
        """Executes this method."""
        if self._client:
            return self._client.request(method=self._fullname, params=kwargs, raw=raw)
        return {}

    def param_list(self) -> List[str]:
        return [param.get(self.PROP_PARAM_NAME) for param in self.params]

    @property
    def fullname(self):
        return self._fullname

    @property
    def parents(self):
        return self._parents

    @property
    def name(self):
        return self._name

    @property
    def properties(self):
        return self._properties

    @property
    def description(self):
        return self._properties.get(self.PROP_DESC)

    @property
    def params(self):
        return self._properties.get(self.PROP_PARAMS, {})

    @property
    def returns(self):
        return self._properties.get(self.PROP_RETURNS)


class JsonRpcEndpoint(MethodContainer):
    """Create a jsonrpc endpoint with methods dynamically defined based on the json schema definition,
    or a list of manually created ones.
    """

    def __init__(
        self,
        url,
        user: Optional[str] = None,
        password: Optional[str] = None,
        json_file: Optional[str] = None,
        schema_path: Optional[str] = None,
        schema_method: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        auto_detect: Optional[bool] = False,
    ) -> None:
        # Create rpc client
        self.client = JsonRpcClient(url, user, password)
        self._methods: Dict[str, Any] = {}

        # Load methods definition from all defined source: Manual, dict, file, urlx
        methods_list = []
        if json_file:
            methods_list.extend(self._methods_from_file(json_file))
        if schema_method or schema_path or auto_detect:
            methods_list.extend(self._methods_from_url(path=schema_path, method=schema_method))
        if schema:
            methods_list.extend(self._methods_from_dict(schema))

        # Create method hierarachy
        self._add_methods(methods_list)

    @property
    def methods(self):
        return self._methods

    def _add_methods(self, methods_list):
        """From the method list, build direct access list and tree:
        - populate a dict for direct access based on fullname,
        - build a tree based on namespace with leaf being the executable methods
        """

        for method in methods_list:
            parent_node = self.child_methods
            # Create all parent nodes
            for ns in method.parents:
                node = parent_node.setdefault(ns, Method(ns, exec=False))
                parent_node = node.child_methods
            # Add actual method
            parent_node[method.name] = method
            self._methods[method.fullname] = method

    def _methods_from_dict(self, json_schema: Optional[Dict[str, Any]]) -> List[Method]:
        methods = []

        if json_schema and "methods" in json_schema:
            for method_name, method_props in json_schema["methods"].items():
                methods.append(Method(method_name, method_props, client=self.client))
        return methods

    def _methods_from_file(self, json_file: str) -> List[Method]:
        with open(json_file, "r") as fp:
            return self._methods_from_dict(json.load(fp))

    def _methods_from_url(self, path: Optional[str], method: Optional[str]) -> List[Method]:
        if method:
            json_schema = self.client.request(method=method, raw=False)
        else:
            json_schema = self.client.get(path)
        return self._methods_from_dict(json_schema)

    def run_method(self, method, *args, raw: bool = True, **kwargs) -> Dict[str, Any]:
        if self.client:
            return self.client.request(method=method, params=kwargs, raw=raw)
        return {}
