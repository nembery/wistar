#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
#
# Copyright (c) 2015 Juniper Networks, Inc.
# All rights reserved.
#
# Use is subject to license terms.
#
# Licensed under the Apache License, Version 2.0 (the ?License?); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import re

from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.config import Config
from lxml import etree

from exceptions import WistarException

logger = logging.getLogger(__name__)


def get_device_reference(host, user, pw):
    try:
        dev = Device(host=host, user=user, password=pw)
        dev.open(gather_facts=False)
        return dev
    except:
        logger.debug("Could not connect to device " + str(host) + "!")
        raise WistarException("Could not connect to Device")


def execute_cli(ip, user, pw, cli):
    try:
        dev = get_device_reference(ip, user, pw)
        return dev.cli(cli)
    except Exception as e:
        logger.debug("Could not execute cli command")
        logger.debug(str(e))
        return str(e)


def get_device_em_interface_macs(dev):
    em_dict = {}
    interfaces = dev.execute("<get-interface-information></get-interface-information>")
    for physicalInterface in interfaces:
        name_tag = physicalInterface.find(".//name")
        if name_tag is not None:
            name = name_tag.text.strip()
            if re.search("em", name):
                mac_tag = physicalInterface.find(".//current-physical-address")
                if mac_tag is not None:
                    mac = mac_tag.text.strip()
                    em_dict[name] = mac

    return em_dict


def set_all_interface_mac(dev, interfaces):
    xml_data = etree.Element("interfaces")
    for i in interfaces:
        interface_el = etree.SubElement(xml_data, "interface")
        name_el = etree.SubElement(interface_el, "name")
        name_el.text = i
        mac_el = etree.SubElement(interface_el, "mac")
        mac_el.text = interfaces[i]

    return push_config_element(xml_data, dev)


def get_interface_ip_config_element(name, ip):
    try:
        xml_data = etree.Element("interfaces")
        interface_el = etree.SubElement(xml_data, "interface")
        name_el = etree.SubElement(interface_el, "name")
        name_el.text = name
        unit_el = etree.SubElement(interface_el, "unit", attrib={"operation": "replace"})
        unit_name_el = etree.SubElement(unit_el, "name")
        unit_name_el.text = "0"
        family_el = etree.SubElement(unit_el, "family")
        inet_el = etree.SubElement(family_el, "inet")
        inet_address_el = etree.SubElement(inet_el, "address")
        inet_address_name_el = etree.SubElement(inet_address_el, "name")
        inet_address_name_el.text = ip
    except Exception as e:
        logger.debug("Error creating interfaceIpConfig element!")
        logger.debug(repr(e))
        raise WistarException("Could not create interface configuration")

    return xml_data


# netconf to box and set the address
def set_interface_ip_address(device_ip, pw, name, interface_ip):
    dev = get_device_reference(device_ip, "root", pw)
    xml_data = get_interface_ip_config_element(name, interface_ip)
    return push_config_element(xml_data, dev)


# log into each device, get the list of em interfaces
# create the corresponding ge-0/0/X interfaces
# only necessary for legacy phase 1 images
# then netconf in and configure them with appropriate mac appropriately
def config_junos_interfaces(ip, user, pw):
    interfaces = {}
    # FIXME - move un and pw to config object
    dev = get_device_reference(ip, user, pw)
    em_interfaces = get_device_em_interface_macs(dev)
    # we have the em interfaces with their macs
    # now, lets convert those to ge-0/0/X names ...
    for em in em_interfaces:
        if not em == "em0" and not em == "em1":
            logger.debug("em should not be em0 or em1")
            logger.debug(em)
            em_num = re.sub("\D", "", em)
            logger.debug(em_num)
            ge_num = int(em_num) - 2
            logger.debug(str(ge_num))
            ge = "ge-0/0/" + str(ge_num)
            # let's grab the mac here
            interfaces[ge] = em_interfaces[em]

    return set_all_interface_mac(dev, interfaces)


# push random config to the device
# let pyez figure out what format it is in
# used by configTemplates from user that can be in any format
def push_config(conf_string, ip, user, pw):
    dev = get_device_reference(ip, user, pw)

    # try to determine the format of our config_string
    config_format = 'set'
    if re.search(r'^\s*<.*>$', conf_string, re.MULTILINE):
        config_format = 'xml'
    elif re.search(r'^\s*(set|delete|replace|rename)\s', conf_string):
        config_format = 'set'
    elif re.search(r'^[a-z:]*\s*\w+\s+{', conf_string, re.I) and re.search(r'.*}\s*$', conf_string):
        config_format = 'text'

    logger.debug("using format: " + config_format)
    cu = Config(dev)
    try:
        cu.lock()
    except LockError as le:
        logger.debug("Could not lock database!")
        logger.debug(str(le))
        dev.close()
        return False

    try:
        cu.load(conf_string, format=config_format)
    except Exception as e:
        logger.debug("Could not load configuration")
        logger.debug(str(e))
        dev.close()
        return False

    diff = cu.diff()
    logger.debug(diff)
    if diff is not None:
        try:
            cu.commit_check()
            logger.debug("Committing config!")
            cu.commit(comment="Commit via wistar")

        except CommitError as ce:
            logger.debug("Could not load config!")
            cu.rollback()
            logger.debug(repr(ce))
            return False

    else:
        # nothing to commit
        logger.debug("Nothing to commit - no diff found")
        return True

    try:
        logger.debug("Unlocking database!")
        cu.unlock()
    except UnlockError as ue:
        logger.debug("Could not unlock database")
        logger.debug(str(ue))
        return False

    logger.debug("Closing device handle")
    dev.close()
    return True


def push_config_element(xml_data, dev, overwrite=False):
    logger.debug(etree.tostring(xml_data, pretty_print=True))
    cu = Config(dev)
    try:
        cu.lock()
    except LockError as le:
        logger.debug("Could not lock database!")
        logger.debug(str(le))
        dev.close()
        return False

    try:
        cu.load(xml_data, overwrite=overwrite)

    except Exception as e:
        logger.debug("Could not load configuration")
        logger.debug(str(e))
        dev.close()
        return False

    diff = cu.diff()
    logger.debug(diff)
    if diff is not None:
        # nothing to commit
        try:
            cu.commit_check()
            logger.debug("Committing config!")
            cu.commit(comment="Commit via wistar")
            logger.debug("Committed successfully!")

        except CommitError as ce:
            logger.debug("Could not load config!")
            cu.rollback()

    else:
        logger.debug("Nothing to commit")

    try:
        logger.debug("Unlocking database!")
        cu.unlock()
    except UnlockError as ue:
        logger.debug("Could not unlock database")
        logger.debug(str(ue))
        return False

    logger.debug("Closing device handle")
    dev.close()
    return True


def push_config_string(xml_string, ip, pw):
    logger.debug("Pushing new config to " + str(ip))
    logger.debug(xml_string)
    dev = get_device_reference(ip, "root", pw)
    xml_data = etree.fromstring(xml_string)
    push_config_element(xml_data, dev, True)


def get_config(ip, pw):
    dev = get_device_reference(ip, "root", pw)
    xml = dev.execute("<get-config><source><running/></source></get-config>")
    config_el = xml.find('configuration')
    return etree.tostring(config_el)
