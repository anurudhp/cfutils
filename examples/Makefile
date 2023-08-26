DATA_PATH ?= ../data/examples
TOOL_EVENT_FEED ?= ../../contestUtil-2.4.727/eventFeed.sh

STATUS_FILE ?= $(DATA_PATH)/resolverfeed/status_104491.json
STANDINGS_FILE ?= $(DATA_PATH)/resolverfeed/standings_104491.json

feed.json: feed.py $(STATUS_FILE) $(STANDINGS_FILE)
	python feed.py 104491 $(STATUS_FILE) $(STANDINGS_FILE) $@ --unofficial

validate: feed.json
	$(TOOL_EVENT_FEED) --validate $^

summary: feed.json validate
	$(TOOL_EVENT_FEED) --summary $<
