#!/usr/bin/python

import argparse
import yaml
import pwd
import grp
import os
import re

def etc_file_to_map(path, id_idx, name_idx):
    result = {}
    with open(path) as f:
        for line in f:
            fields = line.split(':')
            result[int(fields[id_idx])] = fields[name_idx]
    return result

class UGMError(Exception):
    pass

class UserGroupMapper:
    def __init__(self, user_map, group_map, user_transforms, group_transforms, ref_path):
        self.user_map = user_map
        self.group_map = group_map
        self.user_transforms = user_transforms
        self.group_transforms = group_transforms
        self.ref_path = ref_path

    @classmethod
    def create(cls,argp):
        user_map = etc_file_to_map(argp.user_map, 2, 0) if argp.user_map else {}
        group_map = etc_file_to_map(argp.group_map, 2, 0) if argp.group_map else {}
        transform_instrs = {'user': {}, 'group': {}}
        if argp.transform_instrs:
            with open(argp.transform_instrs) as f: transform_instrs = yaml.load(f)
        return UserGroupMapper(user_map, group_map, transform_instrs['user'], transform_instrs['group'], argp.ref_path)

    def run_transform(self,uid, gid, user, group, transform_instr):
        result = transform_instr
        if result == ':user':
            result = user
        elif ':' in str(transform_instr):
            raise "Bad transform instruction "+transform_instr
        return result

    def find_user_and_group(self, uid, gid):
        user = ':unknown'
        group = ':unknown'
        if uid in self.user_map:
            user = self.user_map[uid]
        elif uid in self.user_transforms:
            user = uid

        if gid in self.group_map:
            group = self.group_map[gid]
        elif gid in self.group_transforms:
            group = gid

        while user in self.user_transforms:
            user = self.run_transform(uid, gid, user, group, self.user_transforms[user])
        while group in self.group_transforms:
            group = self.run_transform(uid, gid, user, group, self.group_transforms[group])

        if ':' in str(group):
            group = gid
        if ':' in str(user):
            user = uid

        return user, group

    @classmethod
    def arg_parser(cls):
        argp = argparse.ArgumentParser()
        argp.add_argument('--user-map', action='store', help='User file in /etc/passwd format')
        argp.add_argument('--group-map', action='store', help='Group file in /etc/group format')
        argp.add_argument('--transform-instrs', action='store', help='File of transformations (to fix the fact that the same user had a different name on the other system).')
        argp.add_argument('--ref-path', action='store', help='Instead of the ownership on the target path, use the parallel file from this path instead')
        return argp

if __name__ == '__main__':
    argp = UserGroupMapper.arg_parser()
    argp.add_argument('--dir', action='store', required=True)
    argp.add_argument('--execute', action='store_true')
    args = argp.parse_args()
    ugm = UserGroupMapper.create(args)
    paths_mapped = set()
    unknown_users = set()
    unknown_groups = set()
    for curdir, subdirs, files in os.walk(args.dir):
        paths_to_process = [curdir]+[os.path.join(curdir,x) for x in subdirs+files if x not in paths_mapped]
        for path in paths_to_process:
            try:
                stat_path = path
                if ugm.ref_path:
                    stat_path = re.sub('^'+re.escape(args.dir), ugm.ref_path, path)
                stat = None
                try:
                    stat = os.lstat(stat_path)
                except OSError:
                    stat = os.lstat(path)
                user, group = ugm.find_user_and_group(stat.st_uid, stat.st_gid)
                uid = gid = None
                try:
                    if isinstance(user, int):
                        uid = user
                    else:
                        uid = pwd.getpwnam(user).pw_uid
                except KeyError as e:
                    unknown_users.add(user)
                    raise UGMError("Unknown user {} for {} ({!r})".format(user, path, e))
                try:
                    if isinstance(group, int):
                        gid = group
                    else:
                        gid = grp.getgrnam(group).gr_gid
                except KeyError as e:
                    unknown_groups.add(group)
                    raise UGMError("Unknown group {} for {} ({!r})".format(group, path, e))

                # Take the stat again in case there is refpath
                stat = os.lstat(path)
                if uid == stat.st_uid and gid == stat.st_gid:
                    print "No changes needed for "+path
                elif args.execute:
                    print "About to change ownership of {!s} to {!s}:{!s} ({!s}:{!s})".format(path, user, group, uid, gid)
                    os.lchown(path, uid, gid)
                    print "Changed ownership of {!s} to {!s}:{!s} ({!s}:{!s})".format(path, user, group, uid, gid)
                else:
                    print "Would change ownership of {!s} to {!s}:{!s} ({!s}:{!s})".format(path, user, group, uid, gid)
            except UGMError as e:
                print "ERROR while processing "+path+": ", e
                print "SKIPPED "+path
            paths_mapped.add(path)
    print "Done"
    if unknown_users:
        print "Unknown users found: {!r}".format(unknown_users)
    if unknown_groups:
        print "Unknown groups found: {!r}".format(unknown_groups)
