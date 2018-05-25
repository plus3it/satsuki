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

import os
import github
import satsuki
import json
import glob
import subprocess
import fnmatch
import hashlib
import socket
import platform

from string import Template

__version__ = "0.1.9"
VERBOSE_MESSAGE_PREFIX = "[Satsuki]"
EXIT_OK = 0
MAX_UPLOAD_ATTEMPTS = 3
GB_INFO_FILE = "gravitybee-info.json"
HASH_FILE = "$platform-sha256.json"

verbose = False
pyppy = None
verboseprint = lambda *a, **k: \
    print(satsuki.VERBOSE_MESSAGE_PREFIX, *a, **k) \
    if satsuki.verbose else lambda *a, **k: None

def _error(message, exception):
    """
    Called to raise exceptions.
    """
    print(satsuki.VERBOSE_MESSAGE_PREFIX, "[ERROR]", message)
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
        files_file: A str with a file to be read to provide
            information on files. File must be in JSON.
        file_info: A list of dicts filename, path, label, and mime
            type for files.
        file_sha: A str with option of how to handle SHA256
            hashes (none, file, label).
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

    _COMMAND_CREATE = "i_create"
    _COMMAND_RECREATE = "i_recreate"
    _COMMAND_UPDATE = "i_update"
    _COMMAND_DELETE_FILE = "i_delete_file"
    _COMMAND_DELETE_REL = "i_delete_rel"
    _COMMAND_DELETE_TAG = "i_delete_tag"

    FILE_SHA_NONE = "none"
    FILE_SHA_SEP_FILE = "file"
    FILE_SHA_LABEL = "label"

    GB_FILES_FILE = 'gravitybee-files.json'

    PER_PAGE = 1000

    @classmethod
    def get_hash(cls, filename):
        """
        Finds a SHA256 for the given file.

        Args:
            filename: A str representing a file.
        """

        if os.path.exists(filename):
            sha256 = hashlib.sha256()
            with open(filename, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        else:
            return None


    def _init_basic(self):
        """
        Handles initializing basic attributes, which are:
        auth, user command, slug (owner/repo)
        """

        # auth - required
        self.api_token = self.kwargs.get('token',None)
        if self.api_token is None:
            satsuki._error(
                "No GitHub API token was provided.",
                PermissionError
            )

        # user command
        if not self.kwargs.get('command',False):
            self.user_command = Arguments.COMMAND_UPSERT
        elif self.kwargs.get('command') == Arguments.COMMAND_UPSERT or \
            self.kwargs.get('command') == Arguments.COMMAND_DELETE:
            self.user_command = self.kwargs.get('command')
        else:
            satsuki._error(
                "Invalid command:" + self.kwargs.get('command'),
                AttributeError
            )

        self.force = self.kwargs.get('force',False)

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
            satsuki._error("Slug / User & Repo required.", AttributeError)

        elif self.slug is None:
            self.slug = self.user + '/' + self.repo

        self.recreate = self.kwargs.get('recreate', False)

        self.target_commitish = self.kwargs.get(
            'commitish',
            os.environ.get(
                'TRAVIS_COMMIT',
                os.environ.get(
                    'APPVEYOR_REPO_COMMIT',
                    None
                )
            )
        )            


    def _init_gb_info(self):
        """
        Gets gb_info, if any. The gb_info file is not required and
        one of many ways to get information to Satsuki.
        """

        self.gb_info = None
        self.gb_subs = {}

        if os.path.exists(satsuki.GB_INFO_FILE):
            satsuki.verboseprint("Setting up variable substitution...")

            # open gravitybee info file and use app version
            info_file = open(satsuki.GB_INFO_FILE, "r")
            self.gb_info = json.loads(info_file.read())
            info_file.close()

            if self.gb_info.get('app_version',None) is not None:
                self.gb_subs['gb_pkg_ver'] = self.gb_info['app_version']

            if self.gb_info.get('app_name',None) is not None:
                self.gb_subs['gb_pkg_name'] = self.gb_info['app_name']
                self.gb_subs['gb_pkg_name_lower'] = self.gb_info['app_name'].lower()

            if self.gb_info.get('created_file',None) is not None:
                self.gb_subs['gb_sa_app'] = self.gb_info['created_file']

            satsuki.verboseprint("Available substitutions: ", self.gb_subs)

        else:
            satsuki.verboseprint("No variable substitution. No GravityBee file found.")


    def _get_release(self):
        """
        Handles initializing the GitHub repo and release, which
        means actually finding them through API and saving pointers.
        """

        satsuki.verboseprint("Getting release")

        self._asset_list = None
        self.gh = github.Github(self.api_token, per_page=Arguments.PER_PAGE)

        try:
            self.repo = self.gh.get_repo(self.slug, lazy=False)
        except github.GithubException:
            satsuki._error("Repository not found.", ReferenceError)

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
        """
        Handles initializing the tag which can come from the
        command line, GitHub (latest), gravitybee, or Travis/AppVeyor.
        """

        # find out if we can get a release (need tag or latest)
        self.latest = self.kwargs.get('latest',False)

        # tag - required (or latest)
        self.tag = self.kwargs.get('tag', None)

        if isinstance(self.tag, str):
            self.tag = Template(self.tag).safe_substitute(self.gb_subs)

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
                satsuki._error(
                    "Either tag or the latest flag is required.",
                    AttributeError
                )

        if isinstance(self.tag, str):
            self.latest = False

        self.include_tag = self.kwargs.get('include_tag', False)
        if self.recreate:
            self.include_tag = True        


    def _find_tag(self):
        """
        Similiar to _find_release_asset(), there is no search function so
        this is a rudamentary 1-by-1 search.

        To clarify, you can get a release by a tag name but you
        can't get a tag (which has the commitish) by tag name. :(
        """
        satsuki.verboseprint("Finding tag:", self.working_release.tag_name)

        # get tag list is not done already
        satsuki.verboseprint("Getting tag list")
        self._tag_list = self.repo.get_tags()

        # find by filename
        for check_tag in self._tag_list:
            if check_tag.name == self.working_release.tag_name:
                satsuki.verboseprint("Found tag:", check_tag.name)
                return check_tag

        return None


    def _init_internal_command(self):
        """
        Handles initializing the internal command to one of 6 commands
        based on one of 2 commands provided by the user.
        """

        # internal command
        if self._get_release():

            # good to: delete, update
            if self.user_command == Arguments.COMMAND_UPSERT:
                
                # now the question is, is there a commitish and 
                # is it different than the existing one
                self._working_tag = self._find_tag()

                if self._working_tag is not None \
                    and hasattr(self._working_tag, 'commit') \
                    and self.target_commitish is not None \
                    and self._working_tag.commit.sha != self.target_commitish \
                    and self.recreate:
                    satsuki.verboseprint(
                        "Same tag names:", 
                        self.working_release.tag_name, 
                        self._working_tag.name)
                    satsuki.verboseprint(
                        "Different commitishes:", 
                        self.target_commitish, 
                        self._working_tag.commit)
                    
                    self.internal_command = Arguments._COMMAND_RECREATE
                else:
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
                self.internal_command = Arguments._COMMAND_CREATE


    def _init_files(self):
        """
        This will handle multple files from the command lines args
        and/or a files_file.

        For clarity:
        self.files: list of filenames (usually from command line)
        self.file_sha: choice of how to handle sha hashes for files
        self.files_file: a json file containing file info that is
            equivalent to command line
        self.file_info: list of dicts of file info used for actual
            uploads
        new_files: list of str of filenames potentially glob expanded
            which is fed back into self.file_info
        preprocessed_files: list of dicts of file after added sha
            hashes and filtering out non-existent files, which 
            then replaces self.file_info
        """

        self.files = self.kwargs.get('file', [])
        self.labels = self.kwargs.get('label', [])
        self.mimes = self.kwargs.get('mime', [])
        self.file_sha = self.kwargs.get('file_sha', Arguments.FILE_SHA_NONE)
        satsuki.verboseprint("****************self.file_sha:", self.file_sha)

        self.files_file = self.kwargs.get('files_file', None)

        self.file_info = []

        # handle the files_file
        if not self.files_file is None \
            and os.path.isfile(self.files_file):
            files_file = open(self.files_file, "r")
            self.file_info += json.loads(files_file.read())
            files_file.close()

        # handle the GravityBee files_file
        if os.path.exists(Arguments.GB_FILES_FILE) \
            and self.user_command == Arguments.COMMAND_UPSERT:
            # merge into file_info      
            files_file = open(Arguments.GB_FILES_FILE, "r")
            self.file_info += json.loads(files_file.read())
            files_file.close()       

        # handle the command line files, et al.

        # if there are files, we'll set up a list of dicts with info
        # about each. if there's one label, it will be applied to all
        # files. same for mimes.
        if len(self.files) > 0:

            satsuki.verboseprint("Processing command-line files:", len(self.files))

            if len(self.files) != len(self.labels) \
                and len(self.labels) not in [0, 1]:
                satsuki._error(
                    "Invalid number of labels: " + len(self.labels),
                    AttributeError
                )

            if len(self.files) != len(self.mimes) \
                and len(self.mimes) not in [0, 1]:
                satsuki._error(
                    "Invalid number of MIME types: " + len(self.mimes),
                    AttributeError
                )

            new_files = [] # potentially glob expanded
            if self.user_command == Arguments.COMMAND_UPSERT:

                # glob expand
                for i, filename in enumerate(self.files):
                    satsuki.verboseprint("Processing:", filename)
                    for one_file in glob.glob(filename):
                        satsuki.verboseprint("Glob result:", one_file)
                        new_files.append(one_file)

                # setup data structure for each file
                for i, filename in enumerate(new_files):
                    info = {}
                    info['filename'] = os.path.basename(filename)
                    info['path'] = filename
                    if len(self.labels) > 0:

                        if len(self.labels) == 1:
                            info['label'] = Template(self.labels[0]).safe_substitute(self.gb_subs)
                        else:
                            info['label'] = Template(self.labels[i]).safe_substitute(self.gb_subs)

                    else:

                        info['label'] = info['filename']

                    if len(self.mimes) > 0:
                        if len(self.mimes) == 1:
                            info['mime-type'] = self.mimes[0]
                        else:
                            info['mime-type'] = self.mimes[i]
                    else:
                        info['mime-type'] = None

                    self.file_info.append(info)

            elif self.user_command == Arguments.COMMAND_DELETE:

                # files to be deleted may not exist locally
                for i, filename in enumerate(self.files):
                    info = {}
                    info['filename'] = os.path.basename(filename)
                    info['path'] = filename
                    info['label'] = None
                    info['mime-type'] = None
                    info['sha256'] = None
                    self.file_info.append(info)

        # processing for all files regardless of provenance
        if len(self.file_info) > 0 \
            and self.user_command == Arguments.COMMAND_UPSERT:

            preprocessed_files = [] # will replace self.file_info

            sha_dict = {}

            for info in self.file_info:
                # take care of sha hash and existence of file

                if self.file_sha is not Arguments.FILE_SHA_NONE:
                    info['sha256'] = Arguments.get_hash(info['path'])

                if self.file_sha == Arguments.FILE_SHA_LABEL:
                    info['label'] += " (SHA256: " + info['sha256'] + ")"

                elif self.file_sha == Arguments.FILE_SHA_SEP_FILE:
                    sha_dict[info['filename']] = info['sha256']

                if os.path.isfile(info['path']):
                    preprocessed_files.append(info)
                else:
                    satsuki.verboseprint(
                        "Skipping file.",
                        filename,
                        "does not exist."
                    )

            if self.file_sha == Arguments.FILE_SHA_SEP_FILE:
                sha_filename = Template(satsuki.HASH_FILE).safe_substitute({
                    'platform':platform.system().lower()
                })

                sha_file = open(sha_filename,'w')
                sha_file.write(json.dumps(sha_dict))
                sha_file.close()

                # add the sha hash file to the list of uploads
                if len(self.file_info) > 0:

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

            self.file_info = preprocessed_files

        if len(self.files) > 0 and len(self.file_info) == 0:
            satsuki._error(
                "File flag used but no matching files were found",
                AttributeError
            )


    def _init_data(self):
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
        if self.latest:
            self.tag = self.kwargs.get('tag', self.working_release.tag_name)

        # going to overwrite all values, fill in with old values if
        # no change
        self.pre = self.kwargs.get('pre', self.working_release.prerelease)
        self.draft = self.kwargs.get('draft', self.working_release.draft)

        # use templates for body and rel_name if necessary
        self.body = self.kwargs.get('body', None)

        if self.body == None:
            # use existing value if none given
            self.body = self.working_release.body
        else:
            # possible template expansion
            self.body = Template(self.body).safe_substitute(self.gb_subs)

        self.rel_name = self.kwargs.get('rel_name', None)

        if self.rel_name == None:
            # use existing value if none given
            self.rel_name = self.working_release.title
        else:
            # possible template expansion
            self.rel_name = Template(self.rel_name).safe_substitute(self.gb_subs)


    def _init_data_blank(self):
        """
        This is only called when a release is created.

        Handles initializing data attributes, which are:
        tag, prerelease (pre), draft, body, rel_name.
        """
        # new insert so provide default values
        self.pre = self.kwargs.get('pre', False)
        self.draft = self.kwargs.get('draft', False)

        # use templates for body and rel_name if necessary
        self.body = self.kwargs.get('body', None)

        if self.body == None:
            # use existing value if none given
            self.body = "Release " + self.tag
        else:
            # possible template expansion
            self.body = Template(self.body).safe_substitute(self.gb_subs)

        self.rel_name = self.kwargs.get('rel_name', None)

        if self.rel_name == None:
            # use existing value if none given
            self.rel_name = self.tag
        else:
            # possible template expansion
            self.rel_name = Template(self.rel_name).safe_substitute(self.gb_subs)


    def _init_summary(self):
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
            satsuki.verboseprint("SHA256 for files: ", self.file_sha)

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
                    if info.get("sha256", None) is not None:
                        satsuki.verboseprint(
                            "sha256:",
                            info['sha256']
                        )

        except Exception as err:
            satsuki.verboseprint("Verbosity problem:", err)


    def __init__(self, *args, **kwargs):
        """
        Starts the initialization process by calling helper
        initialization methods.
        """

        # Remove unused options
        empty_keys = [k for k,v in kwargs.items() if not v]
        for k in empty_keys:
            del kwargs[k]

        # preserving $vars means extra quotes
        for k, v in kwargs.items():
            if isinstance(v, str):
                kwargs[k] = v.strip().strip('"').strip("'")

        # store unprocessed kwargs in case they are needed
        self.kwargs = kwargs

        # package level
        satsuki.verbose = kwargs.get('verbose',False)

        # helper inits
        self._init_basic()
        self._init_gb_info()
        self._init_files()
        self._init_tag()
        self._init_internal_command()

        if self.internal_command == Arguments._COMMAND_CREATE:
            self._init_data_blank()
        elif self.internal_command == Arguments._COMMAND_UPDATE \
            or self.internal_command == Arguments._COMMAND_RECREATE:
            self._init_data()

        self._init_summary()

        # this should never happen so an assertion is used
        assert isinstance(self.internal_command, str), \
            "No internal command, user command: " + self.user_command



class ReleaseMgr(object):
    """
    Utility class for managing GitHub releases.

    Attributes:
        args: An instance of satsuki.Arguments containing
            the configuration information for Satsuki.
    """


    def __init__(self, args=None):
        """
        Initialize the instance.

        Args:
            args: An instance of satsuki.Arguments containing
                the configuration information for Satsuki.
        """

        satsuki.verboseprint("ReleaseMgr:")
        if isinstance(args, satsuki.Arguments):
            self.args = args
        else:
            satsuki._error(
                "Initialization requires an instance of satsuki.Arguments.",
                AttributeError
            )


    def _create_release(self):
        """
        Creates a new release.
        """

        satsuki.verboseprint("Creating release:",self.args.rel_name)
        if isinstance(self.args.tag, int):
            # PyGithub will treat it as a release id when finding later
            satsuki._error(
                "Integer tag name given: " + self.args.tag,
                TypeError
            )
        if not isinstance(self.args.target_commitish, str):
            satsuki._error(
                "Commit SHA is required",
                AttributeError
            )

        """
        Call to PyGithub:
        tag, name, message, draft=False, prerelease=False,
        target_commitish=github.GithubObject.NotSet

        https://github.com/PyGithub/PyGithub/blob/master/github/Repository.py
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
        """
        Updates an existing release.
        """

        satsuki.verboseprint(
            "Updating release, id:",
            self.args.working_release.id
        )

        """
        Call to PyGithub:
        name, message, draft=False, prerelease=False

        https://github.com/PyGithub/PyGithub/blob/master/github/GitRelease.py
        """
        self.args.working_release.update_release(
            self.args.rel_name,
            self.args.body,
            draft=self.args.draft,
            prerelease=self.args.pre
        )


    def _find_release_asset(self, id):
        """
        Finds a release asset associated with a release. Since no
        search functionality is available through PyGithub, this is a
        rudamentary search, going through list of assets one at
        a time, comparing filenames, until found.

        Args:
            id: A str or int representing a tag or release ID of a
                release.

        Todo: May not work with long lists of assets, based on
        paginated lists.
        """
        satsuki.verboseprint("Finding asset:", id)

        # get asset list 
        satsuki.verboseprint("Getting asset list")
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

        return None


    def _delete_release_asset(self, filename):
        """
        There is no way to update a release asset's payload (i.e., the
        file). You can update the name and label but to update the file
        you must delete and re-upload. This method allows deleting
        the release asset.
        https://github.com/PyGithub/PyGithub/blob/e9e09b9dda6020b583d17cd727d851c1a79e7150/github/GitReleaseAsset.py#L162

        """
        satsuki.verboseprint("Deleting release asset (if exists):", filename)
        delete_asset = self._find_release_asset(filename)

        if delete_asset is not None:
            satsuki.verboseprint("File exists, deleting...")
            delete_asset.delete_asset()


    def _handle_upload_error(self, error, file_info, complete_filesize):

        satsuki.verboseprint("Upload error!")    
        satsuki.verboseprint("Error:", type(error), error)   
        
        if type(error) in (
            BrokenPipeError, 
            socket.timeout, 
            ConnectionAbortedError
        ):
            # possible non errors
            satsuki.verboseprint("This may be an inconsequential error...")

            release_asset = self._find_release_asset(file_info['filename'])

            if release_asset is not None \
                and hasattr(release_asset, 'size') \
                and release_asset.size == complete_filesize:
                satsuki.verboseprint("File uploaded correctly")
                return release_asset
        
        return None


    def _upload_file(self, file_info):
        """
        Upload an individual file to the release.
        """
        # no way to update uploaded file, so delete->upload
        self._delete_release_asset(file_info['filename'])

        # path, label="", content_type=""
        complete_filesize = os.path.getsize(file_info['path'])
        satsuki.verboseprint(
            "Size of", 
            file_info['filename'], 
            ":", 
            complete_filesize)
        attempts = 0
        success = False

        error = ConnectionError

        while attempts < satsuki.MAX_UPLOAD_ATTEMPTS and not success:
            
            attempts += 1

            upload_args = {}
            if file_info['label'] is None:
                upload_args['label'] = file_info['filename']
            else:
                upload_args['label'] = file_info['label']

            if file_info['mime-type'] is not None:
                upload_args['content_type'] = file_info['mime-type']

            release_asset = None
            error = None

            satsuki.verboseprint("Uploading file:", file_info['filename'])
            satsuki.verboseprint(
                "Attempt:", 
                str(attempts) + '/' + str(satsuki.MAX_UPLOAD_ATTEMPTS)
            )

            try:

                release_asset = self.args.working_release.upload_asset(
                    file_info['path'],
                    **upload_args
                )

            except Exception as exc:
                error = exc

            finally:
                # fix for PyGithub issue
                # renew the repo
                # might be able to remove when PR #771 is merged
                # https://github.com/PyGithub/PyGithub/pull/771
                self.args._get_release()
            
            if error is None \
                and hasattr(release_asset, 'size') \
                and release_asset.size == complete_filesize:
                success = True
            
            else:
                release_asset = self._handle_upload_error(
                    error, 
                    file_info, 
                    complete_filesize
                )         
            
                if release_asset is not None:
                    success = True

        # attempts are done... 

        if success:

            satsuki.verboseprint("Successfully uploaded:", release_asset.name)
            satsuki.verboseprint("Size:", release_asset.size)
            satsuki.verboseprint("ID:", release_asset.id)

        else:
            if error is not None:
                raise error
            else:
                raise ConnectionError


    def _upload_files(self):
        """
        Uploads files to a release.
        """
        files_to_upload = len(self.args.file_info)
        file_uploading = 0

        for file_info in self.args.file_info:

            file_uploading += 1

            satsuki.verboseprint(
                "Uploading file",
                str(file_uploading) + "/" + str(files_to_upload),
                "..."
            )
            satsuki.verboseprint("Prepping upload of", file_info['filename'])

            self._upload_file(file_info)


    def _delete_file(self):
        """
        Deletes a file (i.e., release asset) from a release.
        """

        satsuki.verboseprint("Deleting release asset:",self.args.tag)
        for info in self.args.file_info:
            asset = self._find_release_asset(info['filename'])
            if asset is not None:
                asset.delete_asset()


    def _delete_release(self):
        """
        Deletes a release.
        """

        satsuki.verboseprint("Deleting release:",self.args.tag)

        # delete release
        self.args.working_release.delete_release()

    def _delete_tag(self):
        """
        Attempts to delete tags both from GitHub and git.
        """
        if self.args.internal_command == Arguments._COMMAND_DELETE_TAG \
            or self.args.include_tag:
            satsuki.verboseprint("Cleaning tag(s):",self.args.tag)

            tag_list = self.args.repo.get_tags()
            for tag in tag_list:
                if fnmatch.fnmatch(tag.name, self.args.tag):
                    try:
                        release = self.args.repo.get_release(tag.name)
                        if self.args.force:
                            satsuki.verboseprint("Deleting release:", release.title)
                            release.delete_release()
                            raise github.UnknownObjectException(
                                "404",
                                "Spoof to hit except"
                            )

                        else:
                            satsuki.verboseprint("Tag still connected to "
                                + "release - not deleting:", tag.name)

                    except github.UnknownObjectException as err:

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
        """
        Main method to be called once satsuki.Arguments have been
        configured.

        """
        if self.args.internal_command == Arguments._COMMAND_DELETE_FILE:
            self._delete_file()
        elif self.args.internal_command == Arguments._COMMAND_DELETE_REL:
            self._delete_release()
            self._delete_tag()
        elif self.args.internal_command == Arguments._COMMAND_DELETE_TAG:
            self._delete_tag()
        elif self.args.internal_command == Arguments._COMMAND_RECREATE:
            self._delete_release()
            self._delete_tag()            
            self._create_release()
            self._upload_files()
        elif self.args.internal_command == Arguments._COMMAND_CREATE:
            self._create_release()
            self._upload_files()
        elif self.args.internal_command == Arguments._COMMAND_UPDATE:
            self._update_release()
            self._upload_files()

