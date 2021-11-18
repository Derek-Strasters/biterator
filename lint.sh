#!/usr/bin/env bash

set -eux

poetry run black .
poetry run isort .
poetry run flake8 .
poetry run pydocstyle .
find ./ -maxdepth 2 -name '__init__.py' -printf '%h ' | xargs poetry run pylint
poetry run mypy biterator
poetry run pytest
# TODO: Run unitests from test folder

set +eux