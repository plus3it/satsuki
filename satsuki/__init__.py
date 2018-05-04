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

import sys
import os
import github
import satsuki
import platform
import shutil
import subprocess
import json
import uuid
import glob
from string import Template

import sys # won't need if no system.exit

__version__ = "0.1.0"
VERB_MESSAGE_PREFIX = "[Satsuki]"

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
        clean: A bool indicating whether to clean temporary work from
            the build when complete.
        pkg_dir: A str with location of setup.py for the package to
            be built into a standalone application.
        src_dir: A str with relative path of directory with the
            package source code (e.g., src)
        name_format: A str that represents the format to be used in
            naming the standalone application.
        extra_data: A list of str providing any extra data that
            should be included with the standalone application.
        work_dir: A str with a relative path of directory to be used
            by Satsuki for work files.
        console_script: A str of the name of the first console script
            listed in setup.py or setup.cfg.
        app_version: A str of the version of the standalone
            application pulled from setup.py or setup.cfg.
        app_name: A str with name of the application (which is not
            the same as the file name) to be built.
        pkg_name: A str of the name of the package containing the
            application that will be built.
        script_path: A str of the path the script installed by pip
            when the application is installed.
        created_file: A str with name of file of the standalone
            application created.
        created_path: A str with absolute path and name of file of
            the standalone application created.
    """

    # class
    COMMAND_UPSERT = "upsert"
    COMMAND_DELETE = "delete"

    _COMMAND_INSERT = "i_insert"
    _COMMAND_UPDATE = "i_update"
    _COMMAND_DELETE_FILE = "i_delete_file"
    _COMMAND_DELETE_REL = "i_delete_rel"

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
            satsuki.error("Slug / User & Repo required.", RuntimeError)
        elif self.slug is None:
            self.slug = self.user + '/' + self.repo

    def _get_release(self):
        satsuki.verboseprint("Getting release")

        self.gh = github.Github(self.api_token, per_page=Arguments.PER_PAGE)

        try:
            self.repo = self.gh.get_repo(self.slug, lazy=False)
        except github.GithubException:
            satsuki.error("Repository not found.", ReferenceError)  

        try:
            if self.args.latest:
                self.working_release = self.repo.get_latest_release()
            else:
                self.working_release = self.repo.get_release(self.args.tag)
            
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
                    RuntimeError
                )

        if isinstance(self.tag, str):
            self.latest = False

    def _init_command(self):

        # user command
        if self.kwargs.get('command',False):
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
                satsuki.error(
                    "No release found to delete",
                    RuntimeError
                )
            else:
                self.internal_command = Arguments._COMMAND_INSERT   

    def _init_files(self):

        self.files = self.kwargs.get('file', [])
        self.labels = self.kwargs.get('label', [])
        self.mimes = self.kwargs.get('mime', [])
        self.file_file = self.kwargs.get('file_file','gravitybee.file')

        if len(self.files) == 0 \
            and os.path.isfile(self.file_file):
            file_file = open(self.file_file, "r")
            self.file_info = json.loads(file_file.read())
            file_file.close()

            with open(self.file_file) as f:
                content = f.readlines()
                self.files = [x.strip() for x in content] 

        if len(self.files) != len(self.labels) \
            and len(self.labels) not in [0, 1]:
            satsuki.error(
                "Invalid number of labels: " + len(self.labels),
                RuntimeError
            )

        if len(self.files) != len(self.mimes) \
            and len(self.mimes) not in [0, 1]:
            satsuki.error(
                "Invalid number of MIME types: " + len(self.mimes),
                RuntimeError
            )

        # if there are files, we'll set up a list of dicts with info
        # about each. if there's one label, it will be applied to all
        # files. same for mimes.
        self.file_info = []
        if len(self.files) > 0:
            for i, filename in enumerate(self.files):
                for one_file in glob.glob(filename):
                    info = {}
                    info['file'] = one_file
                    if len(self.labels) > 0:
                        if len(self.labels) == 1:
                            info['label'] = self.labels[0]
                        else:
                            info['label'] = self.labels[i]
                    else:
                        info['label'] = None

                    if len(self.mimes) > 0:
                        if len(self.mimes) == 1:
                            info['mime'] = self.mimes[0]
                        else:
                            info['mime'] = self.mimes[i]
                    else:
                        info['mime'] = None

                    self.file_info.append(info)

    def _init_data(self):
        # idea here is to not change anything not provided
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

        # verbosity
        satsuki.verboseprint("Arguments:")
        satsuki.verboseprint("user command:",self.user_command)
        satsuki.verboseprint("internal command:",self.internal_command)
        satsuki.verboseprint("slug:",self.slug)
        satsuki.verboseprint("rel_name:",self.rel_name)
        satsuki.verboseprint("latest:",self.latest)
        satsuki.verboseprint("body:",self.body)
        satsuki.verboseprint("pre:",self.pre)
        satsuki.verboseprint("draft:",self.draft)
        satsuki.verboseprint("tag:",self.tag)
        satsuki.verboseprint("target_commitish:",self.target_commitish)        

        satsuki.verboseprint("# files:", len(self.files))
        satsuki.verboseprint("# labels:", len(self.labels))
        satsuki.verboseprint("# mimes:", len(self.mimes))

        if self.file_info is not None:
            for info in self.file_info:
                satsuki.verboseprint(
                    "file:", 
                    info['file'], 
                    "label:", 
                    info['label'],
                    "mime:",
                    info['mime']
                )

        assert isinstance(self.internal_command, str), \
            "No internal command, user: " + self.user_command

class ReleaseMgr(object):
    """
    Utility for managing GitHub releases.

    Attributes:
        args: An instance of satsuki.Arguments containing
            the configuration information for Satsuki.
        operating_system: A str of the os. This is automatically
            determined.
        machine_type: A str of the machine (e.g., x86_64)
        standalone_name: A str that will be the name of the
            standalone application.
        gb_dir: A str of the Satsuki runtime package directory.
        gb_filename: A str of the runtime filename.
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
        self.working_release = self.repo.create_git_release(
            self.args.tag,
            self.args.rel_name,
            self.args.body,
            draft=self.args.draft,
            prerelease=self.args.pre,
            target_commitish=self.args.target_commitish
        )  

    def _update_release(self):
        satsuki.verboseprint("Updating release, id:",self.working_release.id)
        #PyGithub makes everything required so fudge updating
        if self.args.body is None:
            self.args.

        """ 
        name, message, draft=False, prerelease=False
        """
        self.working_release.update_release(
            self.args.rel_name,
            self.args.body,
            draft=self.args.draft,
            prerelease=self.args.pre
        )          

        # in order to upsert...
        # 1. is it update or create?
        #   - figure this out by looking for the release by tag
        #   - Must handle:
        #     - No tag / no release     ==> Create Tag      Create Release                          Upload Files
        #     - Yes tag / no release    ==>                 Create Release                          Upload Files
        #     - Yes tag / yes release   ==>                                     Update Release      Upload Files
        # 2. Create Tag
        #   - need to create the tag (requiring commit sha******)
        #     http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository.create_git_tag
        # 3. Create Release
        #   - need to create the release (requiring tag)
        #     http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository.create_git_release
        # 4. Update Release
        #   - release methods not documented so...
        #     https://github.com/PyGithub/PyGithub/blob/566b28d3fa0db4a89de830dc25fbbbfe6a56865f/github/GitRelease.py#L167
        # 5. Upload File(s) if any
        #   - release.upload_asset()
        #     https://github.com/PyGithub/PyGithub/blob/a519e4675a911a3f20f1ad197cbbbb14bdd1842d/github/GitRelease.py#L186
        #   - update release asset (only name & label, not the file itself)
        #     http://pygithub.readthedocs.io/en/latest/github_objects/GitReleaseAsset.html#github.GitReleaseAsset.GitReleaseAsset.update_asset

    def _delete(self):
        satsuki.verboseprint("Deleting release:",self.args.tag)
        # 1. Is it delete release or delete asset?
        #   - If file(s) included, always a delete asset, even if they don't exist
        #   - Must handle:
        #     - No file info / Release info (good)            ==> Delete release          No error
        #     - File info (bad) / Release info (good)         ==> Nothing (message)       No error (For replace functionality)
        #     - File info (good) / Release info (good)        ==> Delete file             No error
        #     - Release info (bad)                            ==> Nothing                 ERROR
        # 2. Delete release asset
        # http://pygithub.readthedocs.io/en/latest/github_objects/GitReleaseAsset.html#github.GitReleaseAsset.GitReleaseAsset.delete_asset
        # 3. Delete release
         # https://github.com/PyGithub/PyGithub/blob/a519e4675a911a3f20f1ad197cbbbb14bdd1842d/github/GitRelease.py#L160

    def execute(self):
        # Exist Upsert ==> update
        # Exist Delete ==> delete
        # Not   Upsert ==> create
        # Not   Delete ==> error
        existing_release = self._get_release()


        elif self.args.command == Arguments.COMMAND_DELETE:
            self._delete()
        elif self.args.command == Arguments.COMMAND_UPSERT:
            if self.working_release is None:
                self._create_release()
            else:
                self._update_release()

