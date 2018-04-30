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
    PER_PAGE = 10

    def __init__(self, *args, **kwargs):
        """Instantiation"""

        # Remove unused options
        empty_keys = [k for k,v in kwargs.items() if not v]
        for k in empty_keys:
            del kwargs[k]

        # package level
        satsuki.verbose = kwargs.get('verbose',False)

        # command
        if kwargs.get('command',False):
            self.command = Arguments.COMMAND_UPSERT
        elif kwargs.get('command') == Arguments.COMMAND_UPSERT or \
            kwargs.get('command') == Arguments.COMMAND_DELETE:
            self.command = kwargs.get('command')
        else:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "[ERROR] Invalid command:",
                kwargs.get('command')
            )
            raise AttributeError

        # flags
        self.latest = kwargs.get('latest',False)
        self.pre = kwargs.get('pre',False)
        self.draft = kwargs.get('draft',False)

        # auth - required
        self.api_token = kwargs.get('token',None)
        if self.api_token is None:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "[ERROR] No GitHub API token was provided using "
                + "SATS_TOKEN environment variable."
            )
            raise PermissionError

        # repo / user - required
        self.repo = kwargs.get('repo', None)
        self.user = kwargs.get('user', None)
        if self.repo is None or self.user is None:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "ERROR: User and repo are required."
            )
            raise RuntimeError

        # tag-name - required (or latest)
        self.tag_name = kwargs.get('tag_name', None)
        if self.tag_name is None and not self.latest:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "ERROR: Either tag name or the latest flag is "
                + "required."
            )
            raise RuntimeError

        # the rest
        self.rel_name = kwargs.get('rel_name', self.tag_name)
        self.body = kwargs.get('body', None)
        self.commitish = kwargs.get('commitish', None)
        self.files = kwargs.get('file', [])
        self.label = kwargs.get('label', None)
        self.mime = kwargs.get('mime', None)

        satsuki.verboseprint("Arguments:")
        satsuki.verboseprint("command:",self.command)
        satsuki.verboseprint("repo:",self.repo)
        satsuki.verboseprint("user:",self.user)
        satsuki.verboseprint("latest:",self.latest)
        satsuki.verboseprint("pre:",self.pre)
        satsuki.verboseprint("draft:",self.draft)
        satsuki.verboseprint("tag_name:",self.tag_name)
        satsuki.verboseprint("rel_name:",self.rel_name)
        satsuki.verboseprint("body:",self.body)
        satsuki.verboseprint("commitish:",self.commitish)
        satsuki.verboseprint("label:",self.label)
        satsuki.verboseprint("mime:",self.mime)
        satsuki.verboseprint("# files:",len(self.files))

        if self.files is not None:
            for one_file in self.files:
                satsuki.verboseprint("file:",one_file)


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

        self.args = args


        satsuki.verboseprint("ReleaseMgr:")

        self._get_latest()


    def _get_latest(self):
        satsuki.verboseprint("Getting latest release")
        gh = github.Github(self.args.api_token, per_page=Arguments.PER_PAGE)
        repository = gh.get_repo(self.args.user + '/' + self.args.repo)
        releases = repository.get_releases()

        for release in releases:
            print('release ', release)
            print('tag: ', release.tag_name)
            print('title: ', release.title)
            print('url: ', release.url)


