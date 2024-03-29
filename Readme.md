Codeforces API Utilities [![CI](https://github.com/anurudhp/cfutils/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/anurudhp/cfutils/actions/workflows/ci.yaml)
========================

Python wrappers for the [Codeforces API](https://codeforces.com/apiHelp), and support for generating an [ICPC Tools](https://tools.icpc.global/) event feed.  

Installation
------------

To install the package, first clone it and then install using `pip`:
```sh
pip install .
```
It is recommended to use a [Virtual environment](https://docs.python.org/3/library/venv.html).

Optional: If you wish to run authorized API calls, copy `example.env` to `.env` and set the API parameters in it.
[Check CF API docs to see how to generate an API key](https://codeforces.com/apiHelp).


### Tool: ICPC Standings Resolver

Go to [tools.icpc.global](https://tools.icpc.global/) and download "Resolver".
Optionally you can download "Contest Utilities" to validate the generated files.

In Resolver, you should have the executables `resolver.sh` and `awards.sh`
In Contest Utilites, you should have the executable `eventFeed.sh` (others are not needed).

A basic CLI tool is provided: [examples/feed.py](https://github.com/anurudhp/cfutils/blob/main/examples/feed.py).
This tool can be used to generate a JSON event feed for the ICPC resolver tool.

1. Run `python examples/feed.py <status_output_file.json> <standings_output_file.json> <feed.json>`.
1. `cd` to the resolver tool, and run `./resolver.sh /path/to/feed.json`
1. (optional) To validate, run `/path/to/eventFeed.sh --validate feed.json`.
1. (optional) To edit the awards manually, `cd` to the resolver folder and run `awards.sh`. Select "Disk" and load the generated `feed.json` file.

Contributing
------------

Install the project in development mode:
```sh
pip install -e .[dev]
```

- Formatter: [Black](https://black.readthedocs.io/en/stable/)
- Linter: [Ruff](https://beta.ruff.rs/docs/)
- Type-checking: [mypy](https://mypy.readthedocs.io/en/stable/)
- Testing: [Pytest](https://docs.pytest.org/en/7.4.x/)

The CI checks can be run with `make ci`.

### ICPC EventFeed dataclass

To generate/update the dataclasses for ICPCTools event feeds, first clone the `ccs-specs` submodule:

```sh
git submodule init
git submodule update
```

Now run `datamodel-codegen` to generate dataclasses from the JSONSchema:
```sh
datamodel-codegen \
    --input "ccs-specs/json-schema/event-feed-array.json" \
    --input-file-type jsonschema \
    --output cfutils/icpctools/event_feed.py \
    --output-model-type dataclasses.dataclass \
    --target-python-version 3.11 \
    --use-standard-collections \
    --use-schema-description
```
