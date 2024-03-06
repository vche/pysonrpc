![GitHub](https://img.shields.io/github/license/vche/pysonrpc) [![Codecov](https://img.shields.io/codecov/c/github/vche/pysonrpc)](https://codecov.io/gh/vche/pysonrpc) [![GitHub release (latest by date)](https://img.shields.io/github/v/release/vche/pysonrpc)](https://github.com/vche/pysonrpc/releases) [![PyPI](https://img.shields.io/pypi/v/pysonrpc)](https://pypi.org/project/pysonrpc/) [![Downloads](https://pepy.tech/badge/pysonrpc)](https://pepy.tech/project/pysonrpc)

## What's pysonrpc

JSON RPC python client module with a CLI and method auto detection.

For JSON RPC server with a schema, an url canbe specified so that the schema is read, detecting the list of methods
supported.
Attributes are dynamically created to allow methods to be called as attributes, including namespaces.

Examples with [kodi](https://kodi.tv/) json rpc client:

### CLI

```bash
# List all methods available, autodetected from the server url (for kodi, this is not a complete list)
pysonrpc -r http://127.0.0.1:8080/jsonrpc -a list

# List all methods available, autodetected from a server rpc method
pysonrpc -r http://127.0.0.1:8080/jsonrpc -am "JSONRPC.Introspect" list -s -f VideoLibrary.

# List all methods available, autodetected from a schema json file
pysonrpc -r http://127.0.0.1:8080/jsonrpc -f schema.json list

# List methods filtered with VideoLibrary
pysonrpc -r http://127.0.0.1:8080/jsonrpc -am "JSONRPC.Introspect" list -s -f VideoLibrary

# Get favaourites list
pysonrpc -r http://127.0.0.1:8080/jsonrpc -a run Favourites.GetFavourites

# Get information on movie 1419
pysonrpc -r http://127.0.0.1:8080/jsonrpc -a run -m VideoLibrary.GetMovieDetails -p '{"movieid": 1419}'
```

Help
```bash
 usage: pysonrpc [-h] [--version] --url URL [--user USER] [--password PASSWORD] [--debug] [--method-discover] [--method-discover-path METHOD_DISCOVER_PATH]
                [--method-file METHOD_FILE]
                {list,run} ...

RPC client

positional arguments:
  {list,run}            commands
    list                List available methods
    run                 Execute a method

options:
  -h, --help            show this help message and exit
  --version, -v         Display version
  --url URL, -r URL     Host url, e.g 'http://192.168.0.1:8080'
  --user USER, -u USER  username if using basic authentication
  --password PASSWORD, -p PASSWORD
                        Password if using basic authentication
  --debug, -d           Enable debug logging
  --method-discover, -a
                        Auto discover rpc methods at the specified endpoint url
  --method-discover-path METHOD_DISCOVER_PATH
                        Specifies a path after the specified endpoint url to query for methods auto discovery
  --method-file METHOD_FILE, -f METHOD_FILE
                        Discover methods from given json file
```

### Python module

```python
from pysonrpc import JsonRpcEndpoint

cli = JsonRpcEndpoint("http://127.0.0.1:8080/jsonrpc", user="user", password="password", auto_detect=True)

#Running a method from name
result=cli.run_method("Favourites.GetFavourites")
result=cli.run_method("VideoLibrary.GetMovieDetails", movieid=1419)

#Running a method from attribute
result=cli.Favourites.GetFavourites()
result=cli.VideoLibrary.GetMovieDetails(movieid=1419)
```

## Development

Using [pixi](https://pixi.sh/)

```sh
# Install dependencies and pycliarr
pixi build

# Run the binary
pixi run pycliarr

# Or start a term
pixi shell

# Run tests
pixi run tests

#generate doc
pixi run doc
```

### Run tests

```sh
pixi run tox
```

If mypy fails due to missing import stubs:
```sh
.tox/checkers/bin/mypy --install-types
```

### Generate documentation:

```sh
pip install sphinx sphinx_rtd_theme m2r2
./setup.py doc
```

In case new classes/modules are added, update the autodoc list:
```sh
rm  docs/sphinx_conf/source/*
sphinx-apidoc -f -o docs/sphinx_conf/source/ src/pycliarr --separate
```

### TODO:
- move setup.cfg to pyproject.toml
- better way for parameters ? (add a list arg for a method only)
- tests and coverage
- workflow to pip publish

