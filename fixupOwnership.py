#!/usr/bin/python

import argparse
import yaml

def etc_file_to_map(path, id_idx, name_idx):
    result = {}
    with open(path) as f:
        for line in f:
            fields = line.split(':')
            result[int(fields[id_idx])] = fields[name_idx]
    return result

class UserGroupMapper:
    def __init__(self, user_map, group_map, user_transforms, group_transforms):
        self.user_map = user_map
        self.group_map = group_map
        self.user_transforms = user_transforms
        self.group_transforms = group_transforms

    @classmethod
    def create(cls,argp):
        user_map = etc_file_to_map(argp.user_map, 2, 0)
        group_map = etc_file_to_map(argp.group_map, 2, 0)
        with open(argp.transform_instrs) as f: transform_instrs = yaml.load(f)
        return UserGroupMapper(user_map, group_map, transform_instrs['user'], transform_instrs['group'])

    def run_transform(self,uid, gid, user, group, transform_instr):
        result = transform_instr
        if result == ':user':
            result = user
        elif ':' in transform_instr:
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

        if ':' in group:
            raise Exception("Gid "+repr(gid)+" resolved to invalid group "+group)
        if ':' in user:
            raise Exception("Uid "+repr(uid)+" resolved to invalid user "+user)

        return user, group

    @classmethod
    def arg_parser(cls):
        argp = argparse.ArgumentParser()
        argp.add_argument('--user-map', action='store', help='User file in /etc/passwd format')
        argp.add_argument('--group-map', action='store', help='Group file in /etc/group format')
        argp.add_argument('--transform-instrs', action='store', help='File of transformations (to fix the fact that the same user had a different name on the other system).')
        return argp

if __name__ == '__main__':
    argp = arg_parser
    argp.add_argument('--dir', action='store', required=True)
    arp.parse_args()

