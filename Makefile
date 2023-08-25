ci:
	black --quiet --check .
	ruff .
	pytest --doctest-modules --quiet
	mypy --check-untyped-defs cfutils examples
	cd docs && make clean && make html # sphinx

eventfeedpy:
	git submodule init
	git submodule update
	datamodel-codegen \
	    --input "ccs-specs/json-schema/event-feed-array.json" \
	    --input-file-type jsonschema \
	    --output cfutils/icpctools/EventFeed.py \
	    --output-model-type dataclasses.dataclass \
	    --target-python-version 3.11 \
	    --use-standard-collections \
	    --use-schema-description
