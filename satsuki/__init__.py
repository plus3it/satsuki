# -*- coding: utf-8 -*-
"""satsuki module.

Satsuki is a Python package that helps manage GitHub releases and
release assets. Satsuki is especially useful paired with Continuous
Integration/Continuous Deployment (CI/CD) tools such as Travis CI and
AppVeyor.

This module can be used by Python scripts or through the included command-
line interface (CLI).

Example:
    Help using the satsuki CLI can be found by typing the following::

        $ satsuki --help
"""

import fnmatch
import glob
import hashlib
import json
import logging
import logging.config
import os
import platform
import socket
import subprocess
import time

from string import Template

import github
import github.GithubException


__version__ = "0.1.30"
EXIT_OK = 0

logging.config.fileConfig(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logging.conf'))
logger = logging.getLogger(__name__)        # pylint: disable=invalid-name


def raise_error(message, exception):
    """Called to raise exceptions."""
    logger.error(message)
    raise exception


class Arguments():
    """
    A class representing the configuration information needed by the
    satsuki.ReleaseMgr class.

    Attributes:
        gb_subs: Substitutions that will be made based on GravityBee input.
        working_release: A github.GitRelease of the target release.
        working_tag: A github.GitTag of the target release.
        repo: A github.Repository handle for the repo.
        flags: A dict of bools for controlling behavior, including "force",
            "latest", "pre", "include_tag", "recreate", "draft".
        opts: A dict of strings with various options, including "api_token",
            "body", "file_sha", "files_file", "internal_cmd", "rel_name",
            "repo_name", "slug", "tag", target_commitish", "user",
            "user_cmd".
        lists: A dict of lists for "file_info", "files", "labels", "mimes"
            (mime types), "assets"
    """

    # class
    CMD_UPSERT = "upsert"
    CMD_DELETE = "delete"

    INTERNAL_CMD_CREATE = "i_create"
    INTERNAL_CMD_RECREATE = "i_recreate"
    INTERNAL_CMD_UPDATE = "i_update"
    INTERNAL_CMD_DELETE_FILE = "i_delete_file"
    INTERNAL_CMD_DELETE_REL = "i_delete_rel"
    INTERNAL_CMD_DELETE_TAG = "i_delete_tag"

    FILE_SHA_NONE = "none"
    FILE_SHA_SEP_FILE = "file"
    FILE_SHA_LABEL = "label"

    GB_FILES_FILE = os.path.join('.gravitybee', 'gravitybee-files.json')
    GB_INFO_FILE = os.path.join('.gravitybee', 'gravitybee-info.json')
    MAX_UPLOAD_ATTEMPTS = 3

    HASH_FILE = "$platform-sha256.json"

    PER_PAGE = 1000

    @classmethod
    def get_hash(cls, filename):
        """Produce SHA256 for the given file."""
        if os.path.exists(filename):
            sha256 = hashlib.sha256()
            with open(filename, "rb") as hash_file:
                for chunk in iter(lambda: hash_file.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()

        return None

    def __init__(self, **kwargs):
        """Starts the initialization process."""

        # Remove unused options
        empty_keys = [key for key, val in kwargs.items() if not val]
        for key in empty_keys:
            del kwargs[key]

        # preserving $vars means extra quotes
        for key, val in kwargs.items():
            if isinstance(val, str):
                kwargs[key] = val.strip().strip('"').strip("'")

        # seven attributes:
        self.gb_subs = None
        self.working_release = None
        self.working_tag = None
        self.repo = None
        self.flags = {}
        self.opts = {}
        self.lists = {}

        # helper inits
        self._init_basic(kwargs)
        self._init_gb_info()
        self._init_files(kwargs)
        self._init_files_file()
        self._init_gb_files_file()
        self._init_cmd_line_files()
        self._init_process_files()
        self._init_check_no_files()
        self._init_tag(kwargs)
        self._init_internal_command()

        if self.opts["internal_cmd"] == Arguments.INTERNAL_CMD_CREATE and \
                (not self.opts['tag'] or self.flags['latest']):
            raise_error(
                "Must include tag when creating release", AttributeError)

        if self.opts["internal_cmd"] == Arguments.INTERNAL_CMD_CREATE:
            self._init_data_blank(kwargs)
        elif self.opts["internal_cmd"] == Arguments.INTERNAL_CMD_UPDATE or \
                self.opts["internal_cmd"] == Arguments.INTERNAL_CMD_RECREATE:
            self._init_data(kwargs)

        self.summary()

        # this should never happen so an assertion is used
        assert isinstance(self.opts["internal_cmd"], str), \
            "No internal command, user command: " + self.opts["user_cmd"]

    def _init_basic(self, kwargs):
        """Initialize basic attributes (auth, user command, slug)."""

        # auth - required
        self.opts["api_token"] = kwargs.get('token', None)
        if self.opts["api_token"] is None:
            raise_error(
                "No GitHub API token was provided.",
                PermissionError)

        # user command
        if not kwargs.get('command', False):
            self.opts["user_cmd"] = Arguments.CMD_UPSERT
        elif kwargs.get('command') == Arguments.CMD_UPSERT or \
                kwargs.get('command') == Arguments.CMD_DELETE:
            self.opts["user_cmd"] = kwargs.get('command')
        else:
            raise_error(
                "Invalid command:" + kwargs.get('command'),
                AttributeError)

        self.flags["force"] = kwargs.get('force', False)

        # slug or repo / user - required
        self.opts["slug"] = kwargs.get(
            'slug',
            os.environ.get(
                'TRAVIS_REPO_SLUG',
                os.environ.get(
                    'APPVEYOR_REPO_NAME',
                    os.environ.get(
                        'BUILD_REPOSITORY_NAME', None))))

        if isinstance(self.opts["slug"], str) and '/' not in self.opts["slug"]:
            logger.warning("Invalid repo slug: %s", self.opts["slug"])
            self.opts["slug"] = None

        self.opts["repo_name"] = kwargs.get('repo', None)
        self.opts["user"] = kwargs.get('user', None)

        # slug  repo    user    result
        # y     *       *       good
        # n     y       y       good
        if self.opts["slug"] is None and (
                self.opts["repo_name"] is None or self.opts["user"] is None):
            raise_error("Slug / User & Repo required.", AttributeError)

        elif self.opts["slug"] is None:
            self.opts["slug"] = '/'.join(
                [self.opts["user"], self.opts["repo_name"]])

        self.flags["recreate"] = kwargs.get('recreate', False)

        self.opts["target_commitish"] = kwargs.get(
            'commitish',
            os.environ.get(
                'TRAVIS_COMMIT',
                os.environ.get(
                    'APPVEYOR_REPO_COMMIT',
                    os.environ.get(
                        'BUILD_SOURCEVERSION', None))))

        self.opts["gb_info_file"] = kwargs.get(
            'gb_info_file',
            os.environ.get(
                'GB_INFO_FILE', Arguments.GB_INFO_FILE))

    def _init_gb_info(self):
        """Gets GB (GravityBee) info, if any."""
        gb_info = None
        self.gb_subs = {}

        if os.path.exists(self.opts["gb_info_file"]):
            logger.info("Setting up variable substitution...")

            # open gravitybee info file and use app version
            info_file = open(self.opts["gb_info_file"], "r")
            gb_info = json.loads(info_file.read())
            info_file.close()

            if gb_info.get('app_version', None) is not None:
                self.gb_subs['gb_pkg_ver'] = gb_info['app_version']

            if gb_info.get('app_name', None) is not None:
                self.gb_subs['gb_pkg_name'] = gb_info['app_name']
                self.gb_subs['gb_pkg_name_lower'] = gb_info[
                    'app_name'].lower()

            if gb_info.get('gen_file', None) is not None:
                self.gb_subs['gb_sa_app'] = gb_info['gen_file']

            logger.info("Available substitutions: %s", self.gb_subs)

        else:
            logger.info("No variable substitution. No GravityBee file found.")

    def _init_tag(self, kwargs):
        """Initialize the tag from CLI, GH, GB, or CI."""
        # find out if we can get a release (need tag or latest)
        self.flags["latest"] = kwargs.get('latest', False)

        # tag - required (or latest)
        self.opts["tag"] = kwargs.get('tag', None)

        if self.opts["tag"]:
            self.opts["tag"] = Template(self.opts["tag"]).safe_substitute(
                self.gb_subs)

        if not isinstance(self.opts["tag"], str) and not self.flags["latest"]:
            # check for Travis & AppVeyor values
            self.opts["tag"] = os.environ.get(
                'TRAVIS_TAG',
                os.environ.get('APPVEYOR_REPO_TAG_NAME', None))
            if self.opts["tag"] is None:
                raise_error(
                    "Either tag or the latest flag is required.",
                    AttributeError)

        if isinstance(self.opts["tag"], str):
            self.flags["latest"] = False

        self.flags["include_tag"] = kwargs.get('include_tag', False)
        if self.flags["recreate"]:
            self.flags["include_tag"] = True

    def _init_internal_command(self):
        """Initialize internal command to one of 6 commands."""
        # internal command
        if self.get_release():
            # good to: delete, update
            if self.opts["user_cmd"] == Arguments.CMD_UPSERT:
                # now the question is, is there a commitish and
                # is it different than the existing one
                self.working_tag = self._find_tag()

                if self.working_tag is not None \
                        and hasattr(self.working_tag, 'commit') \
                        and self.opts["target_commitish"] is not None \
                        and self.working_tag.commit.sha \
                        != self.opts["target_commitish"] \
                        and self.flags["recreate"]:
                    logger.info(
                        "Same tag names: %s %s",
                        self.working_release.tag_name,
                        self.working_tag.name)
                    logger.info(
                        "Different commitishes: %s %s",
                        self.opts["target_commitish"],
                        self.working_tag.commit)

                    self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_RECREATE
                else:
                    self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_UPDATE

            elif self.lists["file_info"] \
                    and self.opts["user_cmd"] == Arguments.CMD_DELETE:
                self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_DELETE_FILE
            else:
                self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_DELETE_REL
        else:
            if self.opts["user_cmd"] == Arguments.CMD_DELETE:
                self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_DELETE_TAG
            else:
                self.opts["internal_cmd"] = Arguments.INTERNAL_CMD_CREATE

    def _init_files(self, kwargs):
        """
        This will handle multple files from the command lines args
        and/or a files_file.

        For clarity:
        self.lists["files"]: list of filenames (usually from command line)
        self.opts["file_sha"]: choice of how to handle sha hashes for files
        self.opts["files_file"]: a json file containing file info that is
            equivalent to command line
        self.lists["file_info"]: list of dicts of file info used for actual
            uploads
        new_files: list of str of filenames potentially glob expanded
            which is fed back into self.lists["file_info"]
        preprocessed_files: list of dicts of file after added sha
            hashes and filtering out non-existent files, which
            then replaces self.lists["file_info"]
        """
        self.lists["files"] = kwargs.get('file', [])
        self.lists["labels"] = kwargs.get('label', [])
        self.lists["mimes"] = kwargs.get('mime', [])
        self.opts["file_sha"] = kwargs.get('file_sha', Arguments.FILE_SHA_NONE)
        self.opts["files_file"] = kwargs.get('files_file', None)
        self.lists["file_info"] = []

    def _init_files_file(self):
        """Handle the files_file."""
        if self.opts["files_file"] \
                and os.path.isfile(self.opts["files_file"]):
            files_file = open(self.opts["files_file"], "r")
            self.lists["file_info"] += json.loads(files_file.read())
            files_file.close()

    def _init_gb_files_file(self):
        """Handle the GravityBee files_file."""
        if os.path.exists(Arguments.GB_FILES_FILE) \
                and self.opts["user_cmd"] == Arguments.CMD_UPSERT:
            files_file = open(Arguments.GB_FILES_FILE, "r")
            self.lists["file_info"] += json.loads(files_file.read())
            files_file.close()

    def _init_cmd_line_files(self):
        """Handle the command line files, et al."""

        # if there's one label, it will be applied to all. same for mimes.
        if self.lists["files"]:
            logger.info("Processing command-line files: %d", len(
                self.lists["files"]))

            if len(self.lists["files"]) != len(self.lists["labels"]) \
                    and len(self.lists["labels"]) not in [0, 1]:
                raise_error(
                    "Invalid number of labels: " + len(self.lists["labels"]),
                    AttributeError
                )

            if len(self.lists["files"]) != len(self.lists["mimes"]) \
                    and len(self.lists["mimes"]) not in [0, 1]:
                raise_error("Invalid number of MIME types: " + len(
                    self.lists["mimes"]), AttributeError)

            if self.opts["user_cmd"] == Arguments.CMD_UPSERT:
                self._init_upsert()
            elif self.opts["user_cmd"] == Arguments.CMD_DELETE:
                self._init_delete()

    def _init_upsert(self):

        new_files = []    # potentially glob expanded

        # glob expand
        for i, filename in enumerate(self.lists["files"]):
            logger.info("Processing: %s", filename)
            for one_file in glob.glob(filename):
                logger.info("Glob result: %s", one_file)
                new_files.append(one_file)

        # setup data structure for each file
        for i, filename in enumerate(new_files):
            info = {}
            info['filename'] = os.path.basename(filename)
            info['path'] = filename
            if self.lists["labels"]:

                if len(self.lists["labels"]) == 1:
                    info['label'] = Template(
                        self.lists["labels"][0]).safe_substitute(self.gb_subs)
                else:
                    info['label'] = Template(
                        self.lists["labels"][i]).safe_substitute(self.gb_subs)

            else:

                info['label'] = info['filename']

            if self.lists["mimes"]:
                if len(self.lists["mimes"]) == 1:
                    info['mime-type'] = self.lists["mimes"][0]
                else:
                    info['mime-type'] = self.lists["mimes"][i]
            else:
                info['mime-type'] = None

            self.lists["file_info"].append(info)

    def _init_delete(self):

        # files to be deleted may not exist locally
        for _, filename in enumerate(self.lists["files"]):
            info = {}
            info['filename'] = os.path.basename(filename)
            info['path'] = filename
            info['label'] = None
            info['mime-type'] = None
            info['sha256'] = None
            self.lists["file_info"].append(info)

    def _init_process_files(self):

        # processing for all files regardless of provenance
        if self.lists["file_info"] \
                and self.opts["user_cmd"] == Arguments.CMD_UPSERT:
            preprocessed_files = []    # will replace self.lists["file_info"]
            sha_dict = {}

            for info in self.lists["file_info"]:
                # take care of sha hash and existence of file
                if self.opts["file_sha"] is not Arguments.FILE_SHA_NONE:
                    info['sha256'] = Arguments.get_hash(info['path'])

                if self.opts["file_sha"] == Arguments.FILE_SHA_LABEL:
                    info['label'] += " (SHA256: " + info['sha256'] + ")"

                elif self.opts["file_sha"] == Arguments.FILE_SHA_SEP_FILE:
                    sha_dict[info['filename']] = info['sha256']

                if os.path.isfile(info['path']):
                    preprocessed_files.append(info)
                else:
                    logger.info(
                        "Skipping file. %s does not exist", info['path'])

            if self.opts["file_sha"] == Arguments.FILE_SHA_SEP_FILE:
                sha_filename = Template(Arguments.HASH_FILE).safe_substitute({
                    'platform': platform.system().lower()})

                sha_file = open(sha_filename, 'w')
                sha_file.write(json.dumps(sha_dict))
                sha_file.close()

                # add the sha hash file to the list of uploads
                if self.lists["file_info"]:

                    info = {}
                    info['filename'] = sha_filename
                    info['path'] = sha_filename
                    info['sha256'] = Arguments.get_hash(sha_filename)
                    info['label'] = "SHA256 hash(es) for " \
                        + platform.system() \
                        + " file(s)\n(This file: " \
                        + info['sha256'] \
                        + ")"
                    info['mime-type'] = "application/json"

                    if platform.system().lower() == "windows":
                        preprocessed_files.insert(0, info)
                    else:
                        preprocessed_files.append(info)

            self.lists["file_info"] = preprocessed_files

    def _init_check_no_files(self):

        if self.lists["files"] and not self.lists["file_info"]:
            raise_error(
                "File flag used but no matching files were found",
                AttributeError
            )

    def _init_data(self, kwargs):
        """
        This is only called when a release will be updated. The idea
        is to *not* change data if not provided by the user. Since
        PyGithub requires body and rel name, for example, if you don't
        initialize these to the existing values and the user doesn't
        provide values, the existing body or rel name will be blanked
        out.

        Handles initializing data attributes, which are:
        tag, prerelease (pre), draft, body, rel_name.
        """
        # if latest, won't be given tag so this is way to get it
        if self.flags["latest"]:
            self.opts["tag"] = kwargs.get('tag', self.working_release.tag_name)

        # going to overwrite all values, fill in with old values if
        # no change
        self.flags["pre"] = kwargs.get('pre', self.working_release.prerelease)
        self.flags["draft"] = kwargs.get('draft', self.working_release.draft)

        # use templates for body and rel_name if necessary
        self.opts["body"] = kwargs.get('body', None)

        if self.opts["body"] is None:
            # use existing value if none given
            self.opts["body"] = self.working_release.body
        else:
            # possible template expansion
            self.opts["body"] = Template(
                self.opts["body"]).safe_substitute(self.gb_subs)

        self.opts["rel_name"] = kwargs.get('rel_name', None)

        if self.opts["rel_name"] is None:
            # use existing value if none given
            self.opts["rel_name"] = self.working_release.title
        else:
            # possible template expansion
            self.opts["rel_name"] = Template(
                self.opts["rel_name"]).safe_substitute(
                    self.gb_subs)

    def _init_data_blank(self, kwargs):
        """Initialize data when release is created."""
        # new insert so provide default values
        self.flags["pre"] = kwargs.get('pre', False)
        self.flags["draft"] = kwargs.get('draft', False)

        # use templates for body and rel_name if necessary
        self.opts["body"] = kwargs.get('body', None)

        if self.opts["body"] is None:
            # use existing value if none given
            self.opts["body"] = "Release " + self.opts["tag"]
        else:
            # possible template expansion
            self.opts["body"] = Template(
                self.opts["body"]).safe_substitute(self.gb_subs)

        self.opts["rel_name"] = kwargs.get('rel_name', None)

        if self.opts["rel_name"] is None:
            # use existing value if none given
            self.opts["rel_name"] = self.opts["tag"]
        else:
            # possible template expansion
            self.opts["rel_name"] = Template(
                self.opts["rel_name"]).safe_substitute(self.gb_subs)

    def _find_tag(self):
        """Find release by tag name (can't find tag by tag name)."""
        logger.info("Finding tag: %s", self.working_release.tag_name)

        # get tag list is not done already
        logger.info("Getting tag list")

        # find by filename
        for check_tag in self.repo.get_tags():
            if check_tag.name == self.working_release.tag_name:
                logger.info("Found tag: %s", check_tag.name)
                return check_tag
        return None

    def get_release(self):
        """Initialize repo and release (find through API)."""
        logger.info("Getting release")

        self.lists["assets"] = None
        github_conn = github.Github(
            self.opts["api_token"], per_page=Arguments.PER_PAGE)

        try:
            self.repo = github_conn.get_repo(self.opts["slug"], lazy=False)
        except github.GithubException:
            raise_error("Repository not found.", ReferenceError)

        try:
            if self.flags["latest"]:
                self.working_release = self.repo.get_latest_release()
            else:
                self.working_release = self.repo.get_release(self.opts["tag"])
            logger.info('Release ID: %s', self.working_release.id)
            logger.info('Tag: %s', self.working_release.tag_name)
            logger.info('Title: %s', self.working_release.title)
            logger.info('URL: %s', self.working_release.url)
            return True
        except github.GithubException:
            logger.info("No release found!")
            self.working_release = None
            return False

    def summary(self):
        """Log a summary of the arguments."""

        logger.info("Arguments:")
        logger.info("user command: %s", self.opts["user_cmd"])
        logger.info("internal command: %s", self.opts["internal_cmd"])
        logger.info("slug: %s", self.opts["slug"])
        logger.info("tag: %s", self.opts["tag"])

        if hasattr(self.flags, 'latest'):
            logger.info("latest: %s", self.flags["latest"])
        if hasattr(self.opts, 'target_commitish'):
            logger.info("target_commitish: %s", self.opts["target_commitish"])
        if hasattr(self.opts, 'rel_name'):
            logger.info("rel_name: %s", self.opts["rel_name"])
        if hasattr(self.opts, 'body'):
            logger.info("body: %s", self.opts["body"])
        if hasattr(self.flags, 'pre'):
            logger.info("pre: %s", self.flags["pre"])
        if hasattr(self.flags, 'draft'):
            logger.info("draft: %s", self.flags["draft"])

        logger.info("# files: %d", len(self.lists["file_info"]))
        logger.info("SHA256 for files: %s", self.opts["file_sha"])

        if self.lists["file_info"] is not None:
            for info in self.lists["file_info"]:
                logger.info(
                    "file: %s; label: %s; mime-type: %s",
                    info['filename'],
                    info['label'],
                    info['mime-type']
                )
                if info.get("sha256", None) is not None:
                    logger.info("sha256: %s", info['sha256'])


class ReleaseMgr():
    """
    Utility class for managing GitHub releases.

    Attributes:
        args: An instance of satsuki.Arguments containing
            the configuration information for Satsuki.
        release_asset: A release asset, such as a binary file.
    """

    def __init__(self, args=None):
        """Initialize the instance."""
        logger.info("ReleaseMgr:")
        if isinstance(args, Arguments):
            self.args = args
        else:
            raise_error(
                "Initialization requires an instance of satsuki.Arguments.",
                AttributeError
            )

        self.release_asset = None

    def summary(self):
        """Log summary of the arguments."""
        self.args.summary()

    def _create_release(self):
        """Create a new release."""
        logger.info("Creating release: %s", self.args.opts["rel_name"])
        if isinstance(self.args.opts["tag"], int):
            # PyGithub will treat it as a release id when finding later
            raise_error(
                "Integer tag name given: " + self.args.opts["tag"],
                TypeError
            )
        if not isinstance(self.args.opts["target_commitish"], str):
            raise_error(
                "Commit SHA is required",
                AttributeError
            )

        # Call to PyGithub:
        # https://github.com/PyGithub/PyGithub/blob/master/github/Repository.py
        self.args.working_release = self.args.repo.create_git_release(
            self.args.opts["tag"],
            self.args.opts["rel_name"],
            self.args.opts["body"],
            draft=self.args.flags["draft"],
            prerelease=self.args.flags["pre"],
            target_commitish=self.args.opts["target_commitish"]
        )

    def _update_release(self):
        """Update an existing release."""

        logger.info("Updating release, id: %s", self.args.working_release.id)

        # Call to PyGithub:
        # https://github.com/PyGithub/PyGithub/blob/master/github/GitRelease.py
        self.args.working_release.update_release(
            self.args.opts["rel_name"],
            self.args.opts["body"],
            draft=self.args.flags["draft"],
            prerelease=self.args.flags["pre"]
        )

    def _find_release_asset(self, asset_id):
        """
        Find a release asset associated with a release.

        Since no search functionality is available through PyGithub, this is a
        rudamentary search, going through list of assets one at
        a time, comparing filenames, until found.

        Args:
            asset_id: A str or int representing a tag or release ID of a
                release.

        Todo: May not work with long lists of assets, based on
        paginated lists.
        """
        logger.info("Finding asset: %s", asset_id)

        # get asset list
        logger.info("Getting asset list")
        self.args.lists["assets"] = self.args.working_release.get_assets()

        if isinstance(asset_id, str):

            # find by filename
            filename = asset_id
            for check_asset in self.args.lists["assets"]:
                if check_asset.name == filename:
                    logger.info("Found asset: %s", filename)
                    self.release_asset = check_asset
                    return True

        elif isinstance(asset_id, int):

            for check_asset in self.args.lists["assets"]:
                if check_asset.asset_id == asset_id:
                    logger.info("Found asset: %s", asset_id)
                    self.release_asset = check_asset
                    return True

        return False

    def _delete_release_asset(self, filename):
        """
        There is no way to update a release asset's payload (i.e., the
        file). You can update the name and label but to update the file
        you must delete and re-upload. This method allows deleting
        the release asset.
        https://github.com/PyGithub/PyGithub/blob/e9e09b9dda6020b583d17cd727d851c1a79e7150/github/GitReleaseAsset.py#L162

        """
        logger.info("Deleting release asset (if exists): %s", filename)

        if self._find_release_asset(filename):
            logger.info("File exists, deleting...")
            self.release_asset.delete_asset()

    def _handle_upload_error(self, upload_error, file_info, complete_filesize):
        logger.warning("Upload error!")
        logger.warning("Error (%s): %s", type(upload_error), upload_error)

        if isinstance(upload_error, (
                github.GithubException, BrokenPipeError,
                socket.timeout, ConnectionAbortedError)):
            # possible non errors
            logger.info("This may be an inconsequential error...")

            if self._find_release_asset(file_info['filename']) \
                    and hasattr(self.release_asset, 'size') \
                    and self.release_asset.size == complete_filesize:
                logger.info("File uploaded correctly")
                return True

        return False

    def _upload_file(self, file_info):
        """Upload an individual file to the release."""
        # no way to update uploaded file, so delete->upload
        self._delete_release_asset(file_info['filename'])

        # path, label="", content_type=""
        complete_filesize = os.path.getsize(file_info['path'])
        logger.info("Size of %s: %d", file_info['filename'], complete_filesize)
        attempts = 0
        success = False
        upload_error = ConnectionError

        while attempts < Arguments.MAX_UPLOAD_ATTEMPTS and not success:
            time.sleep(30 * attempts)
            attempts += 1
            upload_args = {}
            if file_info['label'] is None:
                upload_args['label'] = file_info['filename']
            else:
                upload_args['label'] = file_info['label']

            if file_info['mime-type'] is not None:
                upload_args['content_type'] = file_info['mime-type']

            self.release_asset = None
            upload_error = None

            logger.info("Uploading file: %s", file_info['filename'])
            logger.info(
                "Attempt: %s",
                str(attempts) + '/' + str(Arguments.MAX_UPLOAD_ATTEMPTS))

            try:
                self.release_asset = self.args.working_release.upload_asset(
                    file_info['path'], **upload_args)
            except (
                    BrokenPipeError, socket.timeout, github.GithubException,
                    ConnectionError, ConnectionAbortedError) as exc:
                upload_error = exc
            finally:
                # fix for PyGithub issue, renew the repo
                # might be able to remove when PR #771 is merged
                # https://github.com/PyGithub/PyGithub/pull/771
                self.args.get_release()

            if upload_error is None \
                    and hasattr(self.release_asset, 'size') \
                    and self.release_asset.size == complete_filesize:
                success = True
            elif self._handle_upload_error(
                    upload_error, file_info, complete_filesize):
                success = True

        # attempts are done...
        self._check_upload(success, upload_error)

    def _check_upload(self, success, upload_error):
        if success:
            logger.info("Successfully uploaded: %s", self.release_asset.name)
            logger.info("Size: %d", self.release_asset.size)
            logger.info("ID: %s", self.release_asset.id)
        else:
            if upload_error is not None:
                raise upload_error
            raise ConnectionError

    def _upload_files(self):
        """Upload files to a release."""
        files_to_upload = len(self.args.lists["file_info"])
        file_uploading = 0

        for file_info in self.args.lists["file_info"]:

            file_uploading += 1

            logger.info(
                "Uploading file %s...",
                str(file_uploading) + "/" + str(files_to_upload)
            )
            logger.info("Prepping upload of %s", file_info['filename'])

            self._upload_file(file_info)

    def _delete_file(self):
        """Delete a file (i.e., release asset) from a release."""

        logger.info("Deleting release asset: %s", self.args.opts["tag"])
        for info in self.args.lists["file_info"]:
            if self._find_release_asset(info['filename']):
                self.release_asset.delete_asset()

    def _delete_release(self):
        """Delete a release."""
        logger.info("Deleting release: %s", self.args.opts["tag"])

        # delete release
        self.args.working_release.delete_release()

    def _delete_tag(self):
        """Attempt to delete tags both from GitHub and git."""
        if self.args.opts["internal_cmd"] \
                == Arguments.INTERNAL_CMD_DELETE_TAG \
                or self.args.flags["include_tag"]:
            logger.info("Cleaning tag(s): %s", self.args.opts["tag"])

            for tag in self.args.repo.get_tags():
                if fnmatch.fnmatch(tag.name, self.args.opts["tag"]):
                    try:
                        release = self.args.repo.get_release(tag.name)
                        if self.args.flags["force"]:
                            logger.info("Deleting release: %s", release.title)
                            release.delete_release()
                            raise github.UnknownObjectException(
                                "404", "Spoof to hit except")

                        logger.info(
                            "Tag %s still connected to release: %s",
                            tag.name,
                            "not deleting")
                    except github.UnknownObjectException:
                        # No release exists, get rid of tag
                        # delete the local tag (if any)
                        logger.info("Deleting local tag: %s", tag.name)
                        try:
                            subprocess.run(
                                ['git', 'tag', '--delete', tag.name],
                                check=True)
                        except subprocess.CalledProcessError as err:
                            logger.info("Trouble deleting local tag: %s", err)

                        # delete the remote tag (if any)
                        logger.info("Deleting remote tag: %s", tag.name)
                        try:
                            subprocess.run(
                                ['git', 'push', '--delete', 'origin',
                                 tag.name], check=True)
                        except subprocess.CalledProcessError as err:
                            logger.info("Trouble deleting remote tag: %s", err)

    def execute(self):
        """Do what needs doing based on arguments configuration."""
        if self.args.opts["internal_cmd"] \
                == Arguments.INTERNAL_CMD_DELETE_FILE:
            self._delete_file()
        elif self.args.opts["internal_cmd"] \
                == Arguments.INTERNAL_CMD_DELETE_REL:
            self._delete_release()
            self._delete_tag()
        elif self.args.opts["internal_cmd"] \
                == Arguments.INTERNAL_CMD_DELETE_TAG:
            self._delete_tag()
        elif self.args.opts["internal_cmd"] == Arguments.INTERNAL_CMD_RECREATE:
            self._delete_release()
            self._delete_tag()
            self._create_release()
            self._upload_files()
        elif self.args.opts["internal_cmd"] == Arguments.INTERNAL_CMD_CREATE:
            self._create_release()
            self._upload_files()
        elif self.args.opts["internal_cmd"] == Arguments.INTERNAL_CMD_UPDATE:
            self._update_release()
            self._upload_files()
