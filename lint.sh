#!/usr/bin/env bash

set -eux

poetry run isort .
poetry run black .
poetry run flake8 .
poetry run pydocstyle
poetry run pylint src
poetry run pytest
