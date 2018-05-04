# test_pyppyn.py

import pytest
import uuid

from satsuki import Arguments, ReleaseMgr

TEST_VERBOSE = True
TEST_BODY = str(uuid.uuid1())
TEST_SLUG = "YakDriver/mjukvarulage"
TEST_TAG = "v" + TEST_BODY[:6]
TEST_REL_NAME = "Release name " + TEST_BODY[:4]
TEST_COMMITISH = "dcdbbf3b628995baca977e2f67da2341e4714a7b"

def test_blank_arguments():
    """ Returns an Arguments instance with nothing set. """
    with pytest.raises(PermissionError):
        Arguments()

@pytest.fixture
def arguments_base(token):
    """ Basic arguments with authorization (must provide token) """
    return Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        body = TEST_BODY,
        rel_name = TEST_REL_NAME,
        commitish = TEST_COMMITISH
    )

def test_create_release(arguments_base):
    rm = ReleaseMgr(arguments_base)
    if rm.execute(): # <== should create
        compare_args = Arguments(
            verbose = TEST_VERBOSE,
            token = arguments_base.api_token,
            slug = TEST_SLUG,
            tag = TEST_TAG
        )

    assert compare_args.body == TEST_BODY \
        and compare_args.rel_name == TEST_REL_NAME

def test_get_latest(arguments_base):
    rm = ReleaseMgr(arguments_base)
    if rm.execute(): # <== should create
        compare_args = Arguments(
            verbose = TEST_VERBOSE,
            token = arguments_base.api_token,
            slug = TEST_SLUG,
            latest = True
        )

    assert compare_args.tag == TEST_TAG \
        and compare_args.body == TEST_BODY \
        and compare_args.rel_name == TEST_REL_NAME