=======
Satsuki
=======

.. image:: https://img.shields.io/github/license/plus3it/satsuki.svg
    :target: ./LICENSE
    :alt: License
.. image:: https://travis-ci.org/plus3it/satsuki.svg?branch=master
    :target: http://travis-ci.org/plus3it/satsuki
    :alt: Build Status
.. image:: https://ci.appveyor.com/api/projects/status/9f0bdlgdc9em6bqc?svg=true
    :target: https://github.com/plus3it/satsuki
    :alt: Build Status
.. image:: https://img.shields.io/pypi/pyversions/satsuki.svg
    :target: https://pypi.python.org/pypi/satsuki
    :alt: Python Version Compatibility
.. image:: https://img.shields.io/pypi/v/satsuki.svg
    :target: https://pypi.python.org/pypi/satsuki
    :alt: Version
.. image:: https://pullreminders.com/badge.svg
    :target: https://pullreminders.com?ref=badge
    :alt: Pull Reminder

**Satsuki** (*pronounced SAHT-ski*) is a Python package that helps
manage GitHub releases and release assets.
Satsuki is especially useful paired with Continuous Integration/
Continuous Deployment (CI/CD)
tools such as `Travis CI <https://travis-ci.org>`_ and `AppVeyor <https://www.appveyor.com>`_.

Why not just use the Travis CI GitHub Releases provider? Good question.
The simple answer is that the provider doesn't work very well yet.
In specific, you can't update an existing release or add files
(assets) to a release or provide a release message and a release asset
at the same time.

Satsuki and Travis CI Example
=============================

This example shows setting up Travis CI with your GitHub OAUTH token
for use by Satsuki, and then creating releases and uploading assets.

**Step 1: Encrypt OAUTH Token**

Using Travis's command line tool, encrypt your OAUTH token *with* the
environment variable name. NOTE: Travis CI encrypts values on a repo
by repo
basis. Thus, a value encrypted for one repo will not work in another
repo, even if commonly owned.

.. code-block:: bash

    $ cd myrepodir
    $ travis encrypt SATS_TOKEN=YOUR_GITHUB_OATH_TOKEN
    Please add the following to your .travis.yml file:

    secure: "SBKfniOex/LRjHrN/IVQHyKquTxGRY6UxZhrPd1fMsFHu+1Jl8GGkMX8wZ8GL29S0GgIZwDVHBwu3kVcX0xJWmRrLf9kcUrN5RdbTn7KxAxqboJKLolJqXhbSE1pZBUm1IbY3BuL0hZ4oYg8KyuARnanF0PXjpJTFysYq9cYwolc4XzZ0EOXRNCSBLkcIUsULhunFHPKxaATEwUMgnOIYHkBMdfjVynuW1hqhgwAstpfhNvryir6vbZla7M3/EBTqJjuGhXTf1U6YWubGFBXNDwqIqRurMHRC0pyqc/NpEUhgFANTqs3ax/Ka0cnZAxoq99rPWe9ZtElN/GKrjJT6STPjfsaCC6ls3JFC0aorEuMMH+2pqEr7p3Llbs1OkBnZKD7aTNQxmMimZ78yq6snSM5zew9Nxjv0lytZOpHQXFtjXJtc8YcXcWylYSngMnRVnPzxFADn4udNdFZzP8+HZEkkKHJXaICu0Vx15ll4tEo1I2BJQ/ViV4sjo6KfAL3ZqC6RTjs2aqnMHu7i8DrQzYlmRXsKr2HyVudN3cgAgK5cZkJArCjxu8glY5OrFvSxjKOF1tno8Zrhne6xyBcQfVXP7gqQYQ/sUx1dqTc7XPqkB4r4OkmXH+Af7jRQahQxk04+vahtrKJX4WEYeA4teOAYN2xWsbvdrCcIvgUXNx="


**Step 2: Add Token to Travis YAML**

Now, we'll add this secure value to the ``.travis.yml`` file in our repo.
Only Travis CI can decrypt this value now. (Although this shows Python
as the language, Satsuki will work with projects in other languages
as long as you install Python 3 and pip.)

.. code-block:: yaml

    language: python
    sudo: false
    env:
      global:
        - secure: SBKfniOex/LRjHrN/IVQHyKquTxGRY6UxZhrPd1fMsFHu+1Jl8GGkMX8wZ8GL29S0GgIZwDVHBwu3kVcX0xJWmRrLf9kcUrN5RdbTn7KxAxqboJKLolJqXhbSE1pZBUm1IbY3BuL0hZ4oYg8KyuARnanF0PXjpJTFysYq9cYwolc4XzZ0EOXRNCSBLkcIUsULhunFHPKxaATEwUMgnOIYHkBMdfjVynuW1hqhgwAstpfhNvryir6vbZla7M3/EBTqJjuGhXTf1U6YWubGFBXNDwqIqRurMHRC0pyqc/NpEUhgFANTqs3ax/Ka0cnZAxoq99rPWe9ZtElN/GKrjJT6STPjfsaCC6ls3JFC0aorEuMMH+2pqEr7p3Llbs1OkBnZKD7aTNQxmMimZ78yq6snSM5zew9Nxjv0lytZOpHQXFtjXJtc8YcXcWylYSngMnRVnPzxFADn4udNdFZzP8+HZEkkKHJXaICu0Vx15ll4tEo1I2BJQ/ViV4sjo6KfAL3ZqC6RTjs2aqnMHu7i8DrQzYlmRXsKr2HyVudN3cgAgK5cZkJArCjxu8glY5OrFvSxjKOF1tno8Zrhne6xyBcQfVXP7gqQYQ/sUx1dqTc7XPqkB4r4OkmXH+Af7jRQahQxk04+vahtrKJX4WEYeA4teOAYN2xWsbvdrCcIvgUXNx=

**Step 3: Setup the Travis YAML Script Step**

We'll use the ``script`` step to build an application into an
OS/machine specific binary using
`GravityBee <https://github.com/plus3it/gravitybee>`_.

.. code-block:: yaml

    install:
      - pip install gravitybee satsuki
    script:
      - gravitybee --src-dir src --clean


**Step 4: Setup the Travis YAML Before Deploy Step**

Next, ssign
values to environment variables so that Satsuki can use them to
create the release and tag. Optionally, you can
also use
special variables in Satsuki that will be substituted with
values from GravityBee.  See **Variable Substitution** below.

.. code-block:: yaml

    before_deploy:
      - export SATS_TAG=$(grep "version = " $TRAVIS_BUILD_DIR/setup.cfg | sed "s/version = //")
      - export SATS_BODY="* Here is the message for the release"
      - export SATS_FILE="mysuperapp-1.2.3-standalone-linux-x86_64"


**Step 5: Setup the Travis YAML Deploy Step**

Everything should be set now to deploy.

.. code-block:: yaml

    deploy:
      - provider: script
        script: satsuki
        skip_cleanup: true
        on:
          branch: master
          repo: YakDriver/mysuperapp
          python: "3.6"


Now if you've enabled your repo on Travis CI, when you commit to the
master branch, if all goes well, you'll get a release with your binary
file associated with it.


Reference
=========

Satsuki can be used with command line (CL) options or environment
variables, or a mix of both. If both are provided, command line
options take precedence.


Options
-------

Using Satsuki, you can create releases. A release is a GitHub feature.
However, a release is related to a tag, which is a pure Git feature. (If
the tag doesn't exist, Satsuki will create it along with the release.)
You can also create assets (e.g., binary files) that are
associated with releases. Thus Satsuki has options that relate to each:
Asset ==> Release ==> Tag.

Options from each, tag, release, and asset, can be provided at
the same time,
and Satsuki
will attempt to act appropriately on each. For example, in one
command you can create a tag, release, and asset.

Release/Satsuki Related
-----------------------

Local logging can be configured in ``satsuki/logging.conf``.

================  ===============   ==========================================
ENV VAR           CL Options        Desciption
================  ===============   ==========================================
SATS_TOKEN        --token           **[Required]** An OAUTH token with
                                    repo access.
SATS_COMMAND      -c, --command     The operation to perform on the GitHub
                                    release. Choose from ``upsert`` or
                                    ``delete``. If ``delete`` is selected and a
                                    file is provided, the file (release
                                    asset) is deleted instead of the release.
                                    *Default:* ``upsert``
SATS_RECREATE_OK  --recreate        **[Flag]** Indicates whether a release
                                    commitish can be updated by deleting
                                    and recreating the release. Otherwise,
                                    a release cannot be updated with a new
                                    commit SHA. If this flag is set,
                                    ``--include-tag`` is implied.
                                    *Default: not*
SATS_SLUG         -s, --slug        **[Required]** Either repo and user or
                                    the slug (in the form user/repo) must be
                                    provided. *If not provided, it will default
                                    to the value provided by Travis CI, Azure
                                    Pipelines or AppVeyor, if any.*
SATS_REPO         -r, --repo        **[Required]** The GitHub repository to
                                    work with.
SATS_USER         -u, --user        **[Required]** The owner of the repository
                                    to work with.
SATS_REL_NAME     -n, --rel-name    The name of the release. **Available for
                                    variable substitution.
                                    See below.**
                                    *Default: tag name*
SATS_LATEST       --latest          **[Required][Flag]** Either this option
                                    *OR* ``--tag`` must be used.
                                    When used, Satsuki will perform any
                                    operations on the latest release.
                                    *Default: Not*
SATS_BODY         -b, --body        The message that shows up with releases.
                                    **Available for variable substitution.
                                    See below.**
                                    *Default: Release <tag>*
SATS_PRE          -p, --pre         **[Flag]** Whether or not this release
                                    is a prerelease. *Default: Not*
SATS_DRAFT        -d, --draft       **[Flag]** Whether or not this release
                                    is a draft. *Default: Not*
SATS_FORCE        --force           **[Flag]** Force Satsuki to delete items
                                    when normally it would not. **CAUTION:**
                                    You could easily delete every
                                    release in your repository with this.
                                    *Default: Not*
================  ===============   ==========================================


Tag Related
-----------

================  ===============   ==========================================
ENV VAR           CL Options        Desciption
================  ===============   ==========================================
SATS_TAG          -t, --tag         **[Required]** Either the tag
                                    *OR* the ``--latest`` option must be
                                    provided. If both are used, tag
                                    takes precedence. In finding existing
                                    releases, the "tag" value may be either
                                    the release ID (e.g., 10746271) or tag
                                    name (e.g., v0.1.0). However, if a
                                    release ID is provided, and it does not
                                    exist, an error will be thrown to avoid
                                    creating a tag with an ID-like name.
                                    **Available for variable substitution.
                                    See below.**
                                    *If not provided,
                                    will default
                                    to the value provided by Travis CI or
                                    AppVeyor, if any.*
SATS_COMMITISH    --commitish       Can be any branch or commit SHA. Unused
                                    if the Git tag already exists.
                                    *If not provided, it will
                                    default
                                    to the TRAVIS_COMMIT environment variable
                                    provided by
                                    Travis CI or BUILD_SOURCEVERSION from Azure
                                    Pipelines or APPVEYOR_REPO_COMMIT from
                                    AppVeyor, if any. If none is provided,
                                    GitHub will default to the default branch.*
SATS_INCLUDE_TAG  --include-tag     Whether to delete the tag when deleting the
                                    release. If the provided tag does not match
                                    a release, the tag will be deleted. If the
                                    tag includes a POSIX-style filename pattern
                                    match, all tags which aren't associated
                                    with releases will be deleted. This is
                                    handy for cleaning up tags. If you have
                                    many tags to cleanup, you may need to run
                                    this multiple times to complete the
                                    cleaning. *Default: Not*
================  ===============   ==========================================


Asset Related
-------------

These options can be used multiple times. If there is one label or one MIME
type, and multiple files, the same label and MIME type will be applied to each
file. Otherwise, there must be the same number of labels and/or MIME types as
files, or an error will be thrown.

================  ===============   ==========================================
ENV VAR           CL Options        Desciption
================  ===============   ==========================================
SATS_FILE         -f, --file        File(s) to be uploaded as release asset(s).
                                    If the file name contains an asterik (*)
                                    it will be treated as a POSIX-style glob
                                    and all matching files will be uploaded.
                                    This option can be used multiple times
                                    to upload multiple files.
                                    *Default: No file is uploaded.*
SATS_LABEL        -l, --label       Label to display for files instead of the
                                    file name. Not recommended with multiple
                                    file upload since all will share the same
                                    label. **Available for variable
                                    substitution.
                                    See below.** *Default: GitHub will
                                    use the raw
                                    file name.*
SATS_MIME         -m, --mime        The mime type for files. *Default:
                                    A guess of the file type or*
                                    ``application/octet-stream`` *if all else
                                    fails.*
SATS_FILE_SHA     --file-sha        Whether to create SHA256 hashes for upload
                                    files, and either append them to the file
                                    label or upload them in a separate file.
                                    Valid options are: ``none``, ``file``, and
                                    ``label``. *Default: none*
SATS_FILES_FILE   --files-file      Name of JSON file with information about
                                    file(s) to upload.
                                    See below.
                                    *Default: Will look for*
                                    ``gravitybee-files.json``
================  ===============   ==========================================


Variable Substitution
---------------------

For certain values, you can optionally include variables
that will be
substituted using information from GravityBee.
Whether variables are replaced depends
on all the following conditions being met:

* The GravityBee info file (``gravitybee-info.json``) is in
  the current directory.
* The file is correctly formatted JSON.
* The file uses the correct structure defined by GravityBee.
* The variables within the environment variables are spelled
  correctly and not
  replaced prior to getting to Satsuki (e.g., by the shell
  or OS).

If you're having trouble getting substitutions to work,
try displaying environment variables (e.g., using
``env`` on POSIX systems or ``SET`` on Windows) to make sure
$s haven't been replaced. On POSIX, use single quotes when setting
environment variables to prevent premature substitution.

These are the variables you can use.

=====================   ==========================================
VARIABLE                Desciption
=====================   ==========================================
$gb_pkg_ver             The version of the package extracted by
                        GravityBee from setup.py or setup.cfg.
$gb_pkg_name            The name of the package extracted by
                        GravityBee from setup.py or setup.cfg,
                        which is often the application name.
$gb_pkg_name_lower      Same as $gb_pkg_name but lowercase.
$gb_sa_app              The name of the binary file, standalone
                        application created by GravityBee.
=====================   ==========================================

An example of using substitution.

.. code-block::

    $ export SATS_TAG='$gb_pkg_ver' # will be replaced with 4.2.6, for example


The Files File
--------------

Satsuki also accepts a JSON-formatted file containing information about
assets to be uploaded (see the ``--files-file`` option above). The file
can contain information about multiple files and should contain
information about files
accessible to Satsuki, with paths relative to the directory in which
Satsuki is run. A file in the correct format is generated by
`GravityBee <https://github.com/plus3it/gravitybee>`_.

Satsuki will always look in the current directory for a GravityBee
files file (``gravitybee-files.json``). If found, Satsuki will
upload the specified files. To avoid this behavior, remove a
GravityBee files file from the current directory. You can also use
a GravityBee files file in another location, besides the current
directory, by using the ``--files-file`` flag.

This is an example of the format.

.. code-block::

    [{'filename': 'gbtestapp-4.2.6-standalone-osx-x86_64',
      'label': 'gbtestapp Standalone Executable (gbtestapp-4.2.6-standalone-osx-x86_64) [GravityBee Build]',
      'mime-type': 'application/x-executable',
      'path': '/path/to/file/gbtestapp-4.2.6-standalone-osx-x86_64'}]


Command-Line Examples
---------------------

Here is an example of using Satsuki to clean up tags.
This command will delete all tags not connected to a release that
match the pattern ``Test-*``. To be able to clean tags,
Satsuki must be run from the ``git`` directory of the repo.

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag Test-* -c delete -v


Delete the release asset with the filename
``release-asset.exe`` from the release tagged with ``Test-ve8226c``.

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag Test-ve8226c -c delete -v --file release-asset.exe


Create a new release and tag called ``testtag`` based
on the given commit SHA, and upload the file ``release-asset.exe`` as an
asset of the new release.

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag testtag --commitish 42b8b9f3f44e0a11071cd3c56eaed29a305c3339 \
    -v --file release-asset.exe

Delete the release called ``1.2.3``.

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag 1.2.3 -c delete -v

Delete the release and local and/or remote tags called ``1.2.3``.

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag 1.2.3 -c delete -v --include-tag

Delete ALL releases and local and/or remote tags matching ``Test-*``.
**USE CAUTION!**

.. code-block::

    $ satsuki -s "<OWNER>/<REPO>" --token <YOUR_GITHUB_OATH_TOKEN> \
    --tag Test-* -v -c delete --include-tag --force



The First Confirmed Upload SHA
------------------------------

``25c2f15b0c332bf58d5e625f54525873bcddc2083578b335fdc4a1be8d79edda``
