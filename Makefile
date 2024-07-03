#
# CAR_OCI_REGISTRY_HOST, CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME are combined to define
# the Docker tag for this project. The definition below inherits the standard
# value for CAR_OCI_REGISTRY_HOST (=artefact.skao.int) and overwrites
# PROJECT_NAME to give a final Docker tag of artefact.skao.int/ska-oso-ptt-services
#
CAR_OCI_REGISTRY_HOST ?= artefact.skao.int
CAR_OCI_REGISTRY_USERNAME ?= ska-telescope
PROJECT_NAME = ska-oso-ptt-services
KUBE_NAMESPACE ?= ska-oso-ptt-services
RELEASE_NAME ?= test

# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)
K8S_CHART = ska-oso-ptt-services-umbrella

POSTGRES_HOST ?= $(RELEASE_NAME)-postgresql
K8S_CHART_PARAMS += \
  --set ska-db-oda-umbrella.pgadmin4.serverDefinitions.servers.firstServer.Host=$(POSTGRES_HOST)

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS += --set ska-oso-ptt-services.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-oso-ptt-services.rest.image.registry=$(CI_REGISTRY)/ska-telescope/oso/ska-oso-ptt-services
endif

# Set cluster_domain to minikube default (cluster.local) in local development
# (CI_ENVIRONMENT_SLUG should only be defined when running on the CI/CD pipeline)
ifeq ($(CI_ENVIRONMENT_SLUG),)
K8S_CHART_PARAMS += --set global.cluster_domain="cluster.local"
endif

# For the staging environment, make k8s-install-chart-car will pull the chart from CAR so we do not need to
# change any values
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'staging')
ifneq ($(ENV_CHECK),)
endif

# unset defaults so settings in pyproject.toml take effect
PYTHON_SWITCHES_FOR_BLACK =
PYTHON_SWITCHES_FOR_ISORT =
PYTHON_SWITCHES_FOR_PYLINT =

# Restore Black's preferred line length which otherwise would be overridden by
# System Team makefiles' 79 character default
PYTHON_LINE_LENGTH = 88

# Set the k8s test command run inside the testing pod to only run the component
# tests (no k8s pod deployment required for unit tests)

# Set python-test make target to run unit tests and not the component tests
PYTHON_TEST_FILE = tests/unit/

# include makefile to pick up the standard Make targets from the submodule
-include .make/base.mk
-include .make/python.mk
-include .make/oci.mk
-include .make/k8s.mk

-include .make/helm.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

REST_POD_NAME=$(shell kubectl get pods -o name -n $(KUBE_NAMESPACE) -l app=ska-oso-ptt-services,component=rest | cut -c 5-)


MINIKUBE_NFS_SHARES_ROOT ?=

rest: ## start PTT REST server
	docker run --rm -p 5000:5000 --name=$(PROJECT_NAME) $(IMAGE_TO_TEST) gunicorn --chdir src \
		--bind 0.0.0.0:5000 --logger-class=ska_oso_ptt_services.rest.wsgi.UniformLogger --log-level=$(LOG_LEVEL) ska_oso_ptt_services.rest.wsgi:app


dev-up: K8S_CHART_PARAMS = \
	--set ska-oso-ptt-services.rest.image.tag=$(VERSION) \
	--set ska-oso-ptt-services.rest.ingress.enabled=true
dev-up: k8s-namespace k8s-install-chart k8s-wait ## bring up developer deployment

dev-down: k8s-uninstall-chart k8s-delete-namespace  ## tear down developer deployment

# The docs build fails unless the ska-oso-ptt-services package is installed locally as importlib.metadata.version requires it.
docs-pre-build:
	poetry install --only-root
