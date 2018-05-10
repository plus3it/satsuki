# -*- coding: utf-8 -*-
"""satsuki module.

Satsuki is a Python package that helps manage GitHub releases and
release assets. Satsuki is especially useful paired with Continuous
Integration/ Continuous Deployment (CI/CD) tools such as Travis CI and
AppVeyor.

This module can be used by python scripts or through the included command-
line interface (CLI).

Example:
    Help using the satsuki CLI can be found by typing the following::

        $ satsuki --help
"""

import os
import github
import satsuki
import json
import glob
import subprocess
import fnmatch
import hashlib

__version__ = "0.1.5"
VERB_MESSAGE_PREFIX = "[Satsuki]"
EXIT_OK = 0
MAX_UPLOAD_ATTEMPTS = 3

verbose = False
pyppy = None
verboseprint = lambda *a, **k: \
    print(satsuki.VERB_MESSAGE_PREFIX, *a, **k) \
    if satsuki.verbose else lambda *a, **k: None

def error(message, exception):
    print(satsuki.VERB_MESSAGE_PREFIX, "[ERROR]", message)
    raise exception

class Arguments(object):
    """
    A class representing the configuration information needed by the
    satsuki.ReleaseMgr class.

    Attributes:
        api_token: A str with api token for GitHub.
        slug: A str with user and repo.
        repo: A str of target repo.
        user: A str of owner of target repo.
        gh: A github.github object that represents GitHub level.
        kwargs: A dict of keyword/value pairs as provided through
            CLI or init.
        latest: A bool of whether to use latest release instead
            of looking for one by name.
        working_release: A github.GitRelease of the target
            release.
        tag: A str with tag representing the release. Usually
            identifies the release.
        include_tag: A bool of whether or not to include tag
            when deleting a release.
        user_command: A str of command input by user. Must be
            upsert / delete.
        internal_command: A str of the command that will actually
            control what happens (create / update / delete).
        files: A list of str of files passed in to be uploaded
            or deleted relative to the release.
        labels: A list of str of labels associated with the
            files to be uploaded.
        mimes: A list of str of mimes associated with the
            files to be uploaded.
        file_file: A str with a file to be read to provide
            information on files. File must be in JSON.
        file_info: A list of dicts filename, path, label, and mime
            type for files.
        pre: A bool representing whether release is prerelease.
        draft: A bool representing whether release is a draft.
        body: A str with message associated with the release.
        rel_name: A str with the title of the release.
        target_commitish: A str with the SHA of the commit or a
            branch to associate the tag/release with.
    """

    # class
    COMMAND_UPSERT = "upsert"
    COMMAND_DELETE = "delete"

    _COMMAND_INSERT = "i_insert"
    _COMMAND_UPDATE = "i_update"
    _COMMAND_DELETE_FILE = "i_delete_file"
    _COMMAND_DELETE_REL = "i_delete_rel"
    _COMMAND_DELETE_TAG = "i_delete_tag"

    PER_PAGE = 10

    def _init_basic(self):
        # auth - required
        self.api_token = self.kwargs.get('token',None)
        if self.api_token is None:
            satsuki.error(
                "No GitHub API token was provided using SATS_TOKEN "
                + "environment variable.",
                PermissionError
            )

        # slug or repo / user - required
        self.slug = self.kwargs.get(
            'slug',
            os.environ.get(
                'TRAVIS_REPO_SLUG',
                os.environ.get(
                    'APPVEYOR_REPO_NAME',
                    None
                )
            )
        )

        if isinstance(self.slug, str) and '/' not in self.slug:
            satsuki.verboseprint("Invalid repo slug:",self.slug)
            self.slug = None
        self.repo = self.kwargs.get('repo', None)
        self.user = self.kwargs.get('user', None)

        # slug  repo    user    result
        # y     *       *       good
        # n     y       y       good
        if self.slug is None and (self.repo is None or self.user is None):
            satsuki.error("Slug / User & Repo required.", AttributeError)
        elif self.slug is None:
            self.slug = self.user + '/' + self.repo

    def _get_release(self):
        satsuki.verboseprint("Getting release")

        self._asset_list = None
        self.gh = github.Github(self.api_token, per_page=Arguments.PER_PAGE)

        try:
            self.repo = self.gh.get_repo(self.slug, lazy=False)
        except github.GithubException:
            satsuki.error("Repository not found.", ReferenceError)

        try:
            if self.latest:
                self.working_release = self.repo.get_latest_release()
            else:
                self.working_release = self.repo.get_release(self.tag)

            satsuki.verboseprint('Release ID: ', self.working_release.id)
            satsuki.verboseprint('Tag: ', self.working_release.tag_name)
            satsuki.verboseprint('Title: ', self.working_release.title)
            satsuki.verboseprint('URL: ', self.working_release.url)

            return True

        except github.GithubException:
            satsuki.verboseprint("No release found!")
            self.working_release = None

            return False

    def _init_tag(self):
        # find out if we can get a release (need tag or latest)
        self.latest = self.kwargs.get('latest',False)

        # tag - required (or latest)
        self.tag = self.kwargs.get('tag', None)
        if not isinstance(self.tag, str) and not self.latest:
            # check for Travis & AppVeyor values
            self.tag = os.environ.get(
                'TRAVIS_TAG',
                os.environ.get(
                    'APPVEYOR_REPO_TAG_NAME',
                    None
                )
            )
            if self.tag is None:
                satsuki.error(
                    "Either tag or the latest flag is required.",
                    AttributeError
                )

        if isinstance(self.tag, str):
            self.latest = False

        self.include_tag = self.kwargs.get('include_tag', False)

    def _init_command(self):

        # user command
        if not self.kwargs.get('command',False):
            self.user_command = Arguments.COMMAND_UPSERT
        elif self.kwargs.get('command') == Arguments.COMMAND_UPSERT or \
            self.kwargs.get('command') == Arguments.COMMAND_DELETE:
            self.user_command = self.kwargs.get('command')
        else:
            satsuki.error(
                "Invalid command:" + self.kwargs.get('command'),
                AttributeError
            )

        # internal command
        if self._get_release():
            # good to: delete, update
            if self.user_command == Arguments.COMMAND_UPSERT:
                self.internal_command = Arguments._COMMAND_UPDATE
            elif len(self.file_info) > 0 \
                and self.user_command == Arguments.COMMAND_DELETE:
                self.internal_command = Arguments._COMMAND_DELETE_FILE
            else:
                self.internal_command = Arguments._COMMAND_DELETE_REL
        else:
            if self.user_command == Arguments.COMMAND_DELETE:
                self.internal_command = Arguments._COMMAND_DELETE_TAG
            else:
                self.internal_command = Arguments._COMMAND_INSERT

    def _init_files(self):
        """
        This will handle multple files from the command lines args
        and/or a file_file.
        """

        self.files = self.kwargs.get('file', [])
        self.labels = self.kwargs.get('label', [])
        self.mimes = self.kwargs.get('mime', [])

        self.file_file = self.kwargs.get('file_file',None)

        if len(self.files) == 0 and self.file_file is None:
            self.file_file = 'gravitybee.file' # for integration with GravityBee

        # handle the file_file
        # todo: validate JSON
        if not self.file_file is None \
            and os.path.isfile(self.file_file):
            file_file = open(self.file_file, "r")
            self.file_info = json.loads(file_file.read())
            file_file.close()
        else:
            self.file_info = []

        # handle the command line files, et al.

        # if there are files, we'll set up a list of dicts with info
        # about each. if there's one label, it will be applied to all
        # files. same for mimes.
        if len(self.files) > 0:
            if len(self.files) != len(self.labels) \
                and len(self.labels) not in [0, 1]:
                satsuki.error(
                    "Invalid number of labels: " + len(self.labels),
                    AttributeError
                )

            if len(self.files) != len(self.mimes) \
                and len(self.mimes) not in [0, 1]:
                satsuki.error(
                    "Invalid number of MIME types: " + len(self.mimes),
                    AttributeError
                )

            for i, filename in enumerate(self.files):
                for one_file in glob.glob(filename):
                    info = {}
                    info['filename'] = os.path.basename(one_file)
                    info['path'] = one_file
                    if len(self.labels) > 0:
                        if len(self.labels) == 1:
                            info['label'] = self.labels[0]
                        else:
                            info['label'] = self.labels[i]
                    else:
                        info['label'] = None

                    if len(self.mimes) > 0:
                        if len(self.mimes) == 1:
                            info['mime-type'] = self.mimes[0]
                        else:
                            info['mime-type'] = self.mimes[i]
                    else:
                        info['mime-type'] = None

                    self.file_info.append(info)

    def _init_data(self):
        # idea here is to not change anything not provided by user

        # if latest, won't be given tag so this is way to get it
        self.tag = self.kwargs.get('tag', self.working_release.tag_name)

        # going to overwrite all values, fill in with old values if
        # no change
        self.pre = self.kwargs.get('pre', self.working_release.prerelease)
        self.draft = self.kwargs.get('draft', self.working_release.draft)
        self.body = self.kwargs.get('body', self.working_release.body)
        self.rel_name = self.kwargs.get('rel_name', self.working_release.title)
        self.target_commitish = None

    def _init_data_blank(self):
        # new insert so provide default values
        self.pre = self.kwargs.get('pre', False)
        self.draft = self.kwargs.get('draft', False)
        self.body = self.kwargs.get('body', "Release " + self.tag)
        self.rel_name = self.kwargs.get('rel_name', self.tag)

        self.target_commitish = self.kwargs.get(
            'commitish',
            os.environ.get(
                'TRAVIS_COMMIT',
                os.environ.get(
                    'APPVEYOR_REPO_COMMIT',
                    ""
                )
            )
        )

    def _verbosity(self):
        """
        Verbose printing. Should never cause errors for low priority
        verbosity.
        """

        try:
            # verbosity
            satsuki.verboseprint("Arguments:")
            satsuki.verboseprint("user command:",self.user_command)
            satsuki.verboseprint("internal command:",self.internal_command)
            satsuki.verboseprint("slug:",self.slug)
            satsuki.verboseprint("tag:",self.tag)

            if hasattr(self, 'latest'):
                satsuki.verboseprint("latest:",self.latest)
            if hasattr(self, 'target_commitish'):
                satsuki.verboseprint("target_commitish:",self.target_commitish)
            if hasattr(self, 'rel_name'):
                satsuki.verboseprint("rel_name:",self.rel_name)
            if hasattr(self, 'body'):
                satsuki.verboseprint("body:",self.body)
            if hasattr(self, 'pre'):
                satsuki.verboseprint("pre:",self.pre)
            if hasattr(self, 'draft'):
                satsuki.verboseprint("draft:",self.draft)

            satsuki.verboseprint("# files:", len(self.file_info))

            if self.file_info is not None:
                for info in self.file_info:
                    satsuki.verboseprint(
                        "file:",
                        info['filename'],
                        "label:",
                        info['label'],
                        "mime:",
                        info['mime-type']
                    )

        except Exception as err:
            satsuki.verboseprint("Verbosity problem:", err)
            pass


    def __init__(self, *args, **kwargs):
        """Instantiation"""

        # Remove unused options
        empty_keys = [k for k,v in kwargs.items() if not v]
        for k in empty_keys:
            del kwargs[k]

        self.kwargs = kwargs

        # package level
        satsuki.verbose = kwargs.get('verbose',False)

        # sub inits
        self._init_basic()
        self._init_files()
        self._init_tag()
        self._init_command()

        if self.internal_command == Arguments._COMMAND_INSERT:
            self._init_data_blank()
        elif self.internal_command == Arguments._COMMAND_UPDATE:
            self._init_data()

        self._verbosity()

        assert isinstance(self.internal_command, str), \
            "No internal command, user command: " + self.user_command

class ReleaseMgr(object):
    """
    Utility for managing GitHub releases.

    Attributes:
        args: An instance of satsuki.Arguments containing
            the configuration information for Satsuki.
    """

    def __init__(self, args=None):
        satsuki.verboseprint("ReleaseMgr:")
        self.args = args


    def _create_release(self):
        satsuki.verboseprint("Creating release:",self.args.rel_name)
        if isinstance(self.args.tag, int):
            # PyGithub will treat it as a release id when finding later
            satsuki.error(
                "Integer tag name given: " + self.args.tag,
                TypeError
            )
        if not isinstance(self.args.target_commitish, str):
            satsuki.error(
                "Commit SHA is required",
                AttributeError
            )

        """
        tag, name, message, draft=False, prerelease=False,
        target_commitish=github.GithubObject.NotSet
        """
        self.args.working_release = self.args.repo.create_git_release(
            self.args.tag,
            self.args.rel_name,
            self.args.body,
            draft=self.args.draft,
            prerelease=self.args.pre,
            target_commitish=self.args.target_commitish
        )    

    def _update_release(self):
        satsuki.verboseprint("Updating release, id:",self.args.working_release.id)
        """
        name, message, draft=False, prerelease=False
        """
        self.args.working_release.update_release(
            self.args.rel_name,
            self.args.body,
            draft=self.args.draft,
            prerelease=self.args.pre
        )

    def _get_hash(self, filename):
        sha256 = hashlib.sha256()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _find_release_asset(self, id):

        satsuki.verboseprint("Finding asset:", id)

        # get asset list is not done already
        if not isinstance(self.args._asset_list, list):
            self.args._asset_list = self.args.working_release.get_assets()

        if isinstance(id, str):

            # find by filename
            filename = id
            for check_asset in self.args._asset_list:
                if check_asset.name == filename:
                    satsuki.verboseprint("Found asset:", filename)
                    return check_asset

        elif isinstance(id, int):

            for check_asset in self.args._asset_list:
                if check_asset.id == id:
                    satsuki.verboseprint("Found asset:", id)
                    return check_asset

        else:

            return None


    def _delete_release_asset(self, filename):

        satsuki.verboseprint("Deleting release asset (if exists):", filename)
        delete_asset = self._find_release_asset(filename)

        if delete_asset is not None:
            delete_asset.delete_asset()

    def _upload_files(self):
        for info in self.args.file_info:
            
            # no way to update uploaded file, so delete->upload
            self._delete_release_asset(info['filename'])

            # path, label="", content_type=""
            satsuki.verboseprint("Upload file:",info['filename'])
            complete_filesize = os.path.getsize(info['path'])
            satsuki.verboseprint("File size on disk:", complete_filesize)
            filehash = self._get_hash(info['path'])
            satsuki.verboseprint("SHA256:", filehash)
            attempts = 0
            release_asset = None
            while attempts < satsuki.MAX_UPLOAD_ATTEMPTS:
                try:
                    attempts += 1

                    upload_args = {}
                    if info['label'] is None:
                        upload_args['label'] = info['filename']
                    else:
                        upload_args['label'] = info['label']
                    upload_args['label'] += "   (SHA256: " + filehash + ")"

                    if info['mime-type'] is not None:
                        upload_args['mime-type'] = info['mime-type']

                    release_asset = self.args.working_release.upload_asset(
                        info['path'],
                        **upload_args
                    )

                    if hasattr(release_asset, 'size'):
                        satsuki.verboseprint("Asset size:", release_asset.size)

                    # not sure if this will be accurate size, need to check
                    if not hasattr(release_asset, 'size') \
                        or release_asset.size != complete_filesize:
                        raise ConnectionError

                except IOError as err:
                    if str(err) == "[Errno 32] Broke pipe":
                        
                        # may not be an error - check API for file
                        asset = self._find_release_asset(release_asset.id)

                        if asset is not None \
                            and asset.size == release_asset.size:
                            satsuki.verboseprint(
                                "Upload okay, sizes:", 
                                release_asset.size, 
                                ",",
                                asset.size
                            )

                    else:
                        raise err

                except Exception as err:
                    if hasattr(release_asset, 'size'):
                        satsuki.verboseprint("Asset size:", release_asset.size)
                    satsuki.verboseprint("Exception type:",type(err))
                    satsuki.verboseprint(
                        "Upload FAILED, remaining attempts:",
                        satsuki.MAX_UPLOAD_ATTEMPTS - attempts,
                        "Error:",
                        err
                    )

                    if release_asset is not None:
                        if hasattr(release_asset, 'state'):
                            satsuki.verboseprint("State:",release_asset.state)

                        # release_asset.delete_asset() # throwing exception...

                    if attempts > satsuki.MAX_UPLOAD_ATTEMPTS:
                        raise err

    def _delete_file(self):
        satsuki.verboseprint("Deleting release asset:",self.args.tag)
        for info in self.args.file_info:
            asset = self._find_release_asset(info['filename'])
            if asset is not None:
                asset.delete_asset()

    def _delete_release(self):
        satsuki.verboseprint("Deleting release:",self.args.tag)

        # delete release
        self.args.working_release.delete_release()

    def _delete_tag(self):    

        if self.args.include_tag:
            satsuki.verboseprint("Cleaning tag(s):",self.args.tag)

            tag_list = self.args.repo.get_tags()
            for tag in tag_list:
                if fnmatch.fnmatch(tag.name, self.args.tag):
                    try:
                        self.args.repo.get_release(tag.name)
                        satsuki.verboseprint("Tag still connected to "
                            + "release - not deleting:", tag.name)
                    except Exception:
                        # No release exists, get rid of tag
                        # delete the local tag (if any)
                        satsuki.verboseprint("Deleting local tag:", tag.name)
                        try:
                            subprocess.run([
                                    'git',
                                    'tag',
                                    '--delete',
                                    tag.name
                                ],
                                check=True
                            )
                        except Exception as err:
                            satsuki.verboseprint("Trouble deleting local tag:",err)

                        # delete the remote tag (if any)
                        satsuki.verboseprint("Deleting remote tag:", tag.name)
                        try:
                            subprocess.run([
                                    'git',
                                    'push',
                                    '--delete',
                                    'origin',
                                    tag.name
                                ],
                                check=True
                            )
                        except Exception as err:
                            satsuki.verboseprint("Trouble deleting remote tag:",err)                  

    def execute(self):
        if self.args.internal_command == Arguments._COMMAND_DELETE_FILE:
            self._delete_file()
        elif self.args.internal_command == Arguments._COMMAND_DELETE_REL:
            self._delete_release()
            self._delete_tag()
        elif self.args.internal_command == Arguments._COMMAND_DELETE_TAG:
            self._delete_tag()
        elif self.args.internal_command == Arguments._COMMAND_INSERT:
            self._create_release()
            self._upload_files()
        elif self.args.internal_command == Arguments._COMMAND_UPDATE:
            self._update_release()
            self._upload_files()

