# reduced list by default. Rename the vm_definitions_all.py to vm_defnintions.py to enable all known vm_types
vm_image_types = [
    {
        "name": "blank",
        "description": "Blank",
        "js": "draw2d.shape.node.generic",
    },
    {
        "name": "linux",
        "description": "Linux",
        "js": "draw2d.shape.node.linux",
    },
    {
        "name": "ubuntu16",
        "description": "Ubuntu 16",
        "js": "draw2d.shape.node.ubuntu16",
    },
    {
        "name": "ubuntu18",
        "description": "Ubuntu 18",
        "js": "draw2d.shape.node.ubuntu18",
    },
    {
        "name": "junos_vre_15",
        "description": "Junos vMX RE 15.x",
        "js": "draw2d.shape.node.vre_15",
    },
    {
        "name": "junos_riot",
        "description": "Junos vMX RIOT",
        "js": "draw2d.shape.node.vriot",
    },
    {
        "name": "generic",
        "description": "Other",
        "js": "draw2d.shape.node.generic",
    },
    {
        "name": "panos",
        "description": "PAN-OS VM-Series",
        "js": "draw2d.shape.node.panos",
    },
    {
        "name": "panorama",
        "description": "PAN-OS Panorama",
        "js": "draw2d.shape.node.panorama",
    },
    {
        "name": "windows10",
        "description": "Windows 10",
        "js": "draw2d.shape.node.windows10",
    }
]
