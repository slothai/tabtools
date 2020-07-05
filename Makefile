ENV=$(CURDIR)/.env

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile


.PHONY: clean
# target: clean - Remove temporary files
clean:
	@rm -rf build pydist docs/_build ./dist
	@rm -f *.py[co]
	@rm -f *.so
	@rm -f */*.py[co]
	@rm -f */*.orig
	@rm -f */*/*.py[co]

.PHONY: env
# target: env - install python develpment packages
env:
	@python3 -m venv $(ENV)
	$(ENV)/bin/pip install -r requirements.txt

.PHONY: test
# target: test - Runs tests
test: clean
	$(ENV)/bin/pytest $(CURDIR)/tabtools/tests

.PHONY: build
# target: build - build self-executable tabtools scripts
build: clean
	sh build.sh

.PHONY: upload
# target: upload - Upload module on PyPi
upload:
	@python setup.py sdist --dist-dir pydist bdist_wheel --dist-dir pydist upload || echo 'Upload already'
