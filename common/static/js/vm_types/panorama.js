draw2d.shape.node.panorama = draw2d.shape.node.linux.extend({
    NAME: "draw2d.shape.node.panorama",
    CLOUD_INIT_SUPPORT: false,
    RESIZE_SUPPORT: false,
    MANAGEMENT_INTERFACE_PREFIX: "management",
    MANAGEMENT_INTERFACE_INDEX: 0,
    INTERFACE_PREFIX: "ethernet0/",
    INTERFACE_OFFSET: 0,
    VCPU: 4,
    VRAM: 32768,
    ICON_WIDTH: 35,
    ICON_HEIGHT: 50,
    ICON_FILE: "/static/images/panorama.png",
    CONFIG_DRIVE_SUPPORT: false,
});