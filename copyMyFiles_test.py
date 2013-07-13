#!/usr/bin/python

import unittest
import tempfile
import shutil
import os
import subprocess
import stat
import re
from datetime import datetime

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'test_fixtures')

class CopyFilesTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        self.active_fixture = None

    def call_copy_script(self, fixturepath):
        full_fixturepath = os.path.join(FIXTURE_PATH, fixturepath)
        full_destpath = os.path.join(self.tmpdir, fixturepath)
        log_name = os.path.join(self.tmpdir, fixturepath+".log-"+datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f'))
        with open(log_name, 'w') as log_file:
            subprocess.call([os.path.join(os.path.dirname(__file__), 'copyMyFilesAlready.py'),
                             '--from', full_fixturepath, '--to', full_destpath], stdout=log_file, stderr=subprocess.STDOUT)
        self.active_fixture = fixturepath
        return full_fixturepath, log_name

    def active_fixture_path(self):
        return os.path.join(FIXTURE_PATH, self.active_fixture)

    def active_tempdir_path(self):
        return os.path.join(self.tmpdir, self.active_fixture)

    # This asserts that the contents and metadata of the destination file is equal to its counterpart in the source
    def check_file(self, filepath):
        srcpath = os.path.join(self.active_fixture_path(), filepath)
        destpath = os.path.join(self.active_tempdir_path(), filepath)
        srcstat = os.lstat(srcpath)
        deststat = os.lstat(destpath)
        self.assertEqual(deststat.st_mode, srcstat.st_mode, "File mode is the same for "+filepath)
        self.assertEqual(deststat.st_mtime, srcstat.st_mtime, "File mtime is the same for "+filepath)
        if stat.S_ISLNK(deststat.st_mode):
            self.assertEqual(os.readlink(destpath), os.readlink(srcpath))
        else:
            with open(srcpath) as srcfile, open(destpath) as destfile:
                self.assertEqual(destfile.read(), srcfile.read(),
                                 "File contents are the same for "+filepath)

    def check_files_included(self):
        for curdir, subdirs, files in os.walk(self.active_fixture_path()):
            dest_dir = re.sub(r"^"+re.escape(self.active_fixture_path()), self.active_tempdir_path(), curdir)
            base_dir = re.sub(r"^"+re.escape(self.active_fixture_path())+"/?", '', curdir)
            for sd in subdirs:
                if stat.S_ISLNK(os.lstat(os.path.join(curdir, sd)).st_mode):
                    self.check_file(os.path.join(base_dir, sd))
            for fl in files:
                self.check_file(os.path.join(base_dir, fl))

        # Check that there are no extra files in the destination
        for curdir, subdirs, files in os.walk(self.active_tempdir_path()):
            src_dir = re.sub(r"^"+re.escape(self.active_tempdir_path()), self.active_fixture_path(), curdir)
            for fl in subdirs + files:
                self.assertTrue(os.path.lexists(os.path.join(src_dir, fl)), "File in dest dir must exist in source: "+os.path.join(curdir, fl) + " -> "+os.path.join(src_dir, fl))

    def test_simple_to_empty(self):
        copied_dir, log = self.call_copy_script('test1')
        self.check_files_included()

    def test_some_files_exist(self):
        copied_dir, log = self.call_copy_script('test1')
        os.remove(os.path.join(self.active_tempdir_path(), 'normal_file'))
        copied_dir, log2 = self.call_copy_script('test1')
        self.check_files_included()
        with open(log2) as log_file:
            log_contents = log_file.read()
            self.assertRegexpMatches(log_contents,
                                     re.compile(r"^Directory already exists: "
                                                +re.escape(os.path.join(self.active_tempdir_path(),"normal_subdir")), re.M))
            self.assertRegexpMatches(log_contents,
                                     re.compile(r"^Copy "+re.escape(os.path.join(self.active_fixture_path(), "normal_file"))
                                                +" to "+
                                                re.escape(os.path.join(self.active_tempdir_path(), "normal_file")), re.M))

    # Should copy the normal file again when it's smaller than the source
    def test_dest_file_is_smaller(self):
        copied_dir, log = self.call_copy_script('test1')
        with open(os.path.join(self.active_tempdir_path(),'normal_file'), 'w') as nf:
            nf.write("small\n")
        copied_dir, log2 = self.call_copy_script('test1')
        self.check_files_included()
        with open(log2) as log_file:
            log_contents = log_file.read()
            self.assertRegexpMatches(log_contents,
                                     re.compile(r"^Copy "+re.escape(os.path.join(self.active_fixture_path(), "normal_file"))
                                                +" to "+
                                                re.escape(os.path.join(self.active_tempdir_path(), "normal_file")), re.M))

    # Should copy the normal file again when it's smaller than the source
    def test_dest_file_is_bigger(self):
        copied_dir, log = self.call_copy_script('test1')
        nf_path = os.path.join(self.active_tempdir_path(),'normal_file')
        big_contents = "this is bigger than the normal contents!  watch out!\n"
        with open(nf_path, 'w') as nf:
            nf.write(big_contents)
        copied_dir, log2 = self.call_copy_script('test1')
        self.check_file('another_normal_file')
        with open(nf_path) as nfl: self.assertEqual(nfl.read(), big_contents)
        with open(log2) as log_file:
            log_contents = log_file.read()
            self.assertRegexpMatches(log_contents,
                                     re.compile(r"^HEY!  WTF\?  "+re.escape(os.path.join(self.active_tempdir_path(), "normal_file"))
                                                +" is bigger than "+
                                                re.escape(os.path.join(self.active_fixture_path(), "normal_file")), re.M))

if __name__ == '__main__':
    unittest.main()
