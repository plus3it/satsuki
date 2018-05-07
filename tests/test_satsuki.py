# test_pyppyn.py

import pytest
import uuid
import os

from satsuki import Arguments, ReleaseMgr

TEST_VERBOSE = True
TEST_BODY = str(uuid.uuid1())
TEST_SLUG = "YakDriver/satsuki"
TEST_TAG = "Test-v" + TEST_BODY[:6]
TEST_REL_NAME = "Test Release v" + TEST_BODY[:6]
TEST_COMMITISH = "dd3f3843d9c691b22bd2961d5958233f3b45552f"
TEST_FILENAME = 'tests/release-asset.exe'

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

def test_upload_file(token):
    with open(TEST_FILENAME, 'wb') as fout:
        fout.write(os.urandom(1024000))

    args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        file_file = "tests/test.file"
    )

    ul_rel = ReleaseMgr(args)
    assert ul_rel.execute()
    
def test_delete_release(arguments_base):

    delete_args = Arguments(
        verbose = TEST_VERBOSE,
        token = arguments_base.api_token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        command = Arguments.COMMAND_DELETE
    )

    del_rel = ReleaseMgr(delete_args)
    assert del_rel.execute()