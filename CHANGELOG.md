## Changelog

### 0.1.19

**Commit Delta**: [Change from 0.1.17 release](https://github.com/plus3it/watchmaker/compare/0.1.17...0.1.19)

**Released**: 2020.02.27

**Summary**:

* (ENHANCEMENT) Improve integration with Azure Pipelines, using commitish and repository slug automatically.

### 0.1.17

**Commit Delta**: [Change from 0.1.16 release](https://github.com/plus3it/watchmaker/compare/0.1.16...0.1.17)

**Released**: 2020.01.15

**Summary**:

* (ENHANCEMENT) Remove pipenv files, update setup.cfg dependency versions.

### 0.1.16

**Commit Delta**: [Change from 0.1.15 release](https://github.com/plus3it/watchmaker/compare/0.1.15...0.1.16)

**Released**: 2020.01.14

**Summary**:

* (ENHANCEMENT) New version with updated dependencies versions.

### 0.1.15

**Commit Delta**: [Change from 0.1.14 release](https://github.com/plus3it/watchmaker/compare/0.1.14...0.1.15)

**Released**: 2019.05.06

**Summary**:

* (ENHANCEMENT) New version with updated dependencies versions.

### 0.1.14

**Commit Delta**: [Change from 0.1.13 release](https://github.com/plus3it/watchmaker/compare/0.1.13...0.1.14)

**Released**: 2019.04.22

**Summary**:

* (ENHANCEMENT) New version with updated dependencies versions.

### 0.1.13

**Commit Delta**: [Change from 0.1.12 release](https://github.com/plus3it/watchmaker/compare/0.1.12...0.1.13)

**Released**: 2019.01.29

**Summary**:

* (ENHANCEMENT) Clean up code.
* (ENHANCEMENT) Transfer to Plus3IT.

### 0.1.12

**Commit Delta**: [Change from 0.1.11 release](https://github.com/plus3it/watchmaker/compare/0.1.11...0.1.12)

**Released**: 2019.01.25

**Summary**:

* (ENHANCEMENT) Code clean up.
* (ENHANCEMENT) Add pylint, flake8 to CI.
* (ENHANCEMENT) Revamp Travis CI to test Windows, Mac, Linux.

### 0.1.11

**Commit Delta**: [Change from 0.1.10 release](https://github.com/plus3it/watchmaker/compare/0.1.10...0.1.11)

**Released**: 2018.06.05

**Summary**:

* (ENHANCEMENT) Updated for compatibility with GravityBee's new directory structure (using ``.gravitybee`` directory).

### 0.1.10

**Commit Delta**: [Change from 0.1.9 release](https://github.com/plus3it/watchmaker/compare/0.1.9...0.1.10)

**Released**: 2018.05.25

**Summary**:

* (ENHANCEMENT) Updated for compatibility with GravityBee.

### 0.1.9

**Commit Delta**: [Change from 0.1.8 release](https://github.com/plus3it/watchmaker/compare/0.1.8...0.1.9)

**Released**: 2018.05.25

**Summary**:

* (ENHANCEMENT) Code clean up.
* (ENHANCEMENT) Changed SHA default to None.
* (FIX) Fixed bug in tests affecting SHA hash test.

### 0.1.8

**Commit Delta**: [Change from 0.1.7 release](https://github.com/plus3it/watchmaker/compare/0.1.7...0.1.8)

**Released**: 2018.05.14

**Summary**:

* (ENHANCEMENT) Tag can now be based on info file written by GravityBee (app version from).
* (ENHANCEMENT) Allow sha256 hashes to be added to label or uploaded as a separate file.
* (ENHANCEMENT) Improved testing of SHA hash (downloading file and recalculating.
* (ENHANCEMENT) Added ability to recreate releases in order to update the tag/commitish associated with the release. Otherwise,releases can be updated but will always point to the same tag/commitish.
* (FIX) Fixed various bugs with SHA hashes, creating releases, deleting tags, and revamped upload error handling.

### 0.1.7

**Commit Delta**: [Change from 0.1.6 release](https://github.com/plus3it/watchmaker/compare/0.1.6...0.1.7)

**Released**: 2018.05.11

**Summary**:

* (FIX) Many bug fixes improving compatibility with Windows.
* (ENHANCEMENT) Use new GravityBee file (``gravitybee-files.json``).

### 0.1.6

**Commit Delta**: [Change from 0.1.5 release](https://github.com/plus3it/watchmaker/compare/0.1.5...0.1.6)

**Released**: 2018.05.10

**Summary**:

* (FIX) Wasn't deleting release asset if file given that didn't exist locally.
* (ENHANCEMENT) Added --force option to delete tags and releases using pattern matching.

### 0.1.5

**Commit Delta**: [Change from 0.1.4 release](https://github.com/plus3it/watchmaker/compare/0.1.4...0.1.5)

**Released**: 2018.05.10

**Summary**:

* (FIX) Implemented file (release asset) delete
* (ENHANCEMENT) Generally improved asset handling including SHA256 sums for files and better error handling

### 0.1.4

**Commit Delta**: [Change from 0.1.3 release](https://github.com/plus3it/watchmaker/compare/0.1.3...0.1.4)

**Released**: 2018.05.08

**Summary**:

* (FIX) Looked like an error was occuring because returning True instead of os.EX_OK.

### 0.1.3

**Commit Delta**: [Change from 0.1.2 release](https://github.com/plus3it/watchmaker/compare/0.1.2...0.1.3)

**Released**: 2018.05.07

**Summary**:

* (ENHANCEMENT) Added POSIX-style filename pattern matching for cleaning up tags.

### 0.1.2

**Commit Delta**: [Change from 0.1.1 release](https://github.com/plus3it/watchmaker/compare/0.1.1...0.1.2)

**Released**: 2018.05.07

**Summary**:

* Initial release!
