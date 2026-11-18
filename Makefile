PYTHON := /usr/bin/python3
VERSION := $(shell sed -n 's/^Version: //p' packaging/control)
FILE ?=
export FILE

.PHONY: run test deb source

run:
	@if [ -n "$$FILE" ]; then exec $(PYTHON) viewer.py "$$FILE"; else exec $(PYTHON) viewer.py; fi

test:
	QT_QPA_PLATFORM=offscreen $(PYTHON) -m unittest discover -s tests -v

deb:
	sh build-deb.sh

source:
	mkdir -p dist
	tar --exclude='./dist' --exclude='./.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='./.venv' --transform='s,^\.,step-viewer,' -czf dist/local-step-viewer-$(VERSION)-src.tar.gz .
