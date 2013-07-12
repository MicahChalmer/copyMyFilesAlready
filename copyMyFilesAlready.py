#!/usr/bin/python

import os
import shutil
import sys
import argparse
import subprocess

argp = argparse.ArgumentParser()
argp.add_argument('--from', action='store', dest='root_from', required=True)
argp.add_argument('--to', action='store', dest='root_to', required=True)
args = argp.parse_args()

root_from = args.root_from
root_to = args.root_to
print "Finishing copy from "+root_from+" to "+root_to

sys.stdout = os.fdopen(sys.stdout.fileno(),'w',0)

for dir, subdirs, files in os.walk(root_from):
    for sd in subdirs:
        newdir = os.path.join(dir,sd).replace(root_from,root_to)
        try:
            newdirstat = os.stat(newdir)
            print "Directory already exists: "+newdir
        except OSError:
            print "Creating directory "+newdir
            os.makedirs(newdir)

    for filename in files:
        fullpath = os.path.join(dir,filename)
        newpath = fullpath.replace(root_from,root_to)
        try:
            oldstat = os.stat(fullpath)
            should_copy = False;
            try:
                newstat = os.stat(newpath)
                should_copy = (newstat.st_size < oldstat.st_size)
                if newstat.st_size > oldstat.st_size:
                    print "HEY!  WTF?  "+newpath+" is bigger than "+fullpath
            except OSError:
                should_copy = True

            if should_copy:
                print "Copy "+fullpath + " to " + newpath + "(" + str(oldstat.st_size) + " bytes)"
                subprocess.call(['/bin/cp', '-a', '-f', fullpath,newpath], stderr=subprocess.STDOUT)
                print "Done copying "+fullpath+" to "+newpath
            else:
                print "Already copied, so skip: "+ fullpath
        except Exception, e:
            print "ERROR: "+str(e)+" while copying "+fullpath

print "All done!"
