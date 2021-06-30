draw2d.shape.node.windows_server = draw2d.shape.node.linux.extend({
    NAME: "draw2d.shape.node.windows_server",
    INTERFACE_PREFIX: "nic ",
    VRAM: 8192,
    VCPU: 2,
    ICON_WIDTH: 50,
    ICON_HEIGHT: 50,
    INTERFACE_OFFSET: 0,
    MANAGEMENT_INTERFACE_PREFIX: "nic ",
    RESIZE_SUPPORT: false,
    ICON_FILE: "/static/images/windows_server.png",
    PORT_POSITION: "bottom",
});