#!/usr/bin/python

import os
import shutil
import sys
import argparse
import subprocess
import stat

def copy_file(src_path, dest_path):
    print "Copy "+src_path + " to " + dest_path + "(" + str(os.lstat(src_path).st_size) + " bytes)"
    subprocess.call(['/bin/cp', '-a', '-f', src_path, dest_path], stderr=subprocess.STDOUT)
    print "Done copying "+src_path+" to "+dest_path


argp = argparse.ArgumentParser()
argp.add_argument('--from', action='store', dest='root_from', required=True)
argp.add_argument('--to', action='store', dest='root_to', required=True)
args = argp.parse_args()

root_from = args.root_from
root_to = args.root_to
print "Copy from "+root_from+" to "+root_to

sys.stdout = os.fdopen(sys.stdout.fileno(),'w',0)

for curdir, subdirs, files in os.walk(root_from):
    for sd in subdirs:
        fulldir = os.path.join(curdir,sd)
        dirstat = os.lstat(fulldir)
        newdir = fulldir.replace(root_from,root_to)
        # os.walk puts symlinks to directories in subdirs instead of files, even with followlinks set to False (the default).  Handle them by copying.
        if stat.S_ISLNK(dirstat.st_mode) and not os.path.lexists(newdir):
            copy_file(fulldir,newdir)
        else:
            try:
                newdirstat = os.lstat(newdir)
                if stat.S_ISLNK(newdirstat.st_mode) and not stat.S_ISLNK(dirstat.st_mode):
                    print "HEY!  WTF?  "+fulldir+" is a symlink, but "+newdir+" is not!"
                print "Directory already exists: "+newdir
            except OSError:
                print "Creating directory "+newdir
                os.makedirs(newdir)

    for filename in files:
        fullpath = os.path.join(curdir,filename)
        newpath = fullpath.replace(root_from,root_to)
        try:
            oldstat = os.lstat(fullpath)
            should_copy = False;
            try:
                newstat = os.lstat(newpath)
                should_copy = (newstat.st_size < oldstat.st_size)
                if newstat.st_size > oldstat.st_size:
                    print "HEY!  WTF?  "+newpath+" is bigger than "+fullpath
            except OSError:
                should_copy = True

            if should_copy:
                copy_file(fullpath,newpath)
            else:
                print "Already copied, so skip: "+ fullpath
        except Exception, e:
            print "ERROR: "+str(e)+" while copying "+fullpath

print "All done!"
