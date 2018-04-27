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

Satsuki and Travis CI Example
=============================



Reference
=========

Satsuki can be used with command line (CL) options or environment
variables, or a mix of both. If both are provided, command line
options take precedence.

Command Flags
-------------

==============  ===============   ==========================================
ENV VAR         CL Options        Desciption
==============  ===============   ==========================================
(None)          --upsert          **[Default]** Either update or create
                                  the release with the provided
                                  information and/or upload a release
                                  asset.
(None)          --delete          Delete the release. If a file is provided,
                                  the file (release asset) is deleted instead.
==============  ===============   ==========================================


Information Options
-------------------

For environment variable flags, the existence of the environment variable
is sufficient to trigger the flag. It can be set to any value.


================  ===============   ==========================================
ENV VAR           CL Options        Desciption
================  ===============   ==========================================
SATS_API_KEY      None              **[Required]** An OAUTH token with
                                    repo access.
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
SATS_COMMITISH    -c, --commitish   Specifies the commitish value that
                                    determines where the Git tag is created
                                    from. *Default: None*
SATS_FILE         -f, --file        File(s) to be uploaded as release asset(s).
                                    If the file name contains an asterik (*)
                                    it will be treated as a POSIX-style glob
                                    and all matching files will be uploaded.
                                    *Default: No file is uploaded.*
SATS_LABEL        -l, --label       Label to display for files instead of the
                                    file name. Not recommended with multiple
                                    file upload since all will share the same
                                    lable. *Default: GitHub will use the raw
                                    file name.*
SATS_MIME         -m, --mime        The mime type for files. *Default:
                                    A guess of the file type or
                                    ``application/octet-stream`` if all else
                                    fails.*
SATS_PRERELEASE   -p, --pre         **[Flag]** Whether or not this release
                                    is a prerelease. *Default: Not*
SATS_DRAFT        -d, --draft       **[Flag]** Whether or not this release
                                    is a draft. *Draft: Not*
================  ===============   ==========================================





