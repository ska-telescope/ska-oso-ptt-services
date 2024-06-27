# include Makefile for Javascript related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

JS_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-js-support
JS_PROJECT_BASE_DIR := $(shell dirname $$(dirname $(abspath $(lastword $(MAKEFILE_LIST)))))
VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getTag)

SHELL=/usr/bin/env bash

JS_PROJECT_DIR ?= .## JS project root dir
# Remove trailing slashes
JS_PROJECT_DIR := $(patsubst %/,%,$(strip $(JS_PROJECT_DIR)))
ifeq ($(JS_PROJECT_DIR),)
JS_PROJECT_DIR := .
$(warning 'JS_PROJECT_DIR' not set, setting to '.')
endif

JS_SRC ?= src## JS src directory - defaults to src

JS_COMMAND_RUNNER ?= npx## use to specify command runner, e.g. "npx" or "nothing"

JS_ESLINT_CONFIG ?= .eslintrc.js## use to specify the file to configure eslint, e.g. ".eslintrc.json"

JS_ESLINT_FILE_EXTENSIONS ?= js,jsx,ts,tsx## used to specify which extensions to use with eslint

JS_VARS_BEFORE_ESLINT_FORMAT ?= ## used to include needed argument variables to pass to eslint for format

JS_SWITCHES_FOR_ESLINT_FORMAT ?= ## Custom switches added to eslint for format

JS_VARS_BEFORE_ESLINT_LINT ?= ## used to include needed argument variables to pass to eslint for linting

JS_SWITCHES_FOR_ESLINT_LINT ?= ## Custom switches added to eslint for linting

JS_PACKAGE_MANAGER ?= yarn## use to specify package manager runner, e.g. "yarn" or "npm"

JS_SWITCHES_FOR_INSTALL ?= ## switches to pass to install command

# Default unit testing platform - jest

## Because taranta projects clone the upstream projects shared with MaxIV, the actual directory is not the "root" directory
## The post-processing jobs look for the 'build' directory at the root of the project
JS_BUILD_REPORTS_DIRECTORY ?= $(JS_PROJECT_BASE_DIR)/build/reports## build reports directory

JS_VARS_BEFORE_TEST ?= ## used to include needed argument variables to pass to start command before test

JS_TEST_COMMAND ?= jest## command to use to run jest tests (i.e, react-scripts test)

JS_TEST_SWITCHES ?= ##Custom switches to pass to jest

## switches to pass jest tests
JS_TEST_DEFAULT_SWITCHES ?= --ci --env=jsdom --watchAll=false --passWithNoTests \
	--verbose --reporters=default --reporters=jest-junit \
	--coverage --coverageDirectory=$(JS_BUILD_REPORTS_DIRECTORY) \
	--coverageReporters=text --coverageReporters=cobertura --coverageReporters=html \
	--logHeapUsage $(JS_TEST_SWITCHES)

# Default e2e testing platform - cypress
# Default e2e coverage report generation - nyc (default of cypress)

## Because taranta projects clone the upstream projects shared with MaxIV, the actual directory is not the "root" directory
## The post-processing jobs look for the 'build' directory at the root of the project
JS_BUILD_REPORTS_E2E_DIRECTORY ?= $(JS_PROJECT_BASE_DIR)/build/reports/e2e## build reports directory for e2e tests

JS_VARS_BEFORE_SERVE ?= ## used to include needed argument variables to pass to start command before e2e

JS_SERVE_COMMAND ?= webpack serve## command to use to start the application (i.e, react-scripts start)

JS_SERVE_PORT ?= 8090## serve port

JS_SERVE_SWITCHES ?= --mode development --no-live-reload --no-open --port $(JS_SERVE_PORT)## switches to pass to start command

JS_E2E_TESTS_DIR ?= tests/cypress##directory where to look for e2e tests

JS_VARS_BEFORE_E2E_TEST ?= ## used to include needed argument variables to pass to start command before cypress

JS_E2E_TEST_COMMAND ?= cypress run## command to use to start the cypress tests (i.e, react-scripts test)

JS_E2E_TEST_SWITCHES ?= ##Custom switches to pass to cypress

## switches to pass to cypress
JS_E2E_TEST_DEFAULT_SWITCHES ?= --e2e --headless --browser chrome --config video=false \
	--reporter junit --reporter-options "reportDir=$(JS_BUILD_REPORTS_E2E_DIRECTORY),mochaFile=build/tests/e2e-tests-[hash].xml" \
	$(JS_E2E_TEST_SWITCHES)

JS_E2E_COVERAGE_COMMAND_ENABLED ?= true## enable or disable execution of coverage command, given if test command produces or not coverage report

JS_E2E_COVERAGE_COMMAND ?= nyc report## command to use to generate coverage reports

JS_VARS_BEFORE_E2E_COVERAGE ?= ## used to include needed argument variables to pass to start command before nyc

JS_E2E_COVERAGE_SWITCHES ?= ##Custom switches to pass to nyc

## switches to pass to nyc
JS_E2E_COVERAGE_DEFAULT_SWITCHES ?= --report-dir $(JS_BUILD_REPORTS_E2E_DIRECTORY) \
	--reporter html --reporter cobertura --reporter text \
	$(JS_E2E_COVERAGE_SWITCHES)

## Taranta uses NPM while skeleton based projects use YARN
## Quickly define the "best-practice" arguments for each package manager
ifeq ($(JS_SWITCHES_FOR_INSTALL),)
ifneq (,$(findstring npm,$(VARIABLE)))
    JS_SWITCHES_FOR_INSTALL = --no-cache
endif
ifneq (,$(findstring yarn,$(VARIABLE)))
    JS_SWITCHES_FOR_INSTALL = --frozen-lockfile
endif
endif

js-pre-install:

js-post-install:

js-do-install:
	@cd $(JS_PROJECT_DIR); \
	if [ ! -d "./node_modules" ]; then \
		$(JS_PACKAGE_MANAGER) install $(JS_SWITCHES_FOR_INSTALL); \
	else \
		echo "js-do-install: '$(JS_PROJECT_DIR)/node_modules' already exists. If you want to re-install, run 'make js-install-reinstall'"; \
	fi

## TARGET: js-install
## SYNOPSIS: make js-install
## HOOKS: js-pre-install, js-post-install
## VARS:
##       JS_PACKAGE_MANAGER=<package manager executor> - defaults to yarn
##       JS_SWITCHES_FOR_INSTALL=<switches for install command>
##
##  Install JS project dependencies

js-install: js-pre-install js-do-install js-post-install

js-install-clean:
	@echo "js-install-clean: Removing '$(JS_PROJECT_DIR)/node_modules'"
	@cd $(JS_PROJECT_DIR); \
	rm -rf ./node_modules

## TARGET: js-install-clean
## SYNOPSIS: make js-install-clean
## HOOKS:
## VARS:
##
##  Clean JS project dependencies

js-install-reinstall: js-install-clean js-install

## TARGET: js-install-reinstall
## SYNOPSIS: make js-install-reinstall
## HOOKS:
## VARS:
##
##  Cleanly reinstall JS project dependencies

.PHONY:	js-install js-pre-install js-do-install js-post-install js-install-clean js-install-reinstall

js-pre-format:

js-post-format:

js-do-format:
	@cd $(JS_PROJECT_DIR); \
	$(JS_VARS_BEFORE_ESLINT_FORMAT) $(JS_COMMAND_RUNNER) eslint -c $(JS_ESLINT_CONFIG) \
		--fix --color $(JS_SWITCHES_FOR_ESLINT_FORMAT) \
		--ignore-pattern "**/node_modules/*" --ignore-pattern "**/.eslintignore" \
		"$(JS_SRC)/**/*.{$(JS_ESLINT_FILE_EXTENSIONS)}"

## TARGET: js-format
## SYNOPSIS: make js-format
## HOOKS: js-pre-format, js-post-format
## VARS:
##		JS_SRC=<file or directory path to JS code> - default 'src/'
##		JS_COMMAND_RUNNER=<command executor> - defaults to npx
##		JS_ESLINT_CONFIG=<path to eslint config file> - defaults to .eslintrc.js
##		JS_ESLINT_FILE_EXTENSIONS=<file extensions> - defaults to js,jsx,ts,tsx
##		JS_VARS_BEFORE_ESLINT_FORMAT=<environment variables to pass to eslint>
##		JS_SWITCHES_FOR_ESLINT_FORMAT=<switches to pass to eslint>
##
##  Reformat project javascript code in the given directories/files using eslint

js-format: js-install js-pre-format js-do-format js-post-format  ## format the js code

.PHONY:	js-format js-pre-format js-do-format js-post-format

js-pre-lint:

js-post-lint:

js-do-lint:
	@cd $(JS_PROJECT_DIR); \
	mkdir -p $(JS_BUILD_REPORTS_DIRECTORY); \
	$(JS_PACKAGE_MANAGER) list --depth=0 --json > $(JS_BUILD_REPORTS_DIRECTORY)/dependencies.json; \
	$(JS_PACKAGE_MANAGER) list --depth=0  > $(JS_BUILD_REPORTS_DIRECTORY)/dependencies.txt; \
	$(JS_VARS_BEFORE_ESLINT_LINT) $(JS_COMMAND_RUNNER) eslint -c $(JS_ESLINT_CONFIG) \
		--fix-dry-run --color $(JS_SWITCHES_FOR_ESLINT_LINT) \
		--ignore-pattern "**/node_modules/*" --ignore-pattern "**/.eslintignore" \
		"$(JS_SRC)/**/*.{$(JS_ESLINT_FILE_EXTENSIONS)}"; \
	$(JS_VARS_BEFORE_ESLINT_LINT) $(JS_COMMAND_RUNNER) eslint -c $(JS_ESLINT_CONFIG) \
		--ignore-pattern "**/node_modules/*" --ignore-pattern "**/.eslintignore" \
		-f junit -o $(JS_BUILD_REPORTS_DIRECTORY)/linting.xml $(JS_SWITCHES_FOR_ESLINT_LINT) \
		"$(JS_SRC)/**/*.{$(JS_ESLINT_FILE_EXTENSIONS)}"


## TARGET: js-lint
## SYNOPSIS: make js-lint
## HOOKS: js-pre-lint, js-post-lint
## VARS:
##
##		JS_SRC=<file or directory path to JS code> - default 'src/'
##		JS_BUILD_REPORTS_DIRECTORY=<directory to store build and test results>
##		JS_COMMAND_RUNNER=<command executor> - defaults to npx
##		JS_PACKAGE_MANAGER=<package manager to use> - defaults to yarn
##		JS_ESLINT_FILE_EXTENSIONS=<file extensions> - defaults to js,jsx,ts,tsx
##		JS_VARS_BEFORE_ESLINT_LINT=<environment variables to pass to eslint>
##		JS_SWITCHES_FOR_ESLINT_LINT=<switches to pass to eslint>
##
##  Lint check javascript code in the given directories/files using eslint

js-lint: js-install js-pre-lint js-do-lint js-post-lint  ## lint the javascript code

.PHONY:	js-lint js-pre-lint js-do-lint js-post-lint

js-pre-test:

js-post-test:

js-do-test:
	@{ \
		cd $(JS_PROJECT_DIR); \
		mkdir -p $(JS_BUILD_REPORTS_DIRECTORY); \
		export JEST_JUNIT_OUTPUT_DIR=$(JS_BUILD_REPORTS_DIRECTORY); \
		export JEST_JUNIT_OUTPUT_NAME=unit-tests.xml; \
		$(JS_VARS_BEFORE_TEST) $(JS_COMMAND_RUNNER) $(JS_TEST_COMMAND) $(JS_TEST_DEFAULT_SWITCHES); \
		EXIT_CODE=$$?; \
		echo "js-do-test: Exit code $${EXIT_CODE}"; \
		cp $(JS_BUILD_REPORTS_DIRECTORY)/cobertura-coverage.xml $(JS_BUILD_REPORTS_DIRECTORY)/code-coverage.xml; \
		exit $$EXIT_CODE; \
	}

## TARGET: js-test
## SYNOPSIS: make js-test
## HOOKS: js-pre-test, js-post-test
## VARS:
##		JS_SRC=<file or directory path to JS code> - default 'src/'
##		JS_BUILD_REPORTS_DIRECTORY=<directory to store build and test results>
##		JS_COMMAND_RUNNER=<command executor> - defaults to npx
##		JS_TEST_COMMAND=<command to invoke tests> - defaults to jest
##		JS_TEST_SWITCHES=<extra switches to pass to test command>
##		JS_TEST_DEFAULT_SWITCHES=<default switches plus extra to pass to test command>
##
##  Run javascript unit tests using jest

js-test: js-install js-pre-test js-do-test js-post-test  ## test the javascript code

.PHONY:	js-test js-pre-test js-do-test js-post-test

js-pre-e2e-test:

js-post-e2e-test:

js-start-e2e-test:  ## start the javascript application for e2e testing
	@. $(JS_SUPPORT); \
	JS_VARS_BEFORE_SERVE="$(JS_VARS_BEFORE_SERVE)" \
	JS_COMMAND_RUNNER="$(JS_COMMAND_RUNNER)" \
	JS_PACKAGE_MANAGER="$(JS_PACKAGE_MANAGER)" \
	JS_SERVE_COMMAND="$(JS_SERVE_COMMAND)" \
	JS_SERVE_SWITCHES="$(JS_SERVE_SWITCHES)" \
	JS_SERVE_PORT="$(JS_SERVE_PORT)" \
	jsServe

js-stop-e2e-test:  ## stop the javascript application after e2e testing
	@. $(JS_SUPPORT); \
	jsStopServe

js-do-e2e-test:
	@if [ ! -d "$(JS_E2E_TESTS_DIR)" ]; then \
		echo "js-do-e2e-test: No tests found"; \
		exit 0; \
	fi
	@{ \
		. $(JS_SUPPORT); \
		cd $(JS_PROJECT_DIR); \
		mkdir -p $(JS_BUILD_REPORTS_E2E_DIRECTORY); \
		rm -rf ./build/tests/e2e*.xml; \
		$(JS_VARS_BEFORE_E2E_TEST) COVERAGE_OUTPUT_DIR=$(JS_BUILD_REPORTS_E2E_DIRECTORY) $(JS_COMMAND_RUNNER) $(JS_E2E_TEST_COMMAND) $(JS_E2E_TEST_DEFAULT_SWITCHES); \
		EXIT_CODE=$$?; \
		echo "js-do-e2e-test: Exit code $${EXIT_CODE}"; \
		JS_PACKAGE_MANAGER=$(JS_PACKAGE_MANAGER) jsMergeReports $(JS_BUILD_REPORTS_E2E_DIRECTORY)/e2e-tests.xml "build/tests/e2e*.xml"; \
		cp $(JS_BUILD_REPORTS_E2E_DIRECTORY)/e2e-tests.xml $(JS_BUILD_REPORTS_DIRECTORY)/e2e-tests.xml; \
		$(JS_VARS_BEFORE_E2E_COVERAGE) COVERAGE_OUTPUT_DIR=$(JS_BUILD_REPORTS_E2E_DIRECTORY) $(JS_COMMAND_RUNNER) $(JS_E2E_COVERAGE_COMMAND) $(JS_E2E_COVERAGE_DEFAULT_SWITCHES); \
		cp $(JS_BUILD_REPORTS_E2E_DIRECTORY)/cobertura-coverage.xml $(JS_BUILD_REPORTS_DIRECTORY)/e2e-coverage.xml; \
		jsStopServe; \
		exit $$EXIT_CODE; \
	}


## TARGET: js-e2e-test
## SYNOPSIS: make js-e2e-test
## HOOKS: js-pre-e2e-test, js-start-e2e-test, js-stop-e2e-test, js-post-e2e-test
## VARS:
##		JS_SRC=<file or directory path to JS code> - default 'src/'
##		JS_BUILD_REPORTS_DIRECTORY=<directory to store build and test results>
##		JS_COMMAND_RUNNER=<command executor> - defaults to npx
##		JS_BUILD_REPORTS_E2E_DIRECTORY=<directory to store e2e test results>
##		JS_E2E_TESTS_DIR=<path to location of e2e tests> - defaults to 'tests/cypress/'
##		JS_VARS_BEFORE_SERVE=<vars before serve command>
##		JS_SERVE_COMMAND=<command to invoke to serve the application>
##		JS_SERVE_PORT=<port where to serve the application>
##		JS_SERVE_SWITCHES=<switches passed to serve command>
##		JS_VARS_BEFORE_E2E_TEST=<vars before e2e test command>
##		JS_E2E_TEST_COMMAND=<command to invoke e2e tests> - defaults to cypress
##		JS_E2E_TEST_SWITCHES=<extra switches to pass to test command>
##		JS_E2E_TEST_DEFAULT_SWITCHES=<default switches plus extra to pass to test command>
##		JS_E2E_COVERAGE_COMMAND_ENABLED=<enable or disable coverage command execution>
##		JS_E2E_COVERAGE_COMMAND=<command to invoke coverage generation, i.e nyc report>
##		JS_VARS_BEFORE_E2E_COVERAGE=<vars before e2e coverage generation>
##		JS_E2E_COVERAGE_SWITCHES=<extra switches to pass to coverage generator>
##		JS_E2E_COVERAGE_DEFAULT_SWITCHES=<default switches plus extra to pass to coverage generator>
##
##  Run javascript e2e tests using cypress

js-e2e-test: js-install js-pre-e2e-test js-start-e2e-test js-do-e2e-test js-stop-e2e-test js-post-e2e-test  ## e2e test the javascript code

.PHONY:	js-e2e-test js-start-e2e-test js-pre-e2e-test js-do-e2e-test js-stop-e2e-test js-post-e2e-test

# end of switch to suppress targets for help
endif
endif
