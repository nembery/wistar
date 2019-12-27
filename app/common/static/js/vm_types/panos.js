draw2d.shape.node.panos = draw2d.shape.node.linux.extend({
    NAME: "draw2d.shape.node.panos",
    CLOUD_INIT_SUPPORT: false,
    RESIZE_SUPPORT: false,
    MANAGEMENT_INTERFACE_PREFIX: "management",
    MANAGEMENT_INTERFACE_INDEX: 0,
    INTERFACE_PREFIX: "ethernet0/",
    INTERFACE_OFFSET: 0,
    VCPU: 2,
    VRAM: 8192,
    ICON_WIDTH: 50,
    ICON_HEIGHT: 50,
    ICON_FILE: "/static/images/panos.png",
    CONFIG_DRIVE_SUPPORT: true,
    CONFIG_DRIVE_PARAMS: [
        {
            "template": "panos_init_cfg.j2",
            "destination": "/config/init-cfg.txt"
        },
        {
            "template": "blank.j2",
            "destination": "/software/.ignore"
        },
        {
            "template": "blank.j2",
            "destination": "/content/.ignore"
        },
        {
            "template": "blank.j2",
            "destination": "/license/.ignore"
        },
    ]
});


