Codeforces API Utilities
========================

Python wrappers for the [Codeforces API](https://codeforces.com/apiHelp), and support for generating an [ICPC Tools](https://tools.icpc.global/) event feed.  

Requirements
------------

Install the package using `pip install .`.

Optional: If you wish to run authorized API calls, copy `example.env` to `.env` and set the API parameters in it.
[Check CF API docs to see how to generate an API key](https://codeforces.com/apiHelp).


Tool: ICPC Standings Resolver
-----------------------------

Go to [tools.icpc.global](https://tools.icpc.global/) and download "Resolver".
Optionally you can download "Contest Utilities" to validate the generated files.

In Resolver, you should have the executables `resolver.sh` and `awards.sh`
In Contest Utilites, you should have the executable `eventFeed.sh` (others are not needed).

A basic CLI tool is provided: [examples/resolverFeed.py](examples/resolverFeed.py).
This tool can be used to generate a JSON event feed for the ICPC resolver tool.

1. Run `python examples/feed.py <status_output_file.json> <standings_output_file.json> <feed.json>`.
1. `cd` to the resolver tool, and run `./resolver.sh feed.json`
1. (optional) To validate, run `/path/to/eventFeed.sh --validate feed.json`.
1. (optional) To edit the awards manually, run `/path/to/awards.sh`. Select "Disk" and load the generated `feed.json` file.

Contributing
------------

Install the project in development mode:
```sh
pip install -e .[dev]
```

Code is formatted with [Black](https://black.readthedocs.io/en/stable/), linted with [Ruff](https://beta.ruff.rs/docs/) and tested with [Pytest](https://docs.pytest.org/en/7.4.x/)
```
black .
ruff .
pytest
```

### ICPC EventFeed dataclass

To generate/update the dataclasses for ICPCTools event feeds, first clone the `ccs-specs` submodule:

```sh
git submodule init
git submodule update
```

Now run `datamodel-codegen` to generate dataclasses from the JSONSchema:
```sh
datamodel-codegen \
    --input "/pathto/ccs-specs/json-schema/event-feed-array.json" \
    --input-file-type jsonschema \
    --output cfutils/icpctools/EventFeed.py \
    --output-model-type dataclasses.dataclass \
    --target-python-version 3.11 \
    --use-standard-collections \
    --use-schema-description
```
