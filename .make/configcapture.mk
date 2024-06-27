# include Makefile for configuration capture/export related targets

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
	NAME=$(shell basename $(CURDIR))
else
	NAME=$(PROJECT)
endif

# The SKAO gitlab project name to store the configuration in
CONFIG_CAPTURE_PROJECT ?= 

# images to use for the export "jobs"
CONFIG_CAPTURE_IMAGE ?= $(CAR_OCI_REGISTRY_HOST)/ska-k8s-config-exporter:0.0.3
DSCONFIG_IMAGE ?= $(CAR_OCI_REGISTRY_HOST)/ska-tango-images-tango-dsconfig:1.5.9
# JSON array - maybe from project-base json file
CONFIG_CAPTURE_ATTRIBUTES ?= '["versionId", "buildState"]'
CONFIG_CAPTURE_DIR ?= build/configuration## where config is stored
#CONFIG_CAPTURE_EXTRA_OPTS ?=
CONFIG_CAPTURE_TIMEOUT ?= 1m

ifeq ($(strip $(CONFIG_CAPTURE_PROJECT)),)
	CONFIG_CAPTURE_BRANCH=
	_publish_url=
else
	_export_url  = $(CI_SERVER_HOST)/$(CI_PROJECT_NAMESPACE)/$(CONFIG_CAPTURE_PROJECT)
	_publish_url = "https://ska-config-access-token:${SKA_CONFIG_ACCESS_TOKEN}@$(_export_url)"
	CONFIG_CAPTURE_BRANCH = "https://$(_export_url)/tree/$(CI_PROJECT_NAME)-$(CI_PIPELINE_ID)"## export for xray publishing
endif

SHELL=/usr/bin/env bash

.PHONY: config-capture-publish config-capture-pre-publish config-capture-post-publish config-capture-do-publish

## TARGET: config-capture-publish
## SYNOPSIS: make config-capture-publish
## HOOKS: config-capture-pre-publish, config-capture-post-publish
## VARS:
##       CONFIG_CAPTURE_DIR=<folder to write json config to>, defaults to build/configuration
##       CONFIG_CAPTURE_PROJECT=<the project to push the config to>
##       SKA_CONFIG_ACCESS_TOKEN=<token> - the access (push) token for CONFIG_CAPTURE_PROJECT
##       CI_PROJECT_NAME=
##       CI_PIPELINE_ID=
##
##  Publish the output of config-capture in a git repo

config-capture-publish: config-capture-pre-publish config-capture-do-publish config-capture-post-publish## Publish the output of config-capture in a git repo

config-capture-pre-publish:

config-capture-post-publish:

config-capture-do-publish:
	@if [ -z "$(CI_PIPELINE_ID)" ] || [ -z "$(SKA_CONFIG_ACCESS_TOKEN)" ]; then \
		echo "Can only publish to external repo from CI pipeline with an SKA_CONFIG_ACCESS_TOKEN!"; \
		exit 1; \
	fi
	@if [ -z "$(CONFIG_CAPTURE_PROJECT)" ]; then \
		echo "An external project name needs to be specified! Set CONFIG_CAPTURE_PROJECT"; \
		exit 1; \
	fi
	@if ! which yq &> /dev/null; then \
		echo "Getting yq..."; \
		wget https://github.com/mikefarah/yq/releases/download/v4.33.3/yq_linux_amd64 \
			-O /usr/local/bin/yq && chmod +x /usr/local/bin/yq; \
	fi
	git clone $(_publish_url) tmp; 
	@cd tmp; git config --global user.email "${GITLAB_USER_EMAIL}";git config --global user.name "${GITLAB_USER_NAME}"; \
	git checkout -b "$(CI_PROJECT_NAME)-$(CI_PIPELINE_ID)"; cp ../$(CONFIG_CAPTURE_DIR)/* .; \
	yq 'sort_keys(..)' -i -o json -M k8s.json; \
	git add .; git commit -m "config export from $(CI_PROJECT_NAME) pipeline"; \
	git push --all -o ci.skip; echo "Config exported to ${CONFIG_CAPTURE_BRANCH}"


.PHONY: config-pre-capture config-post-capture config-do-capture config-capture

## TARGET: config-capture
## SYNOPSIS: make config-capture
## HOOKS: config-pre-capture, config-post-capture
## VARS:
##       CONFIG_CAPTURE_DIR=<folder to write json config to>, defaults to build/configuration
##       CONFIG_CAPTURE_ATTRIBUTES=<json list containing tango attributes to capture>, defaults to '["versionId", "buildState"]'
##       CONFIG_CAPTURE_IMAGE=$(CAR_OCI_REGISTRY_HOST)/ska-k8s-config-exporter:0.0.3
##       DSCONFIG_IMAGE=$(CAR_OCI_REGISTRY_HOST)/ska-tango-images-tango-dsconfig:1.5.9
##       TANGO_HOST=<the Tango DB to inspect>
##       KUBE_NAMESPACE=<the namespace to inspect for config>
##
##  Capture dsconfig and k8s runtime versions for e.g. tango devices

config-capture: config-pre-capture config-do-capture config-post-capture## Capture dsconfig and k8s runtime versions for e.g. tango devices

config-pre-capture:

config-post-capture:

_dsconfig-capture:
	kubectl run -q -n $(KUBE_NAMESPACE) --rm -i --restart=Never --image $(DSCONFIG_IMAGE) \
		--env TANGO_HOST="$(TANGO_HOST)" --env NAMESPACE="$(KUBE_NAMESPACE)" \
		--pod-running-timeout=${CONFIG_CAPTURE_TIMEOUT} \
		dsconfig-export -- python -m dsconfig.dump | tee $(CONFIG_CAPTURE_DIR)/dsconfig.json >& /dev/null


_tango-capture:
	kubectl run -q -n $(KUBE_NAMESPACE) --rm -i --restart=Never --image $(CONFIG_CAPTURE_IMAGE) \
		--env TANGO_HOST="$(TANGO_HOST)" --env NAMESPACE="$(KUBE_NAMESPACE)" \
		--pod-running-timeout=${CONFIG_CAPTURE_TIMEOUT} config-export -- ska-config-export \
		-a $(CONFIG_CAPTURE_ATTRIBUTES) | tee $(CONFIG_CAPTURE_DIR)/k8s.json >& /dev/null

_check-role:
	@if ! $$(kubectl -n "$(KUBE_NAMESPACE)" get role -o name | grep ska-k8s-config-exporter &> /dev/null) ; then \
		echo "No ska-k8s-config-exporter chart found in ${KUBE_NAMESPACE}. Skipping capture."; \
		exit 1; \
	else \
		mkdir -p $(CONFIG_CAPTURE_DIR); \
	fi

config-do-capture: _check-role _dsconfig-capture _tango-capture

# end of switch to suppress targets for help
endif
endif
