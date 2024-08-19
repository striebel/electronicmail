PIP_REQ_SPEC    = 'pip>=21.0.1,<24.0.1'
SPHINX_REQ_SPEC = 'sphinx>=8.0.0,<9.0.0'
FURO_REQ_SPEC   = 'furo>=2024.0.0,<2025.0.0'
BUILD_REQ_SPEC  = 'build>=1.2.1,<2.0.0'
TWINE_REQ_SPEC  = 'twine>=5.0.0,<6.0.0'


all: \
    install-editable \
    build-docs \
    build-package \
    test-local \
    upload-testpypi \
    sleep-first \
    test-testpypi \
    upload-realpypi \
    sleep-second \
    test-realpypi

sleep-first:
	sleep 30

sleep-second:
	sleep 30

install-editable:
	printf '\n======================\nbegin install-editable\n======================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./_setup.py
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		--editable .
	rm ./pyproject.toml
	rm ./setup.cfg
	rm ./MANIFEST.in

build-docs:
	printf '\n================\nbegin build-docs\n================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(SPHINX_REQ_SPEC) $(FURO_REQ_SPEC)
	. ./meta.sh >/dev/null && ./_setup.py
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		--editable .
	rm -rf docs_build
	mkdir docs_build
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/sphinx-build \
		-M html docs_source docs_build
	rm -rf docs
	mkdir docs
	touch docs/.nojekyll
	cp -r docs_build/html/* docs/

build-package:
	printf '\n===================\nbegin build-package\n===================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(BUILD_REQ_SPEC)
	. ./meta.sh >/dev/null && ./_setup.py
	rm -rf ./dist
	rm -rf ./*.egg-info
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m build --sdist .
	rm ./pyproject.toml
	rm ./setup.cfg
	rm ./MANIFEST.in
	rm -rf ./*.egg-info

test-local:
	printf '\n================\nbegin test-local\n================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip uninstall --yes $${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --no-cache-dir \
		./dist/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _`
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _` --version

upload-testpypi:
	printf '\n=====================\nbegin upload-testpypi\n=====================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(TWINE_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m twine check \
		--strict \
		./dist/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m twine upload \
        	--repository pypirc-testpypi \
		./dist/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz

upload-realpypi:
	printf '\n=====================\nbegin upload-realpypi\n=====================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(TWINE_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m twine check \
		--strict \
		./dist/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m twine upload \
		--repository pypirc-realpypi \
		./dist/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz

test-testpypi:
	printf '\n===================\nbegin test-testpypi\n===================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip uninstall --yes $${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		`printf $${BUILD_REQUIRES} | tr , ' ' | tr --delete '"'`
	rm -rf dist-testpypi
	mkdir  dist-testpypi
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip download \
		--no-deps \
		--no-build-isolation \
		--no-cache-dir \
		--index-url https://test.pypi.org/simple/ \
		--dest ./dist-testpypi \
		$${NAME}==$${VERSION}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install \
		--no-cache-dir \
		./dist-testpypi/`printf $${NAME} | tr .- _`-$${VERSION}.tar.gz
	rm -rf dist-testpypi
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _`
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _` --version

test-realpypi:
	printf '\n===================\nbegin test-realpypi\n===================\n\n'
	. ./meta.sh >/dev/null && python -m venv ./venv-$${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install --upgrade \
		$(PIP_REQ_SPEC)
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip uninstall --yes $${NAME}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip cache remove \
		`printf $${NAME} | tr - _`
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/pip install \
		--no-cache-dir \
		$${NAME}==$${VERSION}
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _`
	. ./meta.sh >/dev/null && ./venv-$${NAME}/bin/python -m \
		`printf $${NAME} | tr - _` --version



