# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Test Satsuki module."""
import os
import uuid
from unittest.mock import patch, MagicMock

import pytest
import github
import satsuki
from satsuki import Arguments, ReleaseMgr

TEST_UUID = str(uuid.uuid1())
TEST_SLUG = "plus3it/satsuki-tests"
TEST_TAG = "Test-v" + TEST_UUID[:6]
TEST_COMMITISH = "f25a79b856433fe8c35ac4050a70dd53dc6e684f"


def test_sha_hash():
    """Test getting the sha hash for a test file. """
    assert Arguments.get_hash(
        os.path.join('tests', 'sha_hash_test.txt')) == \
        '809838efd41698422636fb2df8bebe2a7e8c29a3baf109b3bdceed6812266903'


def test_sha_hash_nonexistent_file():
    """Test what happens when getting a sha hash for nonexistent file. """
    assert Arguments.get_hash('nonexistent_file.xyz') is None


def test_no_slug_arguments():
    """Test missing slug. """
    restore_enviro = os.environ

    if os.environ.get('TRAVIS_REPO_SLUG', False):
        del os.environ['TRAVIS_REPO_SLUG']
    if os.environ.get('APPVEYOR_REPO_NAME', False):
        del os.environ['APPVEYOR_REPO_NAME']

    with pytest.raises(AttributeError):
        Arguments(token='abc', empty_arg=None)

    os.environ = restore_enviro


def test_bad_command():
    """Test providing a bad command. """
    with pytest.raises(AttributeError):
        Arguments(token='abc', slug=TEST_SLUG, tag=TEST_TAG, command='bad')


def test_gb_info():
    """Test providing a gravitybee info file. """
    with pytest.raises(ReferenceError):
        Arguments(
            token='abc',
            slug=TEST_SLUG,
            tag=TEST_TAG,
            gb_info_file=os.path.join('tests', 'gravitybee-info.json'))


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_get_repo(mock_get_repo):
    """Test getting a repo for Github API. """
    mock_release = MagicMock()
    mock_release.tag_name = 'Mocked tag'

    mock_get_repo.return_value.get_release.return_value = mock_release

    Arguments(
        token='abc',
        slug=TEST_SLUG,
        tag=TEST_TAG)

    mock_get_repo.return_value.get_release.assert_called_once()


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_get_latest_repo(mock_get_repo):
    """Test getting latest release. """
    mock_release = MagicMock()
    mock_release.tag_name = 'Mocked tag'

    mock_get_repo.return_value.get_latest_release.return_value = mock_release

    args = Arguments(
        token='abc',
        slug='bad slug',
        latest=True,
        user='user',
        repo='repo')
    assert args.opts["slug"] == 'user/repo'

    mock_get_repo.return_value.get_latest_release.assert_called_once()


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_no_release_no_tag(mock_get_repo):
    """Test error when no release/no tag exists. """

    # this is to simulate no repo existing yet, i.e., need to create
    mock_get_repo.return_value.get_latest_release.side_effect = \
        github.GithubException('status', 'data')

    with pytest.raises(AttributeError):
        Arguments(
            token='abc',
            slug=TEST_SLUG,
            latest=True)


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_no_release(mock_get_repo):
    """Test create selected when no release exists. """

    # this is to simulate no repo existing yet, i.e., need to create
    mock_get_repo.return_value.get_release.side_effect = \
        github.GithubException('status', 'data')

    args = Arguments(
        token='abc',
        slug=TEST_SLUG,
        tag=TEST_TAG)
    assert args.opts["internal_cmd"] == Arguments.INTERNAL_CMD_CREATE


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_create_execute(mock_get_repo):
    """Test create selected when no release exists. """
    mock_release = MagicMock()
    mock_release.tag_name = 'Mocked tag'

    mock_get_repo.return_value.create_git_release.return_value = mock_release

    # this is to simulate no repo existing yet, i.e., need to create
    mock_get_repo.return_value.get_release.side_effect = \
        github.GithubException('status', 'data')

    args = Arguments(
        token='abc',
        slug=TEST_SLUG,
        tag=TEST_TAG,
        commitish=TEST_COMMITISH)
    rel_man = ReleaseMgr(args)
    rel_man.execute()

    mock_get_repo.return_value.create_git_release.assert_called_once()


@patch.object(satsuki.github.Github, 'get_repo', autospec=True)
def test_find_and_delete(mock_get_repo):
    """Test find and delete release."""
    mock_release = MagicMock()
    mock_release.delete_release.return_value = True

    mock_get_repo.return_value.get_release.return_value = mock_release

    args = Arguments(
        token='abc',
        slug=TEST_SLUG,
        tag=TEST_TAG,
        commitish=TEST_COMMITISH,
        command=Arguments.CMD_DELETE)
    rel_man = ReleaseMgr(args)
    rel_man.execute()

    mock_release.delete_release.assert_called_once()


def test_blank_arguments():
    """Test authorization by getting blank arguments. """
    with pytest.raises(PermissionError):
        Arguments()
