"""TV Pack parse"""
import xml.etree.ElementTree as ET


def parse():
    tree = ET.parse('TV_Pack.xml')
    root = tree.findall('channel')
    channels = {}

    for child in root:
        channel_name = child.find('display-name').text
        channel_id = child.attrib['id']
        channels.update({channel_name: channel_id})

    return channels


channels = parse()
