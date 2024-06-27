# include Makefile for Helm Chart related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support
HELM_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-helm-support
HELM_CONVERT_CHART_TO_HELMFILE ?=  $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/resources/convert_umbrella_chart_to_helmfile.py

HELM_CHART_DIRS := $(shell if [ -d charts ]; then cd charts; ls -d */ 2>/dev/null | sed 's/\/$$//'; fi;)
HELM_CHARTS ?= $(HELM_CHART_DIRS)
HELM_CHARTS_TO_PUBLISH ?= $(HELM_CHARTS)
HELM_CHARTS_TO_CONVERT ?= $(HELM_CHARTS)
HELM_CHARTS_CHANNEL ?= dev## Helm Chart Channel for GitLab publish
HELM_BUILD_PUSH_SKIP ?=
HELM_YQ_VERSION ?= 4.43.1## yq version to install
HELM_YQ_INSTALL_DIR ?= /usr/local/bin

VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getTag)

SHELL=/usr/bin/env bash

.PHONY: helm-pre-lint helm-do-lint helm-post-lint helm-lint \
	helm-publish helm-pre-publish helm-do-publish helm-convert-to-helmfile \
	helm-check-deps

helm-pre-lint:

helm-post-lint:

helm-pre-publish:

helm-post-publish:

helm-do-lint:
	@. $(HELM_SUPPORT) ; helmChartLint "$(HELM_CHARTS)"

## TARGET: helm-lint
## SYNOPSIS: make helm-lint
## HOOKS: helm-pre-lint, helm-post-lint
## VARS:
##       HELM_CHARTS=<list of helm chart directories under ./charts/>
##
##  Perform lint checks on a list of Helm Charts found in the ./charts directory.

helm-lint: helm-pre-lint helm-do-lint helm-post-lint ## lint the Helm Charts

helm-helmfile-pre-lint:

helm-helmfile-post-lint:

## TARGET: helm-helmfile-lint
## SYNOPSIS: make helm-helmfile-lint
## HOOKS: helm-helmfile-pre-lint, helm-helmfile-post-lint
## VARS:
##       HELM_CHARTS=<list of helm chart directories under ./charts/>
##
##  Perform lint checks on a list of Helmfiles Charts found in the ./charts directory.

helm-helmfile-do-lint:
	@. $(HELM_SUPPORT) ; helmfileLint "$(HELM_CHARTS)"

helm-helmfile-lint: helm-helmfile-pre-lint helm-helmfile-do-lint helm-helmfile-post-lint ## lint the Helmfiles

## TARGET: helm-publish
## SYNOPSIS: make helm-publish
## HOOKS: helm-pre-publish, helm-post-publish
## VARS:
##       HELM_CHARTS_TO_PUBLISH=<list of helm chart directories under ./charts/>
##       CAR_HELM_REPOSITORY_URL=<repository URL to publish to> - defaults to https://artefact.skao.int/repository/helm-internal
##
##  For a list of Helm Charts (HELM_CHARTS_TO_PUBLISH), add SKAO metadata to the package, build the package,
##  and publish it to the CAR_HELM_REPOSITORY_URL.  This process does not update
##  the Helm Chart version, which needs to be done independently (<chart name dir>/Chart.yaml).

helm-publish: helm-pre-publish helm-do-publish helm-post-publish  ## publish the Helm Charts to the repository

helm-do-publish:
	@. $(HELM_SUPPORT) ; helmChartPublish "$(HELM_CHARTS_TO_PUBLISH)"

## internal target for install yq
helm-install-yq:
	$(eval TMP_FILE:= $(shell mktemp))
	$(eval INSTALLED_YQ_VERSION := $(shell yq --version | awk '{print $$4}'))
	@if [ $(INSTALLED_YQ_VERSION) != v"$(HELM_YQ_VERSION)" ]; then \
		if which yq &> /dev/null; then \
			echo "helm-install-yq: WARNING: yq already installed with version $(INSTALLED_YQ_VERSION) instead of target version $(HELM_YQ_VERSION)"; \
		else \
			echo "helm-install-yq: Installing yq version $(HELM_YQ_VERSION) from https://github.com/mikefarah/yq/"; \
			if [ ! -d "$(HELM_YQ_INSTALL_DIR)" -o ! -w "$(HELM_YQ_INSTALL_DIR)" ]; then \
				echo "helm-install-yq: HELM_YQ_INSTALL_DIR ($(HELM_YQ_INSTALL_DIR)) is not a writable directory."; \
				echo "helm-install-yq: Please set HELM_YQ_INSTALL_DIR to a writable directory that is part of \$$PATH"; \
				exit 1; \
			fi; \
			curl -Lo $(TMP_FILE) https://github.com/mikefarah/yq/releases/download/v$(HELM_YQ_VERSION)/yq_linux_amd64 && \
			mv $(TMP_FILE) "$(HELM_YQ_INSTALL_DIR)/yq" && \
			chmod +x "$(HELM_YQ_INSTALL_DIR)/yq" && \
			if ! which yq &> /dev/null; then \
				echo "helm-install-yq: Could not find the installed yq in \$$PATH."; \
				echo "helm-install-yq: Please check if HELM_YQ_INSTALL_DIR ($(HELM_YQ_INSTALL_DIR)) is part of \$$PATH."; \
				exit 1; \
			fi \
		fi \
	else \
		echo "helm-install-yq: yq version $(HELM_YQ_VERSION) already installed"; \
	fi

helm-pre-build:

helm-post-build:

## TARGET: helm-build
## SYNOPSIS: make helm-build
## HOOKS: helm-pre-build, helm-post-build
## VARS:
##       HELM_CHARTS_TO_PUBLISH=<list of helm chart directories under ./charts/ for building packages>
##       HELM_CHARTS_CHANNEL=<repository channel> - GitLab repository channel, defaults to dev
##       HELM_BUILD_PUSH_SKIP=[yes|<empty>] - Flag to skip publish to GitLab repository. Should be set when used in local builds as well to skip any dev publishing
##       VERSION=<semver tag of helm charts> - defaults to release key in .release file
##       HELM_REPOSITORY_URL=<repository URL to publish to> - defaults to https://gitlab.com/api/v4/projects/${CI_PROJECT_ID}/packages/helm/api/${HELM_CHARTS_CHANNEL}/charts in pipeline, empty for local builds
##       HELM_YQ_VERSION=yq version to install - defaults to 4.14.1
##       HELM_YQ_INSTALL_DIR=directory for installing yq - defaults to /usr/local/bin.
##                           Only used if yq is not available in the current $PATH.
##                           This directory must be writable and part of $PATH.
##
##  For a list of Helm Charts (HELM_CHARTS_TO_PUBLISH), add SKAO metadata to the package, build the package,
##  and publish it to the CAR_HELM_REPOSITORY_URL.  This process does not update
##  the Helm Chart version, which needs to be done independently (<chart name dir>/Chart.yaml).

helm-build: helm-pre-build helm-do-build helm-post-build  ## build the Helm Charts and publish to the GitLab repository

helm-do-build: helm-install-yq
	@. $(HELM_SUPPORT) ; \
		VERSION=$(VERSION) \
		HELM_BUILD_PUSH_SKIP=$(HELM_BUILD_PUSH_SKIP) \
		HELM_CHARTS_CHANNEL=$(HELM_CHARTS_CHANNEL) \
		helmChartBuild "$(HELM_CHARTS_TO_PUBLISH)"

## TARGET: helm-check-deps
## SYNOPSIS: make helm-check
## HOOKS:
## VARS:
##       HELM_CHARTS_TO_PUBLISH=<list of helm chart directories under ./charts/ for building packages>
##
##  For a list of Helm Charts (HELM_CHARTS_TO_PUBLISH), check what is the latest version of the used sub-charts

helm-check-deps:
	@. $(HELM_SUPPORT) ; \
		helmChartCheckDependencies "$(HELM_CHARTS_TO_PUBLISH)"

## TARGET: helm-convert-to-helmfile
## SYNOPSIS: make helm-convert-to-helmfile
## HOOKS:
## VARS:
##       HELM_CHARTS_TO_CONVERT=<name of charts in the charts folder to convert to helmfile>
##
##  Convert an umbrella chart into helmfile

helm-convert-to-helmfile:
	@python3 $(HELM_CONVERT_CHART_TO_HELMFILE) --charts $(HELM_CHARTS_TO_CONVERT)

# end of switch to suppress targets for help
endif
endif
