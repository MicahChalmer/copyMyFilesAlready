This repo contains some utilities I wrote for myself when trying to copy data out of old hard disks.  It has been tested exactly once, on one system (Ubuntu 13.04).  It has:

  * `copyMyFilesAlready.py`: like "`cp -r`" but skips over files that look like they've been copied already.  Used because linux HFS file system drivers were prone to crashing and couldn't get through copying the whole thing.  This had enough edge cases that I actually added some tests for it in `copyMyFiles_test.py`.  Yeesh.

  Usage: copyMyFilesAlready.py --from SOURCE --to DEST

  This will copy everything, trying to preserve permissions.  If the @#^$@ system crashes in the middle, just start it again and it'll at least skip over the files it already copied.  It considers a file already copied if it exists in the destination and is as big or bigger than the file in source.  If the dest is bigger it'll warn.  If the dest is smaller it'll just copy again.
