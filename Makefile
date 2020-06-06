.DEFAULT_GOAL := help
BUILD_NAME := zerohc

install-requirements: ## pip install project requirements
	pip install -r requirements.txt

install-build-requirements: ## pip install requirements for binary building
	pip install pyinstaller

install-test-requirements: ## pip install requirements for tests
	pip install -r tests/requirements.txt

test: ## run tests
	pytest -sv .

install-package-requirements: ## pip install requirements for packaging & uploading
	pip install --upgrade pip setuptools wheel twine

package: ## create package (sdist)
	python setup.py sdist bdist_wheel

package-upload: ## upload package to pypi
	twine upload --skip-existing dist/*

package-test-upload: ## upload package to test-pypi
	twine upload --skip-existing --repository testpypi dist/*

package-clear: ## clear dist directory
	rm -rf dist/ build/ *.egg-info/ MANIFEST

build-binary: ## build binary with pyinstaller
	python -m PyInstaller --clean --onefile --name=${BUILD_NAME} __main__.py

build-binary-in-docker: ## build binary with pyinstaller within a docker container
	./tools/build-in-docker.sh

build-clean: ## delete pyinstaller directories (except dist)
	rm -rf build *.spec

help: ## show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
