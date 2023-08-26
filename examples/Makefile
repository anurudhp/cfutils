DATA_PATH = ../data/examples

STATUS_FILE = $(DATA_PATH)/resolverfeed/status_104491.json
STANDINGS_FILE = $(DATA_PATH)/resolverfeed/standings_104491.json

feed.json: feed.py $(STATUS_FILE) $(STANDINGS_FILE)
	python feed.py 104491 $(STATUS_FILE) $(STANDINGS_FILE) $@ --unofficial
