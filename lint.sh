#!/usr/bin/env bash

set -eux

poetry run black .
poetry run isort .
poetry run flake8 .
poetry run pydocstyle .
poetry run mypy biterator
poetry run pytest

set +eux