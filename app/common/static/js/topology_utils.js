function setImageType() {
    let topoIconImageSelect = $('#topoIconImageSelect');
    let id = topoIconImageSelect.val().split(':')[0];
    type = topoIconImageSelect.val().split(':')[1];
    console.log("Setting image to " + id + " and type to " + type);
    $('#topoIconType').val(type);
    $('#topoIconImage').val(id);
    
    let addInstanceTbodyCloudInit = $('#addInstanceTbodyCloudInit');
    let addInstanceTbodyResize = $('#addInstanceTbodyResize');
    let addInstanceTbodyVFPC = $('#addInstanceTbodyVFPC');
    let addInstanceTbodySecondaryDisk = $('#addInstanceTbodySecondaryDisk'); 
    // by default, let's hide some things
    addInstanceTbodyCloudInit.css("display", "none");
    addInstanceTbodyResize.css("display", "none");
    addInstanceTbodyVFPC.css("display", "none");
    addInstanceTbodySecondaryDisk.css("display", "none");

    // let's also zero out a couple of optional params
    $('#topoIconScriptSelect').val('default_cloud_init.j2');
    $('#topoIconScriptParam').val(0);
    $('#topoIconResize').val(0);
    $('#newInstanceRoles').val('[]');
    $('#instanceNewRole').val('');
    $('#instanceRoles').empty();
    $('#floating_ip').prop('checked', false);

    for (let v = 0; v < vm_types.length; v++) {
        let vm_type = vm_types[v];
        if (vm_type.name === type) {

            let icon = eval("new " + vm_type.js + "()");

            console.log(icon);

            $('#topoIconCpu').val(icon.VCPU);
            $('#topoIconRam').val(icon.VRAM);

            // FIXME - we may actually never have a need for 'image' selectable types again!
            // just generate the disks images we need!
            if (icon.getSecondaryDiskParams() !== "") {
                let params = icon.getSecondaryDiskParams();
                type = params["type"];
                if (type === "image") {
                    let filter = params["filter"];
                    addInstanceTbodySecondaryDisk.css("display", "");
                    filterCompanionSelect(filter, "topoIconSecondaryDisk");
                }
            }

            if (icon.getTertiaryDiskParams() !== "") {
                let params = icon.getTertiaryDiskParams();
                let type = params["type"];
                if (type === "image") {
                    let filter = params["filter"];
                    $('#addInstanceTbodyTertiaryDisk').css("display", "");
                    filterCompanionSelect(filter, "topoIconTertiaryDisk");
                }
            }

            if (typeof icon.setChildId != "undefined") {
                addInstanceTbodyVFPC.css("display", "");
                filterCompanionSelect(icon.COMPANION_NAME_FILTER, "topoIconImageVFPCSelect");
            }

            if (icon.CLOUD_INIT_SUPPORT) {
                addInstanceTbodyCloudInit.css("display", "");
            }

            if (icon.RESIZE_SUPPORT) {
                addInstanceTbodyResize.css("display", "");
            }
        }
    }
}

function addIconAndClose() {
    let rv = addIcon();
    if (rv === true) {
        hideOverlay('#add_vm_form');
        hideOverlay('#overlayPanel');
    }
    // zero out all optional params as well, so they don't sneak in any other image types where they would
    // normally be hidden and zero anyway
    $('#topoIconScriptSelect').val(0);
    $('#topoIconScriptParam').val(0);
    $('#topoIconResize').val(0);
    $('#newInstanceRoles').val('[]');
    $('#instanceNewRole').val('');
    $('#instanceRoles').empty();

}

// add icon to the topology with the indicated values
function addIcon() {
    let ip = nextIp();

    if (ip === null) {
        return;
    }

    let topoIconName = $('#topoIconName');
    let user = $('#topoIconUser').val();
    let pw = $('#topoIconPass').val();
    let name = topoIconName.val();
    let type = $('#topoIconType').val();
    let image = $('#topoIconImage').val();
    let cpu = $('#topoIconCpu').val();
    let ram = $('#topoIconRam').val();
    //let iconData = $('#topoIconIcon').val();

    if (image === 0) {
        alert('Please select a valid image');
        return false;
    }

    let scriptId = $('#topoIconScriptSelect').val();
    if (scriptId === null) {
        scriptId = '';
    }
    let scriptParam = $('#topoIconScriptParam').val();
    let roles = $('#newInstanceRoles').val();

    let floating_ip = $('#floating_ip').prop('checked');

    let resize = $('#topoIconResize').val();

    let vpfe_image = $('#topoIconImageVFPCSelect').val();

    // enforce names always end with a digit
    // 11-23-19 - remove this!
    // let last = name.substr(-1);
    // let lastInt = parseInt(last);
    // if (isNaN(lastInt)) {
    //     alert('Name must end in a digit');
    //     $('#topoIconName').val(name + "1");
    //     $('#topoIconName').focus();
    //     return false;
    // }

    if (name === "") {
        alert("Please add a valid instance name");
        return false;
    }

    let icon;

    let vm_type_data = {};
    for (v = 0; v < vm_types.length; v++) {
        let vm_type = vm_types[v];
        if (vm_type.name === type) {
            vm_type_data = vm_type;
            break;
        }
    }
    console.log(vm_type_data);

    icon = eval("new " + vm_type_data.js + "()");

    // Should the user have selected a companion image?
    if (icon.getCompanionType() !== "") {
        // yes, did they?
        if (vpfe_image === 0) {
            // uh-oh!
            alert('Please select a Companion Image before continuing!');
            return false;
        }
    }

    // simple algorithm to add icons to the screen without overlapping
    lastX += 100;
    lastY += 0;
    vmxCount += 1;
    iconCount += 1;

    if (iconCount > iconWrapLimit) {
        lastX = 50;
        lastY = iconOffset;
        iconCount = 1;
        iconOffset += 110;
    }

    icon.setup(type, name, ip, user, pw, image);

    icon.setCpu(cpu);
    icon.setRam(ram);

    // set the resize value in userData dict
    icon.setUserDataKey('resize', resize);

    icon.setUserDataKey('floating_ip', floating_ip);

    // set the scriptId in the
    if (scriptId !== 0) {
        icon.setUserDataKey('configScriptId', scriptId);
        icon.setUserDataKey('configScriptParam', scriptParam);
    }

    if (roles !== '[]') {
        icon.setUserDataKey('roles', JSON.parse(roles));
        $('#newInstanceRoles').val('[]');
        $('#instanceNewRole').val('');
        $('#instanceRoles').empty();
    }

    if (icon.getSecondaryDiskParams() !== "") {
        let params = icon.getSecondaryDiskParams();
        let type = params["type"];
        if (type === "image") {
            params["image_id"] = $('#topoIconSecondaryDisk').val();
            icon.setSecondaryDiskParams(params);
        }
    }

    if (icon.getCompanionType() !== "") {

        let vpfe_cpu = $('#topoIconVFPCCpu').val();
        let vpfe_ram = $('#topoIconVFPCRam').val();
        let vpfe_js = $('#topoIconVFPCJs').val();
        let vpfe_type = $('#topoIconVFPCType').val();

        // attempt to load vpfe as the selected image_id type
        // otherwise, use the default companion_type
        if (vpfe_js === '') {
            vpfe_js = icon.COMPANION_TYPE;
        }

        let vpfe = eval("new " + vpfe_js + "()");

        let vpfe_ip = nextIp();

        vpfe.setup(vpfe_type, name, vpfe_ip, user, pw, vpfe_image);

        vpfe.setCpu(vpfe_cpu);
        vpfe.setRam(vpfe_ram);
        // bind them together here!

        if (typeof vpfe.setParentId != 'undefined') {
            console.log("vpfe is actually a child!");
            console.log(vpfe.NAME);
            vpfe.setParentId(icon.getId());
            icon.setChildId(vpfe.getId());

            canvas.add(vpfe, lastX, lastY + 15);
        } else {
            alert("Companion Doesn't appear to be a valid companion image type!");
            return false;
        }

        canvas.add(icon, lastX, lastY);

        let figures = new draw2d.util.ArrayList([icon, vpfe]);
        let cg = new draw2d.command.CommandGroup(canvas, figures);
        cg.execute();

        // work around, ports are being drawn as hidden until they are clicked!
        vpfe.getPorts().first().toFront();

    } else {
        canvas.add(icon, lastX, lastY);
    }

    // let's try to increment everything nicely
    topoIconName.val(incrementIconName(name));

    return true;
}


var ip_floor = 2;
var dhcp_floor = ip_floor;

// convenience func to increment icon name if it happens to end
// in a digit
function incrementIconName(name) {
    let last = name.substr(-1);
    let lastInt = parseInt(last);

    if (isNaN(lastInt)) {
        return name + '-01';
    }

    if (last === "9") {
        let lastTwo = name.substr(-2);
        let lastTwoInt = parseInt(lastTwo);
        if (!isNaN(lastTwoInt)) {
            return name.substring(0, name.length - 2) + (lastTwoInt + 1);
        } else {
            // last two are not an int, check for single digit suffix
            if (!isNaN(lastInt)) {
                return name.substring(0, name.length - 1) + (lastInt + 1);
            } else {
                return name + "2";
            }
        }
    } else {
        if (!isNaN(lastInt)) {
            return name.substring(0, name.length - 1) + (lastInt + 1);
        } else {
            return name + "2";
        }
    }
}

function addLabel() {

    let label = $('#newLabel').val();
    let labelSize = $('#newLabelFontSize').val();
    let l = new draw2d.shape.basic.Label({text: label});
    // l.setBackgroundColor();
    l.setFontColor("#000000");
    l.setFontSize(labelSize);
    l.setStroke(0);

    // simple algorithm to add icons to the screen without overlapping
    lastX += 100;
    lastY += 0;
    iconCount += 1;

    if (iconCount > iconWrapLimit) {
        lastX = 50;
        lastY = iconOffset;
        iconCount = 1;
        iconOffset += 110;
    }
    canvas.add(l, lastX, lastY);
    hideOverlay("#add_label_form");
}

function filterCompanionSelect(filter_string, select_name) {
    let filter_regex = RegExp(filter_string, 'i');
    let companion_select = $('#' + select_name);
    companion_select.empty();
    companion_select.append('<option value="0">None</option>');
    for (index in images) {
        let image_name = images[index]["fields"]["name"];
        let image_id = images[index]["pk"];
        if (image_name.match(filter_regex)) {
            companion_select.append('<option value="' + image_id + '">' + image_name + '</option>');
        }
    }
}

function setCompanionParams(o) {
    let companion_image = $('#topoIconImageVFPCSelect').val();
    console.log(companion_image);
    let companion_type = "blank";
    for (i = 0; i < images.length; i++) {

        if (images[i]["pk"] === companion_image) {
            companion_type = images[i]["fields"]["type"];
            console.log(companion_type);
            break;
        }
    }
    // set the companion type here to be used later
    $('#topoIconVFPCType').val(companion_type);

    for (let v = 0; v < vm_types.length; v++) {
        let vm_type = vm_types[v];
        console.log(vm_type.name);
        if (vm_type.name === companion_type) {
            console.log('found it');
            let companion = eval("new " + vm_type.js + "()");

            $('#topoIconVFPCCpu').val(companion.VCPU);
            $('#topoIconVFPCRam').val(companion.VRAM);
            $('#topoIconVFPCJs').val(companion.NAME);

            break;
        }
    }
}

function loadInstanceDetails() {

    let doc = $(document);
    doc.css('cursor', 'progress');

    let figureId = $('#selectedObject').val();
    let figure = canvas.getFigure(figureId);

    let domainName = generateDomainNameFromLabel(figure.getLabel());

    let cso = $('<div/>').attr("id", "overlay").addClass("screen-overlay");

    $('#content').append(cso);

    let url = '/ajax/instanceDetails/';
    let params = {
        'domainName': domainName,
        'csrfmiddlewaretoken': window.csrf_token
    };
    let post = $.post(url, params, function (response) {
        let content = $(response);
        cso.append(content);
    });
    post.fail(function () {
        alert('Could not perform request!');
    });
    post.always(function () {
        doc.css('cursor', '');
    });
}

function addNewInstanceRole() {
    let instance_role = $('#instanceNewRole');
    let r = instance_role.val();
    if (r === '') {
        console.log('no role to set');
        return;
    }
    let instance_saved_roles = $('#newInstanceRoles');
    let roles_string = instance_saved_roles.val();
    let roles = JSON.parse(roles_string);

    if (!$.isArray(roles)) {
        roles = [];
    }
    roles.push(r);

    instance_saved_roles.val(JSON.stringify(roles));

    $('#instanceRoles').append("<li>" + r + "</li>");
    instance_role.val('');
}

function clearNewInstanceRoles() {
    $('#newInstanceRoles').val('[]');
    $('#instanceRoles').empty();
}

    function addInstanceForm() {
        let doc = $(document.documentElement);
        doc.css('cursor', 'progress');

        let url = '/topologies/addInstanceForm/';

        let post = $.get(url, function (response) {
            let content = $(response);
            $('#overlayPanel').empty().append(content);
            showOverlay('#overlayPanel');
        });
        post.fail(function () {
            alert('Could not perform request!');
        });
        post.always(function () {
            doc.css('cursor', '');
        });
    }