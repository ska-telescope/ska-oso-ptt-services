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

@test 'config capture: test config capture skip' {
    run make -f ../tests/Makefile config-capture
    assert_output -p "Skipping capture"
    assert_failure
}

@test 'onfig publish: test config capture publish fail env - no token' {
    run make -f ../tests/Makefile config-capture-publish
    echo "$output"
    assert_output -p "SKA_CONFIG_ACCESS_TOKEN"
    assert_failure
}

@test 'k8s config publish: test config capture publish fail env - no project' {
    run make -f ../tests/Makefile config-capture-publish \
      SKA_CONFIG_ACCESS_TOKEN=abc CI_PIPELINE_ID=123
    echo "$output"
    assert_output -p "CONFIG_CAPTURE_PROJECT"
    assert_failure
}
