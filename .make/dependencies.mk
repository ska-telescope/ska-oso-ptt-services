# Make targets for inter repository tooling

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

SHELL=/bin/bash
DEPS_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-dependencies-support

GIT_REMOTE ?= origin
TARGET_BRANCH ?= `git config --get init.defaultBranch || echo main` # defaults to main
AUTO_RELEASE ?= true  # if true, user input to commands will not be needed

SKART_DEPS_FILE ?= skart.toml
SKART_WAIT ?= 120
SKART_REQUERY ?= 5

SKART_TOML_EXISTS=$(shell [ -e $(SKART_DEPS_FILE) ] && echo 1 || echo 0 )
PYPROJECT_TOML_EXISTS=$(shell [ -e pyproject.toml ] && echo 1 || echo 0 )

.PHONY: deps-pre-update deps-do-update deps-post-update deps-update \
    deps-pre-update-release deps-post-update-release deps-do-update-release deps-update-release \
    deps-pre-update-devel deps-post-update-devel deps-do-update-devel deps-update-devel \
    deps-pre-patch-release deps-do-patch-release deps-post-patch-release deps-patch-release

deps-pre-update:

deps-post-update:

deps-do-update:
	@. $(DEPS_SUPPORT) ; \
	    SKART_TOML_EXISTS="$(SKART_TOML_EXISTS)" \
	    PYPROJECT_TOML_EXISTS="$(PYPROJECT_TOML_EXISTS)" \
		SKART_DEPS_FILE="$(SKART_DEPS_FILE)" \
		SKART_WAIT="$(SKART_WAIT)" \
		SKART_REQUERY="$(SKART_REQUERY)" \
		depsUpdate

## TARGET: deps-update
## SYNOPSIS: make deps-update
## HOOKS: deps-pre-update, deps-post-update
## VARS:
##       SKART_DEPS_FILE=<skart dependency information file (.toml)> (default skart.toml)
##       SKART_WAIT=<seconds to wait for pending/running pipelines> (default 5)
##       SKART_REQUERY=<seconds to re-query state while waiting> (default 120)
##
## Update pyproject.toml using ska-rt and then update poetry.lock.
## ska-rt: https://gitlab.com/ska-telescope/ska-rt

deps-update: deps-pre-update deps-do-update deps-post-update  ## Update latest dependencies using skart

deps-pre-update-release:

deps-post-update-release:

deps-do-update-release:
	@. $(DEPS_SUPPORT) ; \
	    SKART_TOML_EXISTS="$(SKART_TOML_EXISTS)" \
	    PYPROJECT_TOML_EXISTS="$(PYPROJECT_TOML_EXISTS)" \
		SKART_DEPS_FILE="$(SKART_DEPS_FILE)" \
		SKART_WAIT="$(SKART_WAIT)" \
		SKART_REQUERY="$(SKART_REQUERY)" \
		depsUpdate "release"

## TARGET: deps-update-release
## SYNOPSIS: make deps-update-release
## HOOKS: deps-pre-update-release, deps-post-update-release
## VARS:
##       SKART_DEPS_FILE=<skart dependency information file (.toml)> (default skart.toml)
##       SKART_WAIT=<seconds to wait for pending/running pipelines> (default 5)
##       SKART_REQUERY=<seconds to re-query state while waiting> (default 120)
##
## Update pyproject.toml using ska-rt and then update poetry.lock.
## ska-rt is used in "release" mode, it will update the packages
## listed in skart.toml with the given "release" specifications.
## ska-rt: https://gitlab.com/ska-telescope/ska-rt

deps-update-release: deps-pre-update-release deps-do-update-release deps-post-update-release ## Update dependencies from released versions


deps-pre-update-devel:

deps-post-update-devel:

deps-do-update-devel:
	@. $(DEPS_SUPPORT) ; \
	    SKART_TOML_EXISTS="$(SKART_TOML_EXISTS)" \
	    PYPROJECT_TOML_EXISTS="$(PYPROJECT_TOML_EXISTS)" \
		SKART_DEPS_FILE="$(SKART_DEPS_FILE)" \
		SKART_WAIT="$(SKART_WAIT)" \
		PROJECT_NAME="$(PROJECT_NAME)" \
		PROJECT_PATH="$(PROJECT_PATH)" \
		ARTEFACT_TYPE="$(ARTEFACT_TYPE)" \
		SKART_REQUERY="$(SKART_REQUERY)" \
		BRANCH_NAME="$(BRANCH_NAME)" \
		depsDevelBranch

## TARGET: deps-update-devel
## SYNOPSIS: make deps-update-devel
## HOOKS: deps-pre-update-devel, deps-post-update-devel
## VARS:
##       BRANCH_NAME=<name of build branch. Will be created or checked out.> (mandatory)
##       SKART_WAIT=<seconds to wait for pending/running pipelines> (default 120)
##       SKART_REQUERY=<seconds to re-query state while waiting> (default 5)
##       PROJECT_NAME=<name of project to be released> (mandatory)
##       PROJECT_PATH=<project path relative to https://gitlab.com/> (mandatory)
##       ARTEFACT_TYPE=<type of released artefact: python or oci> (mandatory)
##
## Updates pyproject.toml with development versions using skart and then updates poetry.lock.
## The updated branch is pushed to gitlab and this function will wait for a pipeline build
## according to --wait and --requery parameters

deps-update-devel: deps-pre-update-devel deps-do-update-devel deps-post-update-devel ## Update development branch dependencies and build new/updated branch using Gitlab


deps-pre-patch-release:

deps-post-patch-release:

deps-do-patch-release:
	@. $(DEPS_SUPPORT) ; \
	    SKART_TOML_EXISTS="$(SKART_TOML_EXISTS)" \
	    PYPROJECT_TOML_EXISTS="$(PYPROJECT_TOML_EXISTS)" \
		SKART_DEPS_FILE="$(SKART_DEPS_FILE)" \
		SKART_WAIT="$(SKART_WAIT)" \
		SKART_REQUERY="$(SKART_REQUERY)" \
		TARGET_BRANCH="$(TARGET_BRANCH)" \
		PROJECT_NAME="$(PROJECT_NAME)" \
		PROJECT_PATH="$(PROJECT_PATH)" \
		ARTEFACT_TYPE="$(ARTEFACT_TYPE)" \
		AUTO_RELEASE="$(AUTO_RELEASE)" \
		GIT_REMOTE="$(GIT_REMOTE)" \
		depsPatchRelease

## TARGET: deps-patch-release
## SYNOPSIS: make deps-patch-release
## HOOKS: deps-pre-patch-release, deps-post-patch-release
## VARS:
##       SKART_DEPS_FILE=<skart dependency information file (.toml)> (default skart.toml)
##       SKART_WAIT=<seconds to wait for pending/running pipelines> (default 5)
##       SKART_REQUERY=<seconds to re-query state while waiting> (default 120)
##       TARGET_BRANCH=<target branch that changes are compared to> (default 'main')
##       PROJECT_NAME=<name of project to be released> (mandatory)
##       PROJECT_PATH=<project path relative to https://gitlab.com/> (mandatory)
##       ARTEFACT_TYPE=<type of released artefact: python or oci> (mandatory)
##       AUTO_RELEASE=<if true, no user input is needed for creating the tag> (default true)
##
## Updates pyproject.toml and update poetry.lock using `depsUpdate "release"`.
## Then check if there are difference on the git repository.
## Bumps the patch release version by incrementing the current semver patch level.
## Creates a git tag automatically for the current calculated $VERSION.
## Pushes outstanding changes to git including tags.

deps-patch-release: deps-pre-patch-release deps-do-patch-release deps-post-patch-release ## Update dependencies from released versions, bumps patch release version and pushes to Gitlab

# end of switch to suppress targets for help
endif
endif
