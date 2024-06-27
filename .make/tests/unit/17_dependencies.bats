#!/usr/bin/env bats

# Load a library from the `${BATS_TEST_DIRNAME}/test_helper' directory.
#
# Globals:
#   none
# Arguments:
#   $1 - name of library to load
# Returns:
#   0 - on success
#   1 - otherwise
load_lib() {
  local name="$1"
  load "../../scripts/${name}/load"
}

load_lib bats-support
load_lib bats-assert

@test 'DEPENDENCIES: pyproject.toml update' {
    cp -f pyproject.toml.default pyproject.toml
    run make -f ../tests/Makefile deps-update SKART_DEPS_FILE=../tests/resources/skart.toml
    echo "$output"
    assert_success
}

@test 'DEPENDENCIES: pyproject.toml update with release' {
    cp -f pyproject.toml.default pyproject.toml
    run make -f ../tests/Makefile deps-update-release SKART_DEPS_FILE=../tests/resources/skart.toml
    echo "$output"
    assert_success
}

@test 'DEPENDENCIES: pipelineWait function succeeds' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol ARTEFACT_TYPE=oci tag="0.11.0" pipelineWait"
  echo "$output"
  assert_success
}

@test 'DEPENDENCIES: missing PROJECT_NAME environment variable fails depsPatchRelease function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol ARTEFACT_TYPE=oci depsPatchRelease"
  echo "$output"
  assert_failure
  assert_output -p "PROJECT_NAME environment variable has to be provided."
}

@test 'DEPENDENCIES: missing PROJECT_PATH environment variable fails depsPatchRelease function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol ARTEFACT_TYPE=oci depsPatchRelease"
  echo "$output"
  assert_failure
  assert_output -p "PROJECT_PATH environment variable has to be provided."
}

@test 'DEPENDENCIES: missing ARTEFACT_TYPE environment variable fails depsPatchRelease function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol depsPatchRelease"
  echo "$output"
  assert_failure
  assert_output -p "ARTEFACT_TYPE environment variable has to be provided."
}

@test 'DEPENDENCIES: missing PROJECT_NAME environment variable fails depsDevelBranch function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol ARTEFACT_TYPE=oci depsDevelBranch"
  echo "$output"
  assert_failure
  assert_output -p "PROJECT_NAME environment variable has to be provided."
}

@test 'DEPENDENCIES: missing PROJECT_PATH environment variable fails depsDevelBranch function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol ARTEFACT_TYPE=oci depsDevelBranch"
  echo "$output"
  assert_failure
  assert_output -p "PROJECT_PATH environment variable has to be provided."
}

@test 'DEPENDENCIES: missing ARTEFACT_TYPE environment variable fails depsDevelBranch function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol depsDevelBranch"
  echo "$output"
  assert_failure
  assert_output -p "ARTEFACT_TYPE environment variable has to be provided."
}
@test 'DEPENDENCIES: missing BRANCH_NAME environment variable fails depsDevelBranch function' {
  run bash -c "cd .. && . .make-dependencies-support ; PROJECT_NAME=ska-sdp-proccontrol PROJECT_PATH=ska-telescope/sdp/ska-sdp-proccontrol ARTEFACT_TYPE=oci depsDevelBranch"
  echo "$output"
  assert_failure
  assert_output -p "BRANCH_NAME environment variable has to be provided."
}
