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

@test 'TMDATA: package with metadata' {
    mkdir tmdata
    echo "test_file_contents" > tmdata/test_file_name
    run make -f ../tests/Makefile tmdata-package
    echo "$output"
    assert_success
}
