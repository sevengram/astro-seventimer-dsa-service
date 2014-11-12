#! /usr/bin/env python2
# -*- coding:utf8 -*-

import unittest
import sys
sys.path.append('..')

from util import config
from util import document

class DeepskyObjectTestCase(unittest.TestCase):
    def setUp(self):
        raw_data = '01|CEP|planetary nebula|00119.4;AnotherName|18.0| |0.8|0.5|00h  12m54.6s|- 9 10\' 23"|008'
        self.settings = config.Settings('config')
        self.item = document.DeepskyObject(raw_data, self.settings)

    def tearDown(self):
        pass

    def testClean(self):
        self.item.fix_value()
        self.item.clean()
        self.assertFalse(self.item.has('ura2'))
        self.assertFalse(self.item.has('size_max'))
        self.assertFalse(self.item.has('brstr'))

    def testFixName(self):
        self.item.fix_name()
        self.assertEqual(self.item.get('object'), 'Abell1')

    def testFixAlias(self):
        self.item.fix_alias()
        self.assertEqual(self.item.get('alias'), ['Abell119.4','AnotherName'])

    def testFixAlias(self):
        self.item.fix_alias()
        self.assertEqual(self.item.get('alias'), ['Abell119.4','AnotherName'])

    def testFixValue(self):
        self.item.fix_value()
        self.item.fix_type()
        self.assertAlmostEqual(self.item.get('mag'), 18.0)
        self.assertAlmostEqual(self.item.get('brstr'), 99.9)
        self.assertEqual(self.item.get('type'), 'PLNNB')

    def testUpdateSize(self):
        self.item.update_size()
        self.assertEqual(self.item.get('size'),'0.8mx0.5m')

    def testUpdateRaDec(self):
        self.item.update_ra_dec()
        self.assertEqual(self.item.get('ra'),'00 12 54.6')
        self.assertEqual(self.item.get('dec'),'-09 10 23')
        self.assertAlmostEqual(self.item.get('ra_value'),12.0/60.0+54.6/3600.0)
        self.assertAlmostEqual(self.item.get('dec_value'),-9-10.0/60.0-23.0/3600.0)

# class DeepskyObjectTestSuite(unittest.TestSuite):
#     def __init__(self):
#         super(DeepskyObjectTestSuite, self).__init__(
#             map(DeepskyObjectTestCase,('testInit','testUpdateRaDec')))

if __name__ == "__main__":
    unittest.main()
    # unittest.TextTestRunner().run(DeepskyObjectTestSuite())
