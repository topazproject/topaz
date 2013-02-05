Stuff to do before public launch
================================

* Move to new github org
  * Make sure travis picks up the change
* Public mailing list
  * Check with Armin if librelist is good enough, otherwise google groups
* Binaries (with nightly builds preferably)
  * Build release script exists, either put OS X and Linux builds on S3
    manually or write a web app to post/display them.
  * Make the LOAD_PATH relative to run location, fallback to compile location
* Remove source key from .travis.yml
* Put docs on readthedocs
