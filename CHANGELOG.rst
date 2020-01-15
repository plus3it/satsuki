CHANGE LOG
==========

0.1.16 - 2020.01.14
-------------------
* [ENHANCEMENT] New version with updated dependencies versions.

0.1.15 - 2019.05.06
-------------------
* [ENHANCEMENT] New version with updated dependencies versions.

0.1.14 - 2019.04.22
-------------------
* [ENHANCEMENT] New version with updated dependencies versions.

0.1.13 - 2019.01.29
-------------------
* [ENHANCEMENT] Clean up code.
* [ENHANCEMENT] Transfer to Plus3IT.

0.1.12 - 2019.01.25
-------------------
* [ENHANCEMENT] Code clean up.
* [ENHANCEMENT] Add pylint, flake8 to CI.
* [ENHANCEMENT] Revamp Travis CI to test Windows, Mac, Linux.

0.1.11 - 2018.06.05
-------------------
* [ENHANCEMENT] Updated for compatibility with GravityBee's
  new directory structure (using ``.gravitybee`` directory).

0.1.10 - 2018.05.25
-------------------
* [ENHANCEMENT] Updated for compatibility with GravityBee.

0.1.9 - 2018.05.25
------------------
* [ENHANCEMENT] Code clean up.
* [ENHANCEMENT] Changed SHA default to None.
* [BUG FIX] Fixed bug in tests affecting SHA hash test.

0.1.8 - 2018.05.14
------------------
* [ENHANCEMENT] Tag can now be based on info file written by
  GravityBee (app version from).
* [ENHANCEMENT] Allow sha256 hashes to be added to label or uploaded
  as a separate file.
* [ENHANCEMENT] Improved testing of SHA hash (downloading file and
  recalculating.
* [ENHANCEMENT] Added ability to recreate releases in order to
  update the tag/commitish associated with the release. Otherwise,
  releases can be updated but will always point to the same tag/
  commitish.
* [BUG FIX] Fixed various bugs with SHA hashes, creating releases,
  deleting tags, and revamped upload error handling.

0.1.7 - 2018.05.11
------------------
* [BUG FIX] Many bug fixes improving compatibility with Windows.
* [ENHANCEMENT] Use new GravityBee file (``gravitybee-files.json``).

0.1.6 - 2018.05.10
------------------
* [BUG FIX] Wasn't deleting release asset if file given that didn't
  exist locally.
* [ENHANCEMENT] Added --force option to delete tags and releases
  using pattern matching.

0.1.5 - 2018.05.10
------------------
* [BUG FIX] Implemented file (release asset) delete
* [ENHANCEMENT] Generally improved asset handling including SHA256 sums
  for files and better error handling

0.1.4 - 2018.05.08
------------------
* [BUG FIX] Looked like an error was occuring because returning True
  instead of os.EX_OK.

0.1.3 - 2018.05.07
------------------
* [ENHANCEMENT] Added POSIX-style filename pattern matching for
  cleaning up tags.

0.1.2 - 2018.05.07
------------------
* Initial release!
