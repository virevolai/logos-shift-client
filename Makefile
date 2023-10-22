.PHONY: install install-dev test lint lintgit clean build upload

install:
	pip install .

install-dev:
	pip install .[dev]

test:
	pytest

lint:
	ruff check logos_shift_client

lintgit:
	ruff check --output-format=github logos_shift_client

clean:
	rm -rf dist build *.egg-info

build: clean
	python setup.py sdist bdist_wheel

# Upload the package to PyPI
upload:
	twine upload dist/*

all: install-dev lint lintgit test build

