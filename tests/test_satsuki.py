# test_pyppyn.py

import pytest
import uuid
import os
import github
import platform
import requests

from satsuki import Arguments, ReleaseMgr, HASH_FILE
from string import Template

TEST_VERBOSE = True
TEST_BODY = str(uuid.uuid1())
TEST_SLUG = "YakDriver/satsuki"
TEST_TAG = "Test-v" + TEST_BODY[:6]
TEST_REL_NAME = "Test Release v" + TEST_BODY[:6]
TEST_COMMITISH = "5aacf6b744ec379afafbf3bac2131474a464ee9d"
TEST_FILENAME = 'tests/release-asset.exe'
TEST_DOWNLOAD = 'tests/downloaded-asset'
TEST_DOWNLOAD_SHA = 'tests/downloaded-asset-sha'
TEST_RECREATE_COMMITISH = "6ba16ceff2efa08fa01c1471c739a6febc2343b6"

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
    rm.execute() # <== should create
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
    rm.execute() # <== should create
    compare_args = Arguments(
        verbose = TEST_VERBOSE,
        token = arguments_base.api_token,
        slug = TEST_SLUG,
        latest = True
    )

    if compare_args.tag == TEST_TAG:
        assert compare_args.tag == TEST_TAG \
            and compare_args.body == TEST_BODY \
            and compare_args.rel_name == TEST_REL_NAME
    else:
        # a real tag has gotten in first, forget the test
        assert True


def test_upload_file_no_sha(token):
    with open(TEST_FILENAME, 'wb') as fout:
        fout.write(os.urandom(1024000))

    args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        files_file = "tests/test.file"
    )

    ul_rel = ReleaseMgr(args)
    ul_rel.execute()
    assert True


def test_download_file_no_sha(token):
    """
    Doesn't directly check Satsuki but rather the effects of Satsuki
    and creation of file and no SHA hash.
    """

    # github => repo => release => asset_list => asset => url => download

    gh = github.Github(token, per_page=100)
    repo = gh.get_repo(TEST_SLUG, lazy=False)
    release = repo.get_release(TEST_TAG)
    asset_list = release.get_assets()
    sha_filename = Template(HASH_FILE).safe_substitute({
        'platform': platform.system().lower()
    })

    pass_test = True

    for check_asset in asset_list:
        # look through list of assets for uploaded file and sha file

        if check_asset.name == sha_filename:

            pass_test = False

    assert pass_test


# Order is important, no sha tests upload, recreate gets rid of upload,
# and then upload can be done again
def test_recreate_release(arguments_base):
    
    recreate_args = Arguments(
        verbose = TEST_VERBOSE,
        token = arguments_base.api_token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        recreate = True,
        commitish = TEST_RECREATE_COMMITISH
    )
    new = ReleaseMgr(recreate_args)
    new.execute() # <== should recreate

    # really the test is if it makes it this far
    assert recreate_args.target_commitish == TEST_RECREATE_COMMITISH


def test_upload_file(token):
    with open(TEST_FILENAME, 'wb') as fout:
        fout.write(os.urandom(1024000))

    args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        files_file = "tests/test.file",
        file_sha = Arguments.FILE_SHA_SEP_FILE
    )

    ul_rel = ReleaseMgr(args)
    ul_rel.execute()
    assert True


def test_download_file(token):
    """
    Doesn't directly check Satsuki but rather the effects of Satsuki
    and creation of file and SHA hash.
    """

    # github => repo => release => asset_list => asset => url => download

    gh = github.Github(token, per_page=100)
    repo = gh.get_repo(TEST_SLUG, lazy=False)
    release = repo.get_release(TEST_TAG)
    asset_list = release.get_assets()
    sha_filename = Template(HASH_FILE).safe_substitute({
        'platform': platform.system().lower()
    })

    assets_calculated_sha = 'notasha'
    sha_dict = {}

    for check_asset in asset_list:
        # look through list of assets for uploaded file and sha file

        if check_asset.name == os.path.basename(TEST_FILENAME):

            # the uploaded asset
            r = requests.get(check_asset.browser_download_url)
            open(TEST_DOWNLOAD, 'wb').write(r.content)
            
            # recalc hash of downloaded file
            assets_calculated_sha = Arguments.get_hash(TEST_DOWNLOAD)                

        elif check_asset.name == sha_filename:

            # the sha hash file
            r = requests.get(check_asset.browser_download_url)
            sha_dict = r.json()

    assert assets_calculated_sha == sha_dict[os.path.basename(TEST_FILENAME)]


def test_delete_release(token):

    delete_args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        command = Arguments.COMMAND_DELETE,
        include_tag = True
    )

    del_rel = ReleaseMgr(delete_args)
    del_rel.execute()
    assert True
