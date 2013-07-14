#!/usr/bin/python

import unittest
from fixupOwnership import UserGroupMapper
import os


class UserGroupMapperTest(unittest.TestCase):

    def setUp(self):
        argp = UserGroupMapper.arg_parser()
        args = argp.parse_args(['--user-map', os.path.join(os.path.dirname(__file__),'test_fixtures/fixupOwnership/users'),
                         '--group-map', os.path.join(os.path.dirname(__file__),'test_fixtures/fixupOwnership/groups'),
                         '--transform-instrs', os.path.join(os.path.dirname(__file__),'test_fixtures/fixupOwnership/transforms')])
        self.ugm = UserGroupMapper.create(args)

    def test_straight_mappings(self):
        self.assertEqual(self.ugm.find_user_and_group(1000, 1000), ('alice', 'alice'))
        self.assertEqual(self.ugm.find_user_and_group(1001, 1002), ('charlie', 'charlie'))

    def test_name_transform(self):
        self.assertEqual(self.ugm.find_user_and_group(1003, 1003), ('charlie', 'lewis'))  # We didn't put a group transform for "lewis", only a user one

    def test_unknown_transform(self):
        self.assertEqual(self.ugm.find_user_and_group(9999, 1002), ('alice', 'charlie')) # Unknown is mapped to Alice

    def test_transform_to_curr_user(self):
        self.assertEqual(self.ugm.find_user_and_group(9999, 200), ('alice', 'alice')) # Unknown is mapped to Alice, staff is mapped to user

if __name__ == '__main__':
    unittest.main()
