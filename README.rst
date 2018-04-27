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


=====  =====
col 1  col 2
=====  =====
1      Second column of row 1.
2      Second column of row 2.
       Second line of paragraph.
3      - Second column of row 3.

       - Second item in bullet
         list (row 3, column 2).
\      Row 4; column 1 will be empty.
=====  =====



=======         ===============   ==========================================
ENV VAR         CL Options        Desciption
=======         ===============   ==========================================
SATS_API_KEY    None              An OAUTH token with repo access.
SATS_TAG_NAME   -t, --tag-name    (**Required**) Either the tag name
                                  *OR* the ``latest`` option must be
                                  provided. If both are used, tag name
                                  takes precedence.

(None)          -l, --latest      (**Required**) Either this option
                                  *OR* ``--tag-name`` must be used.
                                  When used, Satsuki will perform any
                                  operations on the latest release.

(None)          -u, --upsert      Indicates to either update or create
                                  the release with the provided
                                  information.
=======         ==========        ==========================================

