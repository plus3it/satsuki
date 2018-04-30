=======
Satsuki
=======

.. image:: https://img.shields.io/github/license/YakDriver/satsuki.svg
    :target: ./LICENSE
    :alt: License
.. image:: https://travis-ci.org/YakDriver/satsuki.svg?branch=master
    :target: http://travis-ci.org/YakDriver/satsuki
    :alt: Build Status
.. image:: https://img.shields.io/pypi/pyversions/satsuki.svg
    :target: https://pypi.python.org/pypi/satsuki
    :alt: Python Version Compatibility
.. image:: https://img.shields.io/pypi/v/satsuki.svg
    :target: https://pypi.python.org/pypi/satsuki
    :alt: Version


**Satsuki** is a Python package that helps manage GitHub releases and release assets.
Satsuki is especially useful paired with Continuous Integration/
Continuous Deployment (CI/CD)
tools such as `Travis CI <https://travis-ci.org>`_ and `AppVeyor <https://www.appveyor.com>`_.

Why not just use the Travis CI GitHub Releases provider? Good question.
The simple answer is that the provider doesn't work very well yet.
In specific, you can't update an existing release or add files
(assets) to a release or provide a release body and a release asset
at the same time.

Satsuki and Travis CI Example
=============================

This example shows setting up Travis CI with your GitHub OAUTH token
for use by Satsuki, and then creating releases and uploading assets.

**Step 1: Encrypt OAUTH Token**

Using Travis's command line tool, encrypt your OAUTH token *with* the
environment variable name. NOTE: the encrypt is on a repo by repo
basis so the encrypted value will only work on the repo under it was
created.

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

We'll use the ``script`` step to build an application into a OS-
machine specific binary using `GravityBee <https://github.com/YakDriver/gravitybee>`_.

.. code-block:: yaml

    install:
      - pip install gravitybee satsuki
    script:
      - gravitybee --src-dir src --verbose --clean


**Step 4: Setup the Travis YAML Before Deploy Step**

Here assign
values to environment variables so that Satsuki can use them to
create the release and we'll tag the release.

.. code-block:: yaml

    before_deploy:
      - export SATS_TAG_NAME=$(grep "version = " $TRAVIS_BUILD_DIR/setup.cfg | sed "s/version = //")
      - export SATS_BODY="* Here is the body for the release"
      - export SATS_FILE="mysuperapp-1.2.3-standalone-linux-x86_64"
      - git tag -a $SATS_TAG_NAME -m "This is the v$SATS_TAG_NAME message"


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

For environment variable flags, the existence of the environment variable
is sufficient to trigger the flag. It can be set to any value.


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
SATS_REPO         -r, --repo        **[Required]** The GitHub repository to
                                    work with.
SATS_USER         -u, --user        **[Required]** The owner of the repository
                                    to work with.
SATS_TAG_NAME     -t, --tag-name    **[Required]** Either the tag name
                                    *OR* the ``--latest`` option must be
                                    provided. If both are used, tag name
                                    takes precedence.
SATS_REL_NAME     -n, --rel-name    The name of the release.
                                    *Default: tag name*
SATS_LATEST       --latest          **[Required][Flag]** Either this option
                                    *OR* ``--tag-name`` must be used.
                                    When used, Satsuki will perform any
                                    operations on the latest release.
                                    *Default: Not*
SATS_BODY         -b, --body        The blurb that shows up with releases.
                                    *Default: None*
SATS_COMMITISH    -o, --commitish   Specifies the commitish value that
                                    determines where the Git tag is created
                                    from. *Default: None*
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
                                    lable. *Default: GitHub will use the raw
                                    file name.*
SATS_MIME         -m, --mime        The mime type for files. *Default:
                                    A guess of the file type or*
                                    ``application/octet-stream`` *if all else
                                    fails.*
SATS_PRERELEASE   -p, --pre         **[Flag]** Whether or not this release
                                    is a prerelease. *Default: Not*
SATS_DRAFT        -d, --draft       **[Flag]** Whether or not this release
                                    is a draft. *Default: Not*
SATS_VERBOSE      -v, --verbose     **[Flag]** Verbose mode. *Default: Not*
================  ===============   ==========================================





