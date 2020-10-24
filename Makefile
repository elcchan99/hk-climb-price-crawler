# Determine this makefile's path.
# Be sure to place this BEFORE `include` directives, if any.
THIS_FILE := $(lastword $(MAKEFILE_LIST))

SHELL := $(SHELL) -e  # insure return codes within line continuations are honored
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
OS = $(shell uname -s)

PACKAGE_NAME=.

# Print usage of main targets when user types "make" or "make help"
.PHONY: help
help:
	@echo "Please choose one of the following targets: \n"\
	      "    setup: Setup your dev environment and install dev and package dependencies\n"\
	      "    dependencies: Only build the Python dependencies\n"\
	      "    test: Run tests\n"\
	      "    format: Validate code and documentation\n"\
	      "\n"\
	      "View the Makefile for more documentation about all of the available commands"
	@exit 2


.PHONY: setup
setup: dependencies


.PHONY: dependencies
dependencies:
	poetry install


.PHONY: format
format:
	poetry run isort ${PACKAGE_NAME}
	poetry run black ${PACKAGE_NAME}


.PHONY: lint
lint:
	poetry run isort --check --diff ${PACKAGE_NAME}
	poetry run black --check ${PACKAGE_NAME}
	poetry run flake8 ${PACKAGE_NAME}
	poetry run pylint *.py

.PHONY: justclimb
justclimb:
	poetry run scrapy runspider justclimb_price_crawler.py
