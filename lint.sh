#!/usr/bin/env bash

set -eux

poetry run black src
poetry run isort src
poetry run flake8 src
poetry run pydocstyle src
find ./src -maxdepth 2 -name '__init__.py' -printf '%h ' | xargs poetry run pylint
poetry run mypy src
poetry run pytest
