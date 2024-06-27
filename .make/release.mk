#
#   Original Copyright 2015  Xebia Nederland B.V.
#   Further contibutions by various, SKA Observatory, 2021
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

# include Makefile for release related targets and variables

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

CONFIG := $(CONFIG)
ALLOWED_CONFIGS := $(ALLOWED_CONFIGS)

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support

ifeq ($(strip $(CAR_OCI_REGISTRY_HOST)),)
  CAR_OCI_REGISTRY_HOST = artefact.skao.int
endif

ifneq ($(strip $(CONFIG)),)
ifneq ($(strip $(ALLOWED_CONFIGS)),)
ifeq ($(filter $(CONFIG), $(ALLOWED_CONFIGS)),)
$(error `CONFIG` must be one of $(ALLOWED_CONFIGS))
endif
endif
endif

#export DEBUG_DIRTY=true

VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getTag)

RELEASE_CONTEXT_DIR ?=
RELEASE_FILE=$(shell . $(RELEASE_SUPPORT); CONFIG=${CONFIG} setReleaseFile; getReleaseFile)

SHELL=/usr/bin/env bash

DOCKER_BUILD_CONTEXT=.
DOCKER_FILE_PATH=Dockerfile

CHANGELOG_FILE ?= CHANGELOG.md
CHANGELOG_CONFIG ?= ".chglog/config.yml"
CHANGELOG_TEMPLATE ?= ".chglog/CHANGELOG.tpl.md"

.PHONY: release python-set-release bump-patch-release bump-minor-release bump-major-release set-release check-status check-release show-version create-git-tag push-git-tag check-release helm-update-deps helm-set-release .release generate-changelog add-author-notes


# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

# Setup the .release file in the RELEASE_CONTEXT_DIR
.release:
	@if [ -n "$(RELEASE_CONTEXT_DIR)" ]; then \
		export RELEASE_CONTEXT_DIR="$(RELEASE_CONTEXT_DIR)/" ; \
	fi; \
	if [ -n "$(RELEASE_FILE)" ]; then \
		export RELEASE_FILE="$(RELEASE_FILE)" ; \
	fi; \
	if [[ ! -f "$${RELEASE_CONTEXT_DIR}$${RELEASE_FILE}" ]]; then \
		echo "release=0.0.0" > "$${RELEASE_CONTEXT_DIR}$${RELEASE_FILE}"; \
		echo "tag=$(NAME)-0.0.0" >> "$${RELEASE_CONTEXT_DIR}$${RELEASE_FILE}"; \
		echo INFO: "$${RELEASE_CONTEXT_DIR}$${RELEASE_FILE}" created; \
		cat "$${RELEASE_CONTEXT_DIR}$${RELEASE_FILE}"; \
	fi

## TARGET: show-version
## SYNOPSIS: make show-version
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  show current calculated $VERSION.
##  RELEASE_CONTEXT defaults to the root folder of the project, but can be overriden
##  if .release files are required per image to build.  See ska-tango-images for an example.

show-version: .release ## Show current release version
	@. $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getVersion

## TARGET: bump-patch-release
## SYNOPSIS: make bump-patch-release
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Increment the current semver patch level using the current calculated $VERSION.
##  RELEASE_CONTEXT defaults to the root folder of the project, but can be overriden
##  if .release files are required per image to build.  See ska-tango-images for an example.
## NOTE all bump-*-release targets call set-release which has pre and post hooks

bump-patch-release: VERSION := $(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; nextPatchLevel)
bump-patch-release: .release set-release  ## bump patch release

## TARGET: bump-minor-release
## SYNOPSIS: make bump-minor-release
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Increment the current semver minor level, and reset patch level to 0 using
##  the current calculated $VERSION.
##  RELEASE_CONTEXT defaults to the root folder of the project, but can be overriden
##  if .release files are required per image to build.  See ska-tango-images for an example.
## NOTE all bump-*-release targets call set-release which has pre and post hooks

bump-minor-release: VERSION := $(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; nextMinorLevel)
bump-minor-release: .release set-release  ## bump minor release

## TARGET: bump-major-release
## SYNOPSIS: make bump-major-release
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Increment the current semver major level, and reset minor and patch levels to 0 using
##  the current calculated $VERSION.
##  RELEASE_CONTEXT defaults to the root folder of the project, but can be overriden
##  if .release files are required per image to build.  See ska-tango-images for an example.
## NOTE all bump-*-release targets call set-release which has pre and post hooks

bump-major-release: VERSION := $(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; nextMajorLevel)
bump-major-release: .release set-release  ## bump major release

## TARGET: python-set-release
## SYNOPSIS: make python-set-release
## HOOKS: python-pre-set-release, python-post-set-release
## VARS: none
##
##  Set the Python package version in pyproject.toml based on the current calculated $VERSION.

python-pre-set-release:

python-post-set-release:

python-do-set-release:
	@. $(RELEASE_SUPPORT) ; ! hasChanges "RELEASE_CHECK" ;
	@if [[ -f pyproject.toml ]]; then \
		poetry version $(VERSION); \
	else \
		echo 'no pyproject.toml to update!'; \
		exit 1; \
	fi

python-set-release: python-pre-set-release python-do-set-release python-post-set-release ## set the Python package version

## TARGET: helm-update-deps
## SYNOPSIS: make helm-update-deps
## HOOKS: helm-pre-update-deps, helm-post-update-deps
## VARS: none
##
##  Set the versions of Helm Chart dependences ./charts/**/Chart.yaml based
##  on the current calculated $VERSION.

helm-pre-update-deps:

helm-post-update-deps:

helm-do-update-deps:
	@echo "helm-update-deps: $(UPDATE_VERSION)"
	@. $(RELEASE_SUPPORT) ; updateHelmDeps ${UPDATE_VERSION} "${HELM_CHARTS_TO_PUBLISH}"

helm-update-deps: helm-install-yq helm-pre-update-deps helm-do-update-deps helm-post-update-deps ## update the versions of Helm Chart dependencies

## TARGET: helm-set-release
## SYNOPSIS: make helm-set-release
## HOOKS: helm-pre-set-release, helm-post-set-release
## VARS: none
##
##  Set the Helm Chart versions and appVersion in ./charts/**/Chart.yaml based
##  on the current calculated $VERSION.

helm-pre-set-release:

helm-post-set-release:

helm-do-set-release:
	@if [ -d "./charts" ]; then \
		. $(RELEASE_SUPPORT) ; ! hasChanges "RELEASE_CHECK"; \
		echo "helm-set-release: $(VERSION)"; \
		. $(RELEASE_SUPPORT) ; setHelmRelease $(VERSION) "$(HELM_CHARTS_TO_PUBLISH)"; \
		. $(RELEASE_SUPPORT) ; updateHelmDeps ${VERSION} "${HELM_CHARTS_TO_PUBLISH}"; \
	else \
		echo "helm-set-release: there are no charts to update!"; \
	fi

helm-set-release: helm-install-yq helm-pre-set-release helm-do-set-release helm-post-set-release ## set the Helm Chart version and appVersion

## TARGET: check-release
## SYNOPSIS: make check-release
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Check if there is a git tag for the current calculated $VERSION.

check-release: .release ## check if there's a tag in Git for the current version
	@. $(RELEASE_SUPPORT) ; tagExists $(TAG) || (echo "ERROR: version not yet tagged in git. make [minor,major,patch]-release." >&2 && exit 1) ;
	@. $(RELEASE_SUPPORT) ; ! differsFromRelease $(TAG) || (echo "ERROR: current directory differs from tagged $(TAG). make [minor,major,patch]-release." ; exit 1)

## TARGET: create-git-tag
## SYNOPSIS: make create-git-tag
## HOOKS: none
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##       AUTO_RELEASE=<true or false>. Used to skip interactive prompts. Default false.
##            if AUTO_RELEASE is true, then the Jira ticket ID for commit is read from the JIRA_TICKET variable
##
##  Create a git tag for the current calculated $VERSION.
##  Setting AUTO_RELEASE to true will automatically commit the messages without JIRA ID and prompts.

git-create-tag: create-git-tag  ## create git tag for current version
create-git-tag: .release show-version
	@. $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; \
	if hasChanges; then \
	    if [ "$(AUTO_RELEASE)" = "true" ]; then \
	      test -n "$$(git status -s | grep -v -E '^\?\? ')"; \
	      hc_result=$$?; \
	      if [[ $hc_result -eq 0 ]]; then \
			  echo "OK - commiting changes..."; \
			  git commit -a -m "$(JIRA_TICKET): bumped version to $$(. $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getRelease)"; \
	      fi; \
	    else \
			read -p "Do you wish to continue (will commit outstanding changes) [N/y]: " SHALL_WE; \
			if [[ "y" == "$${SHALL_WE}" ]] || [[ "Y" == "$${SHALL_WE}" ]]; then \
				test -n "$$(git status -s | grep -v -E '^\?\? ')"; \
				hc_result=$$?; \
				if [[ $hc_result -eq 0 ]]; then \
					read -p "Tell me your Jira Ticket ID (REL-999): " JIRA_TICKET; \
					echo "OK - commiting changes..."; \
					git commit -a -m "$${JIRA_TICKET}: bumped version to $$(. $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getRelease)"; \
				fi; \
			else \
				echo "OK - aborting"; \
				exit 1; \
			fi; \
		fi; \
	fi; \
	createGitTag || (echo "ERROR: Some error in creating tag" >&2 && exit 1)

## TARGET: git-push-tag
## SYNOPSIS: make git-push-tag
## HOOKS: none
## VARS: none
##
##  Push outstanding changes to git including tags.

git-push-tag: push-git-tag  ## push git and tags
push-git-tag: show-version
	@if [[ -n "$(shell git remote -v)" ]]; then \
		git push; \
		git push --tags; \
	else \
		echo 'no remote to push tags to'; \
	fi

## TARGET: set-release
## SYNOPSIS: make set-release TAG=<semver string>
## HOOKS: pre-set-release, post-set-release
## VARS:
##       TAG=<semantic version  string> - default is calculated VERSION based on .release
##
##  Utility target for updating .release file - not normally used directly.

pre-set-release:

post-set-release:

do-set-release:
	@. $(RELEASE_SUPPORT) ; ! hasChanges "RELEASE_CHECK";
	@. $(RELEASE_SUPPORT) ; ! tagExists $(TAG) || (echo "ERROR: tag $(TAG) for version $(VERSION) already tagged in git" >&2 && exit 1) ;
	@echo ""
	@echo "		🔥 ATTENTION 🔥: Please beware this is the release file being used: $(RELEASE_FILE)"
	@echo ""
	@echo "set-release: $(VERSION)"
	@. $(RELEASE_SUPPORT) ; setRelease $(VERSION)
	@. $(RELEASE_SUPPORT) ; targetExists python-build && make python-set-release || echo "python target not included, nothing to release here!" 
	@. $(RELEASE_SUPPORT) ; targetExists helm-build && make helm-set-release || echo "helm target not included, nothing to release here!"
	@echo "update-doc-release: $(VERSION)"
	@. $(RELEASE_SUPPORT) ; updateReleaseDoc $(VERSION)

set-release: TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; CONFIG=${CONFIG} setReleaseFile; getTag $(VERSION))
set-release: pre-set-release do-set-release post-set-release ## Set the release from $VERSION in .release

## TARGET: check-status
## SYNOPSIS: make check-status
## HOOKS: none
## VARS: none
##
##  Check for outstanding changes in the current git repository.  This excludes
##  changes to version update files such as .release, Chart.yaml, and pyproject.tonl

check-status: ## check if there are still outstanding changes
	@. $(RELEASE_SUPPORT) ; ! hasChanges ;

## TARGET: generate-changelog
## SYNOPSIS: generate-changelog
## HOOKS: none
## VARS:
##       OCI_IMAGES_TO_PUBLISH=<default: OCI_IMAGES> - list of oci images to publish
##       HELM_CHARTS_TO_PUBLISH=<default: HELM_CHARTS> - list of helm charts to publish
##       RAW_PKGS_TO_PUBLISH=<default: RAW_PKGS> - list of raw packages to publish
##       JIRA_USERNAME=<default in pipelines: marvin username> - used for Changelog generation
##       JIRA_PASSWORD=<default in pipelines: marvin password> - used for Changelog generation
##       JIRA_URL=<default in pipelines: https://jira.skatelescope.org> - used for Changelog generation
##       CHANGELOG_FILE=<default : CHANGELOG.md> - name of the changelog file
##       CHANGELOG_CONFIG=<default: .chglog/config.yml> - location of the chglog config file
##       CHANGELOG_TEMPLATE=<default : .chglog/CHANGELOG.tpl.md> - location of the chglog template file
##
##  Appends to the CHANGELOG_FILE the changes from the tag before CI_COMMIT_TAG until CI_COMMIT_TAG
##  With that file creates a release on gitlab under CI_COMMIT_TAG with the artefacts appended as assets to the release

generate-changelog:
	@. $(RELEASE_SUPPORT); OCI_IMAGES_TO_PUBLISH="${OCI_IMAGES_TO_PUBLISH}" HELM_CHARTS_TO_PUBLISH="${HELM_CHARTS_TO_PUBLISH}" \
	RAW_PKGS_TO_PUBLISH="$(RAW_PKGS_TO_PUBLISH)" CONAN_PKGS_TO_PUBLISH="$(CONAN_PKGS_TO_PUBLISH)" CONAN_USER="$(CONAN_USER)" CONAN_CHANNEL="$(CONAN_CHANNEL)" \
	CHANGELOG_FILE=$(CHANGELOG_FILE) CHANGELOG_CONFIG=$(CHANGELOG_CONFIG) \
	CHANGELOG_TEMPLATE=$(CHANGELOG_TEMPLATE) generateChangelog

generate-release-notes:
	@. $(RELEASE_SUPPORT); CHANGELOG_FILE=$(CHANGELOG_FILE) CHANGELOG_CONFIG=$(CHANGELOG_CONFIG) \
	CHANGELOG_TEMPLATE=$(CHANGELOG_TEMPLATE) EXECUTED_FROM_MAKE_TARGET=true generateReleaseNotes

# end of switch to suppress targets for help
endif
endif
