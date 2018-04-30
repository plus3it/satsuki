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

    def __init__(self, *args, **kwargs):
        """Instantiation"""

        # Remove unused options
        empty_keys = [k for k,v in kwargs.items() if not v]
        for k in empty_keys:
            del kwargs[k]

        # package level
        satsuki.verbose = kwargs.get('verbose',False)

        # flags
        if kwargs.get('upsert',False):
            self.command = Arguments.COMMAND_UPSERT
        elif kwargs.get('delete',False):
            self.command = Arguments.COMMAND_DELETE
        else:
            self.command = Arguments.COMMAND_UPSERT

        self.latest = kwargs.get('latest',False)
        self.pre = kwargs.get('pre',False)
        self.draft = kwargs.get('draft',False)

        # auth - required
        self.api_token = os.environ.get('SATS_TOKEN', None)
        if self.api_token is None:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "ERROR: No GitHub API token was provided using "
                + "SATS_TOKEN environment variable."
            )
            raise PermissionError

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

        sys.exit()

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
        satsuki.verboseprint("operating_system:",self.operating_system)
        satsuki.verboseprint("machine_type:",self.machine_type)
        satsuki.verboseprint("standalone_name:",self.standalone_name)


    def _get_latest(self):
        client = Github(config.get_github_token(), per_page=PER_PAGE)
        user = client.get_user('PyGithub')
        repository = client.get_repo('PyGithub')
        releases = repository.get_releases()

        for release in releases:
            print 'release ', release
            print 'release.name ', release.name
            
        # get the hook ready
        template = Template(open(os.path.join(self.gb_dir, "hook-template"), "r").read())

        hook = template.safe_substitute({ 'app_name': self.args.app_name })

        # 1 extra data
        hook += "# collection extra data, if any (using --extra-data option)"
        try:
            for data in self.args.extra_data:
                #datas.append(('../src/watchmaker/static', './watchmaker/static'))
                hook += "\ndatas.append(('"
                hook += self.args.pkg_dir + os.sep
                if self.args.src_dir != '.':
                    hook += self.args.src_dir + os.sep
                hook += self.args.pkg_name + os.sep + data
                hook += "', '" + self.args.pkg_name + "/" + data + "'))"
                hook += "\n\n"
        except:
            pass

        # 2 package metadata
        hook += "# add dependency metadata"
        for package in satsuki.pyppy.get_required():
            #datas += copy_metadata(pkg)
            hook += "\ndatas += copy_metadata('" + package + "')"
        hook += "\n"

        # 3 write file
        self.hook_file = os.path.join(self.args.work_dir, "hook-" + self.args.pkg_name + ".py")
        f = open(self.hook_file,"w+")
        f.write(hook)
        f.close()

        satsuki.verboseprint("Created hook file:",self.hook_file)

    def _cleanup(self):
        # set self.created_file ad self.created_path even if not deleting
        for standalone in glob.glob(os.path.join(self.args.work_dir, 'dist', self.standalone_name + '*')):
            self.created_path = standalone
            self.created_file = os.path.basename(self.created_path)
            satsuki.verboseprint("Filename:", self.created_file)

        if self.args.clean:
            satsuki.verboseprint("Cleaning up...")

            # clean work dir
            # get standalone app out first if it exists
            satsuki.verboseprint("Moving standalone application to current directory:")
            if os.path.exists(os.path.join(os.getcwd(), self.created_file)):
                satsuki.verboseprint("File already exists, removing...")
                os.remove(os.path.join(os.getcwd(), self.created_file))
            shutil.move(self.created_path, os.getcwd())

            # new path for app now it's been copied
            self.created_path = os.path.join(os.getcwd(), self.created_file)

            if os.path.isdir(self.args.work_dir):
                satsuki.verboseprint("Deleting working dir:", self.args.work_dir)
                shutil.rmtree(self.args.work_dir)

        satsuki.verboseprint("Absolute path of standalone:", self.created_path)

    def generate(self):
        """
        if self.operating_system.lower() == 'linux':
            src_path = '/var/opt/git/watchmaker/src'
            additional_hooks = '/var/opt/git/satsuki/pyinstaller'
        elif self.operating_system.lower() == 'windows':
            src_path = 'C:\\git\\watchmaker\\src'
            additional_hooks = 'C:\\git\\satsuki\\pyinstaller'
        """

        self._create_hook()

        try:
            shutil.copy2(self.args.script_path, self._temp_script)
        except FileNotFoundError:
            print(
                satsuki.VERB_MESSAGE_PREFIX,
                "ERROR: Satsuki could not find your application's " +
                "script in the virtual env that was installed by pip. " +
                "Possible solutions:\n1. Run Satsuki in a virtual " +
                "env;\n2. Point Satsuki to the script using the " +
                "--script option;\n3. Install your application using " +
                "pip;\n4. Make sure your application has a console " +
                "script entry in setup.py or setup.cfg."
            )
            self._cleanup()
            return False

        commands = [
            'pyinstaller',
            '--noconfirm',
            #'--clean',
            '--onefile',
            '--name', self.standalone_name,
            '--paths', self.args.src_dir,
            '--additional-hooks-dir', self.args.work_dir,
            '--specpath', self.args.work_dir,
            '--workpath', os.path.join(self.args.work_dir, 'build'),
            '--distpath', os.path.join(self.args.work_dir, 'dist'),
            '--hidden-import', self.args.pkg_name,
            # This hidden import is introduced by botocore.
            # We won't need this when this issue is resolved:
            # https://github.com/pyinstaller/pyinstaller/issues/1844
            '--hidden-import', 'html.parser',
            # This hidden import is also introduced by botocore.
            # It appears to be related to this issue:
            # https://github.com/pyinstaller/pyinstaller/issues/1935
            '--hidden-import', 'configparser',
            #'--hidden-import', 'packaging', # was required by pyinstaller for a while
            #'--hidden-import', 'packaging.specifiers', # was required by pyinstaller for a while
            '--hidden-import', 'pkg_resources',
        ]

        # get all the packages called for by package
        for pkg in satsuki.pyppy.get_required():
            commands += [
                '--hidden-import', pkg,
            ]

        commands += [
            self._temp_script
        ]

        if self.operating_system != 'windows':
            insert_point = commands.index('--onefile') + 1
            commands[insert_point:insert_point] = ['--runtime-tmpdir', '.']

        satsuki.verboseprint("PyInstaller commands:")
        satsuki.verboseprint(*commands, sep=', ')

        subprocess.run(
            commands,
            check=True)

        self._cleanup()
        return True

