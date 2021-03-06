# encoding: utf-8
#
# Copyright 2018 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#
from __future__ import absolute_import
from __future__ import division

from vdsm.common import xmlutils
from vdsm.virt.vmdevices import hwclass
from vdsm.virt.vmdevices import lookup

from testlib import VdsmTestCase
from testlib import expandPermutations, permutations


@expandPermutations
class TestLookup(VdsmTestCase):

    def setUp(self):
        self.drives = [
            FakeDrive(
                name='sda',
                serial='scsi0000',
                alias='ua-0000'
            ),
            FakeDrive(
                name='vdb',
                serial='virtio0000',
                alias='ua-2001'
            ),
        ]
        self.devices_conf = [
            {'alias': 'dimm0', 'type': hwclass.MEMORY, 'size': 1024},
            {'alias': 'ac97', 'type': hwclass.SOUND}
        ]

    def test_lookup_drive_by_name_found(self):
        drive = lookup.drive_by_name(self.drives, 'sda')
        assert drive is self.drives[0]

    def test_lookup_drive_by_name_missing(self):
        self.assertRaises(
            LookupError, lookup.drive_by_name, self.drives, 'hdd')

    def test_lookup_drive_by_serial_found(self):
        drive = lookup.drive_by_serial(self.drives, 'scsi0000')
        assert drive is self.drives[0]

    def test_lookup_drive_by_serial_missing(self):
        self.assertRaises(
            LookupError, lookup.drive_by_serial, self.drives, 'ide0002')

    def test_lookup_device_by_alias_found(self):
        device = lookup.device_by_alias(self.drives, 'ua-0000')
        assert device is self.drives[0]

    def test_lookup_device_by_alias_missing(self):
        self.assertRaises(
            LookupError, lookup.device_by_alias, self.drives, 'ua-UNKNOWN')

    @permutations([
        # drive_xml, dev_name - if None, we expect LookupError
        (u'''<disk device="disk" snapshot="no" type="file" />''', None),
        (u'''<disk device="disk" snapshot="no" type="file">
              <serial>virtio0000</serial>
            </disk>''', 'vdb'),
        # TODO: check it is valid for user aliases too
        (u'''<disk device="disk" snapshot="no" type="file">
              <alias name='ua-0000' />
            </disk>''', 'sda'),
        (u'''<disk device="disk" snapshot="no" type="file">
              <serial>virtio1111</serial>
              <alias name='ua-0000' />
            </disk>''', 'sda'),
    ])
    def test_lookup_drive_by_element(self, drive_xml, dev_name):
        # intentionally without serial and alias
        if dev_name is None:
            self.assertRaises(
                LookupError,
                lookup.drive_from_element,
                xmlutils.fromstring(drive_xml),
                self.drives
            )
        else:
            drive = lookup.drive_from_element(
                xmlutils.fromstring(drive_xml),
                self.drives
            )
            self.assertEqual(drive.name, dev_name)

    @permutations([
        [hwclass.MEMORY, 'dimm0', 0],
        [hwclass.SOUND, 'ac97', 1],
    ])
    def test_lookup_conf(self, dev_type, alias, index):
        conf = lookup.conf_by_alias(
            self.devices_conf, dev_type, alias)
        self.assertEqual(conf, self.devices_conf[index])

    @permutations([
        [hwclass.MEMORY, 'dimm1'],
        [hwclass.SOUND, 'dimm0'],
    ])
    def test_lookup_conf_error(self, dev_type, alias):
        self.assertRaises(LookupError,
                          lookup.conf_by_alias,
                          self.devices_conf, dev_type, alias)

    @permutations([
        # devices_conf
        [[]],
        [[{}]],
    ])
    def test_lookup_conf_missing(self, devices_conf):
        self.assertRaises(LookupError,
                          lookup.conf_by_alias,
                          devices_conf, hwclass.MEMORY, 'dimm0')


class FakeDrive(object):
    def __init__(self, name='vda', serial='0000', alias='ua-0'):
        self.name = name
        self.serial = serial
        self.alias = alias
