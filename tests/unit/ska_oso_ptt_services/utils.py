"""
Utility functions to be used in tests
"""

from deepdiff import DeepDiff


def assert_json_is_equal(json_a, json_b, exclude_paths=None, exclude_regex_paths=None):
    """
    Utility function to compare two JSON objects
    """

    diff = DeepDiff(
        json_a,
        json_b,
        ignore_order=True,
        exclude_paths=exclude_paths,
        exclude_regex_paths=exclude_regex_paths,
    )

    # Raise an assertion error if there are differences
    assert {} == diff, f"JSON not equal: {diff}"
