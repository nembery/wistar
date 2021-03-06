import json
import logging
import os
import random
import time
import traceback

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string

from common.lib import consoleUtils
from common.lib import libvirtUtils
from common.lib import openstackUtils
from common.lib import osUtils
from common.lib import ovsUtils
from common.lib import wistarUtils
from common.lib.exceptions import WistarException
from images.models import Image
from scripts.models import ConfigTemplate
from scripts.models import Script
from topologies.models import Topology
from wistar import configuration

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponseRedirect('/topologies/')


def manage_hypervisor(request):
    return render(request, 'ajax/manageHypervisor.html')


def instance_details(request):
    required_fields = set(['domainName'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    try:
        if configuration.deployment_backend == "kvm":
            domain_name = request.POST['domainName']
            domain = libvirtUtils.get_domain_by_name(domain_name)
            domain_details = libvirtUtils.get_domain_dict(domain_name)
            vnc_port = libvirtUtils.get_domain_vnc_port(domain)
            return render(request, 'ajax/instanceDetails.html', {'d': domain_details, 'vnc_port': vnc_port})
        elif configuration.deployment_backend == "openstack":
            return render(request, 'ajax/instanceDetails.html', {'d': {}, 'vnc_port': 6000})

    except Exception as e:
        print(e)
        return render(request, 'ajax/ajaxError.html', {'error': e})


def view_domain(request, domain_id):
    try:
        domain = libvirtUtils.get_domain_by_uuid(domain_id)
        return render(request, 'ajax/viewDomain.html', {'domain': domain, 'xml': domain.XMLDesc(0)})
    except Exception as e:
        return render(request, 'ajax/ajaxError.html', {'error': e})


def view_network(request, network_name):
    try:
        network = libvirtUtils.get_network_by_name(network_name)
        return render(request, 'ajax/viewNetwork.html', {'network': network, 'xml': network.XMLDesc(0)})
    except Exception as e:
        return render(request, 'ajax/ajaxError.html', {'error': e})


def preconfig_junos_domain(request):
    response_data = {"result": True, "message": "success"}
    required_fields = set(['domain', 'user', 'password', 'ip', 'mgmtInterface'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    domain = request.POST['domain']
    user = request.POST["user"]
    password = request.POST['password']
    ip = request.POST['ip']
    mgmt_interface = request.POST['mgmtInterface']

    logger.debug("Configuring domain:" + str(domain))
    try:

        # let's see if we need to kill any webConsole sessions first
        wc_dict = request.session.get("webConsoleDict")
        if wc_dict is not None:
            if domain in wc_dict:
                wc_config = wc_dict[domain]
                wc_port = wc_config["wsPort"]
                server = request.get_host().split(":")[0]
                wistarUtils.kill_web_socket(server, wc_port)

        # FIXME - there is a bug somewhere that this can be blank ?
        if mgmt_interface == "":
            mgmt_interface = "em0"
        elif mgmt_interface == "em0":
            if not osUtils.check_is_linux():
                mgmt_interface = "fxp0"

        if user != "root":
            response_data["result"] = False
            response_data["message"] = "Junos preconfiguration user must be root!"
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        if consoleUtils.preconfig_junos_domain(domain, user, password, ip, mgmt_interface):
            response_data["result"] = True
            response_data["message"] = "Success"
        else:
            response_data["result"] = False
            response_data["message"] = "Could not configure domain"
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except WistarException as we:
        logger.debug(we)
        response_data["result"] = False
        response_data["message"] = str(we)
        return HttpResponse(json.dumps(response_data), content_type="application/json")


def preconfig_linux_domain(request):
    response_data = {"result": True}
    required_fields = set(['domain', 'hostname', 'user', 'password', 'ip', 'mgmtInterface'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    domain = request.POST['domain']
    user = request.POST["user"]
    password = request.POST['password']
    ip = request.POST['ip']
    mgmt_interface = request.POST['mgmtInterface']
    hostname = request.POST['hostname']

    logger.debug("Configuring linux domain:" + str(domain))
    try:
        response_data["result"] = consoleUtils.preconfig_linux_domain(domain, hostname, user, password, ip,
                                                                      mgmt_interface)
        logger.debug(str(response_data))
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except WistarException as we:
        logger.debug(we)
        response_data["result"] = False
        response_data["message"] = str(we)
        return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_junos_startup_state(request):
    response_data = dict()
    response_data["console"] = False
    response_data["power"] = False
    response_data["network"] = False

    if not configuration.check_vm_network_state:
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    required_fields = set(['name'])
    if not required_fields.issubset(request.POST):
        logger.error('Invalid parameters in POST for get_junos_startup_state')
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    name = request.POST['name']

    # always check network if possible regardless of deployment_backend
    if "ip" in request.POST:
        # this instance is auto-configured, so we can just check for IP here
        response_data["network"] = osUtils.check_ip(request.POST["ip"])

    if configuration.deployment_backend == "kvm" and libvirtUtils.is_domain_running(name):
        # topologies/edit will fire multiple calls at once
        # let's just put a bit of a breather between each one
        response_data["power"] = True
        if "ip" not in request.POST:
            time.sleep(random.randint(0, 10) * .10)
            response_data["console"] = consoleUtils.is_junos_device_at_prompt(name)

    elif configuration.deployment_backend == "openstack":

        time.sleep(random.randint(0, 20) * .10)
        response_data["power"] = True
        # console no longer supported in openstack deployments
        response_data["console"] = False

    return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_linux_startup_state(request):
    response_data = dict()
    response_data["console"] = False
    response_data["power"] = False
    response_data["network"] = False

    if not configuration.check_vm_network_state:
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    required_fields = set(['name'])
    if not required_fields.issubset(request.POST):
        logger.error('Invalid parameters in POST for get_linux_startup_state')
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    name = request.POST['name']
    # always check network if possible regardless of deployment_backend
    if "ip" in request.POST:
        # this instance is auto-configured, so we can just check for IP here
        response_data["network"] = osUtils.check_ip(request.POST["ip"])

    if configuration.deployment_backend == "openstack":
        if openstackUtils.connect_to_openstack():
            time.sleep(random.randint(0, 10) * .10)
            response_data["power"] = True
            # as of 2018-01-01 we no longer support openstack console, this is dead code
            # response_data["console"] = consoleUtils.is_linux_device_at_prompt(name)
            response_data['console'] = False
    else:
        if libvirtUtils.is_domain_running(name):
            time.sleep(random.randint(0, 10) * .10)
            response_data["power"] = True
            # let's check the console only if we do not have network available to check
            if "ip" not in request.POST:
                response_data["console"] = consoleUtils.is_linux_device_at_prompt(name)

    return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_config_templates(request):
    required_fields = set(['ip'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    template_list = ConfigTemplate.objects.all().order_by('modified')

    ip = request.POST['ip']
    context = {'template_list': template_list, 'ip': ip}
    return render(request, 'ajax/configTemplates.html', context)


def get_scripts(request):
    required_fields = set(['ip'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    script_list = Script.objects.all().order_by('modified')

    ip = request.POST['ip']
    context = {'script_list': script_list, 'ip': ip}
    return render(request, 'ajax/scripts.html', context)


def start_topology(request):
    required_fields = set(['topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    topology_id = request.POST['topologyId']

    delay_str = request.POST.get('delay', '180')

    try:
        delay = int(delay_str)
    except ValueError:
        delay = 180

    if topology_id == "":
        logger.debug("Found a blank topoId!")
        return render(request, 'ajax/ajaxError.html', {'error': "Blank Topology Id found"})

    domain_list = libvirtUtils.get_domains_for_topology("t" + topology_id + "_")
    network_list = []

    if configuration.deployment_backend == "kvm":
        network_list = libvirtUtils.get_networks_for_topology("t" + topology_id + "_")

    for network in network_list:
        logger.debug("Starting network: " + network["name"])
        if libvirtUtils.start_network(network["name"]):
            time.sleep(1)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not start network: " + network["name"]})

    num_domains = len(domain_list)
    iter_counter = 1
    for domain in domain_list:
        logger.debug("Starting domain " + domain["name"])
        if libvirtUtils.is_domain_running(domain["name"]):
            # skip already started domains
            logger.debug("domain %s is already started" % domain["name"])
            iter_counter += 1
            continue

        if libvirtUtils.start_domain(domain["uuid"]):
            # let's not sleep after the last domain has been started
            if iter_counter < num_domains:
                time.sleep(delay)
            iter_counter += 1
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not start domain: " + domain["name"]})

    logger.debug("All domains started")
    return refresh_deployment_status(request)


def pause_topology(request):
    required_fields = set(['topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    topology_id = request.POST['topologyId']

    if topology_id == "":
        logger.debug("Found a blank topoId!")
        return render(request, 'ajax/ajaxError.html', {'error': "Blank Topology Id found"})

    domain_list = libvirtUtils.get_domains_for_topology("t" + topology_id + "_")

    for domain in domain_list:
        if domain["state"] == "running":
            logger.debug("Pausing domain " + domain["name"])
            libvirtUtils.suspend_domain(domain["uuid"])
            time.sleep(5)
        else:
            logger.debug("Domain %s is already shut down" % domain["name"])

    network_list = []
    if osUtils.check_is_linux():
        network_list = libvirtUtils.get_networks_for_topology("t" + topology_id + "_")

    for network in network_list:
        logger.debug("Stopping network: " + network["name"])
        if libvirtUtils.stop_network(network["name"]):
            time.sleep(1)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not stop network: " + network["name"]})

    logger.debug("All domains paused")
    return refresh_deployment_status(request)


def refresh_deployment_status(request):
    logger.debug('---- ajax refresh_deployment_status ----')
    required_fields = set(['topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    topology_id = request.POST['topologyId']

    if topology_id == "":
        logger.debug("Found a blank topology_id, returning full hypervisor status")
        return refresh_hypervisor_status(request)

    if configuration.deployment_backend == "openstack":
        logger.info('Refresh openstack deployment status')
        return refresh_openstack_deployment_status(request, topology_id)
    else:
        domain_list = libvirtUtils.get_domains_for_topology("t" + topology_id + "_")
        network_list = []
        is_linux = False
        if osUtils.check_is_linux():
            is_linux = True
            network_list = libvirtUtils.get_networks_for_topology("t" + topology_id + "_")

        context = {'domain_list': domain_list, 'network_list': network_list, 'topologyId': topology_id,
                   'isLinux': is_linux}
        return render(request, 'ajax/deploymentStatus.html', context)


def refresh_openstack_deployment_status(request, topology_id):
    logger.debug('---- ajax refresh_openstack_deployment_status ----')
    if not openstackUtils.connect_to_openstack():
        error_message = "Could not connect to Openstack!"
        logger.error(error_message)
        return render(request, 'ajax/ajaxError.html', {'error': error_message})

    topology = Topology.objects.get(pk=topology_id)
    stack_name = topology.name.replace(' ', '_')
    stack_details = openstackUtils.get_stack_details(stack_name)
    stack_resources = dict()
    logger.debug(stack_details)
    if stack_details is not None and 'stack_status' in stack_details and 'COMPLETE' in stack_details["stack_status"]:
        stack_resources = openstackUtils.get_stack_resources(stack_name, stack_details["id"])

    if hasattr(configuration, 'openstack_horizon_url'):
        horizon_url = configuration.openstack_horizon_url
    else:
        horizon_url = 'http://' + configuration.openstack_host + '/dashboard'

    context = {"stack": stack_details, "topology_id": topology.id,
               "openstack_host": configuration.openstack_host,
               "openstack_horizon_url": horizon_url,
               "stack_resources": stack_resources
               }
    return render(request, 'ajax/openstackDeploymentStatus.html', context)


def refresh_host_load(request):
    (one, five, ten) = os.getloadavg()
    load = {'one': one, 'five': five, 'ten': ten}
    context = {'load': load}
    return render(request, 'ajax/hostLoad.html', context)


def refresh_hypervisor_status(request):
    try:
        domains = libvirtUtils.list_domains()
        if osUtils.check_is_linux():
            networks = libvirtUtils.list_networks()
        else:
            networks = []

        context = {'domain_list': domains, 'network_list': networks}
        return render(request, 'ajax/deploymentStatus.html', context)

    except Exception as e:
        return render(request, 'ajax/ajaxError.html', {'error': e})


def check_ip(request):
    required_fields = set(['ip'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    ip_address = request.POST['ip']
    ip_exists = osUtils.check_ip(ip_address)
    response_data = {"result": ip_exists}
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_available_ip(request):
    # just grab the next available IP that is not currently
    # reserved via DHCP. This only get's called from topologies/new.html
    # when we've allocated all the IPs to various topologies
    # this allows new topologies to be built with overlapping
    # IP addresses. This makes the attempt to use 'old' ips that
    # are at least not still in use.
    logger.info("getting ips that are currently reserved via DHCP")
    all_used_ips = wistarUtils.get_consumed_management_ips()
    logger.debug(all_used_ips)
    next_ip = wistarUtils.get_next_ip(all_used_ips, 2)
    logger.debug(next_ip)
    response_data = {"result": next_ip}
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def manage_domain(request):
    required_fields = set(['domainId', 'action', 'topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    domain_id = request.POST['domainId']
    action = request.POST['action']
    topology_id = request.POST["topologyId"]

    if action == "start":
        # force all networks to be up before we start a topology
        # potential minor optimization here to only start networks attached to domain
        networks = libvirtUtils.get_networks_for_topology(topology_id)
        for network in networks:
            if network["state"] != "running":
                libvirtUtils.start_network(network["name"])

        # prevent start up errors by missing ISO files - i.e cloud-init seed files
        domain = libvirtUtils.get_domain_by_uuid(domain_id)
        iso = libvirtUtils.get_iso_for_domain(domain.name())
        # if we have an ISO file configured, and it doesn't actually exist
        # just remove it completely
        if iso is not None and not osUtils.check_path(iso):
            logger.debug("Removing non-existent ISO from domain")
            libvirtUtils.detach_iso_from_domain(domain.name())

        # now we should be able to safely start the domain
        if libvirtUtils.start_domain(domain_id):
            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not start domain!"})

    elif action == "stop":
        if libvirtUtils.stop_domain(domain_id):
            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not stop domain!"})

    elif action == "suspend":
        if libvirtUtils.suspend_domain(domain_id):
            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not suspend domain!"})

    elif action == "undefine":

        domain = libvirtUtils.get_domain_by_uuid(domain_id)
        domain_name = domain.name()

        source_file = libvirtUtils.get_image_for_domain(domain_id)
        if libvirtUtils.undefine_domain(domain_id):
            if source_file is not None:
                osUtils.remove_instance(source_file)
                osUtils.remove_cloud_init_seed_dir_for_domain(domain_name)

            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not stop domain!"})
    else:
        return render(request, 'ajax/ajaxError.html', {'error': "Unknown Parameters in POST!"})


def manage_network(request):
    required_fields = set(['networkName', 'action', 'topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    network_name = request.POST['networkName']
    action = request.POST['action']

    if action == "start":
        if libvirtUtils.start_network(network_name):
            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not start network!"})
    elif action == "stop":
        if libvirtUtils.stop_network(network_name):
            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not stop network!"})

    elif action == "undefine":
        # clean up ovs bridges if needed
        if hasattr(configuration, "use_openvswitch") and configuration.use_openvswitch:
            use_ovs = True
        else:
            use_ovs = False

        if libvirtUtils.undefine_network(network_name):
            if use_ovs:
                ovsUtils.delete_bridge(network_name)

            return refresh_deployment_status(request)
        else:
            return render(request, 'ajax/ajaxError.html', {'error': "Could not stop domain!"})
    else:
        return render(request, 'ajax/ajaxError.html', {'error': "Unknown Parameters in POST!"})


def multi_clone_topology(request):
    response_data = {"result": True}
    required_fields = set(['clones', 'topologyId'])
    if not required_fields.issubset(request.POST):
        response_data["message"] = "Invalid Parameters in Post"
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    topology_id = request.POST["topologyId"]
    num_clones = request.POST["clones"]

    logger.debug(num_clones)

    topology = Topology.objects.get(pk=topology_id)
    orig_name = topology.name
    json_data = topology.json
    i = 0
    while i < int(num_clones):

        nj = wistarUtils.clone_topology(json_data)
        if nj is not None:
            new_topology = topology
            new_topology.name = orig_name + " " + str(i + 1).zfill(2)
            new_topology.json = nj
            json_data = new_topology.json
            new_topology.id = None
            new_topology.save()

        i += 1

    return HttpResponse(json.dumps(response_data), content_type="application/json")


def redeploy_topology(request):
    required_fields = set(['json', 'topologyId'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "No Topology Id in request"})

    topology_id = request.POST['topologyId']
    j = request.POST['json']
    try:
        topo = Topology.objects.get(pk=topology_id)
        topo.json = j
        topo.save()
    except ObjectDoesNotExist:
        return render(request, 'ajax/ajaxError.html', {'error': "Topology doesn't exist"})

    try:
        domains = libvirtUtils.get_domains_for_topology(topology_id)
        config = wistarUtils.load_config_from_topology_json(topo.json, topology_id)

        logger.debug('checking for orphaned domains first')
        # find domains we no longer need
        for d in domains:
            logger.debug('checking domain: %s' % d['name'])
            found = False
            for config_device in config["devices"]:
                if config_device['name'] == d['name']:
                    found = True
                    continue

            if not found:
                logger.info("undefine domain: " + d["name"])
                source_file = libvirtUtils.get_image_for_domain(d["uuid"])
                if libvirtUtils.undefine_domain(d["uuid"]):
                    if source_file is not None:
                        osUtils.remove_instance(source_file)

                    osUtils.remove_cloud_init_seed_dir_for_domain(d['name'])

    except Exception as e:
        logger.debug("Caught Exception in redeploy")
        logger.debug(str(e))
        return render(request, 'ajax/ajaxError.html', {'error': str(e)})

    # forward onto deploy topo
    try:
        inline_deploy_topology(config)
        inventory = wistarUtils.get_topology_inventory(topo)
        wistarUtils.send_new_topology_event(inventory)
    except Exception as e:
        logger.debug("Caught Exception in inline_deploy")
        logger.debug(str(e))
        return render(request, 'ajax/ajaxError.html', {'error': str(e)})

    return refresh_deployment_status(request)


def deploy_topology(request):
    if 'topologyId' not in request.POST:
        return render(request, 'ajax/ajaxError.html', {'error': "No Topology Id in request"})

    topology_id = request.POST['topologyId']
    try:
        topo = Topology.objects.get(pk=topology_id)
    except ObjectDoesNotExist:
        return render(request, 'ajax/ajaxError.html', {'error': "Topology not found!"})

    try:
        # let's parse the json and convert to simple lists and dicts
        config = wistarUtils.load_config_from_topology_json(topo.json, topology_id)
        # FIXME - should this be pushed into another module?
        inline_deploy_topology(config)
        inventory = wistarUtils.get_topology_inventory(topo)
        wistarUtils.send_new_topology_event(inventory)
    except Exception as e:
        logger.debug("Caught Exception in deploy")
        logger.debug(str(e))
        return render(request, 'ajax/ajaxError.html', {'error': str(e)})

    domain_list = libvirtUtils.get_domains_for_topology("t" + topology_id + "_")
    network_list = []

    if osUtils.check_is_linux():
        network_list = libvirtUtils.get_networks_for_topology("t" + topology_id + "_")
    context = {'domain_list': domain_list, 'network_list': network_list, 'isLinux': True, 'topologyId': topology_id}
    return render(request, 'ajax/deploymentStatus.html', context)


def inline_deploy_topology(config):
    """
    takes the topology configuration object and deploys to the appropriate hypervisor
    :param config: output of the wistarUtils.
    :return:
    """

    if configuration.deployment_backend != 'kvm':
        raise WistarException('Cannot deploy to KVM configured deployment backend is %s'
                              % configuration.deployment_backend)

    is_ovs = False
    is_linux = osUtils.check_is_linux()
    is_ubuntu = osUtils.check_is_ubuntu()

    if hasattr(configuration, "use_openvswitch") and configuration.use_openvswitch:
        is_ovs = True

    # only create networks on Linux/KVM
    logger.debug("Checking if we should create networks first!")
    if is_linux:
        for network in config["networks"]:

            network_xml_path = "ajax/kvm/network.xml"

            # Do we need openvswitch here?
            if is_ovs:
                # set the network_xml_path to point to a network configuration that defines the ovs type here
                network_xml_path = "ajax/kvm/network_ovs.xml"
                if not ovsUtils.create_bridge(network["name"]):
                    err = "Could not create ovs bridge"
                    logger.error(err)
                    raise Exception(err)

            try:
                if not libvirtUtils.network_exists(network["name"]):
                    logger.debug("Rendering networkXml for: %s" % network["name"])
                    network_xml = render_to_string(network_xml_path, {'network': network})
                    logger.debug(network_xml)
                    libvirtUtils.define_network_from_xml(network_xml)
                    time.sleep(.5)

                logger.debug("Starting network")
                libvirtUtils.start_network(network["name"])
            except Exception as e:
                raise Exception(str(e))

    # are we on linux? are we on Ubuntu linux? set kvm emulator accordingly
    vm_env = dict()
    vm_env["emulator"] = "/usr/libexec/qemu-kvm"
    vm_env["pcType"] = "rhel6.5.0"
    # possible values for 'cache' are 'none' (default) and 'writethrough'. Use writethrough if you want to
    # mount the instances directory on a glusterFs or tmpfs volume. This might make sense if you have tons of RAM
    # and want to alleviate IO issues. If in doubt, leave it as 'none'
    vm_env["cache"] = configuration.filesystem_cache_mode
    vm_env["io"] = configuration.filesystem_io_mode

    if is_linux and is_ubuntu:
        vm_env["emulator"] = "/usr/bin/kvm-spice"
        vm_env["pcType"] = "pc"

    # by default, we use kvm as the hypervisor
    domain_xml_path = "ajax/kvm/"
    if not is_linux:
        # if we're not on Linux, then let's try to use vbox instead
        domain_xml_path = "ajax/vbox/"

    for device in config["devices"]:
        domain_exists = False
        try:
            if libvirtUtils.domain_exists(device['name']):
                domain_exists = True
                device_domain = libvirtUtils.get_domain_by_name(device['name'])
                device['domain_uuid'] = device_domain.UUIDString()
            else:
                device['domain_uuid'] = ''

            # if not libvirtUtils.domain_exists(device["name"]):
            logger.debug("Rendering deviceXml for: %s" % device["name"])

            configuration_file = device["configurationFile"]
            logger.debug("using config file: " + configuration_file)

            logger.debug(device)

            image = Image.objects.get(pk=device["imageId"])
            image_base_path = settings.MEDIA_ROOT + "/" + image.filePath.url
            instance_path = osUtils.get_instance_path_from_image(image_base_path, device["name"])

            secondary_disk = ""
            tertiary_disk = ""

            if not osUtils.check_path(instance_path):
                if device["resizeImage"] > 0:
                    logger.debug('resizing image')
                    if not osUtils.create_thick_provision_instance(image_base_path,
                                                                   device["name"],
                                                                   device["resizeImage"]):
                        raise Exception("Could not resize image instance for image: " + device["name"])

                else:
                    if not osUtils.create_thin_provision_instance(image_base_path, device["name"]):
                        raise Exception("Could not create image instance for image: " + image_base_path)

            if "type" in device["secondaryDiskParams"]:
                secondary_disk = wistarUtils.create_disk_instance(device, device["secondaryDiskParams"])

            if "type" in device["tertiaryDiskParams"]:
                tertiary_disk = wistarUtils.create_disk_instance(device, device["tertiaryDiskParams"])

            cloud_init_path = ''
            if device["cloudInitSupport"]:
                # grab the last interface
                management_interface = device["managementInterface"]

                # grab the prefix len from the management subnet which is in the form 192.168.122.0/24
                if '/' in configuration.management_subnet:
                    management_prefix_len = configuration.management_subnet.split('/')[1]
                else:
                    management_prefix_len = '24'

                management_ip = device['ip'] + '/' + management_prefix_len

                # domain_name, host_name, mgmt_ip, mgmt_interface
                script_string = ""
                script_param = ""
                roles = list()

                if 'roles' in device and type(device['roles']) is list:
                    roles = device['roles']

                if device["configScriptId"] != 0:
                    logger.debug("Passing script data!")

                    script = osUtils.get_cloud_init_template(device['configScriptId'])
                    script_param = device["configScriptParam"]

                    logger.debug("Creating cloud init path for linux image")
                    cloud_init_path = osUtils.create_cloud_init_img(device["name"], device["label"],
                                                                    management_ip, management_interface,
                                                                    device["password"], script, script_param, roles)

                    logger.debug(cloud_init_path)

            device_xml = render_to_string(domain_xml_path + configuration_file,
                                          {'device': device, 'instancePath': instance_path,
                                           'vm_env': vm_env, 'cloud_init_path': cloud_init_path,
                                           'secondary_disk_path': secondary_disk,
                                           'tertiary_disk_path': tertiary_disk,
                                           'use_ovs': is_ovs}
                                          )
            logger.debug(device_xml)
            libvirtUtils.define_domain_from_xml(device_xml)

            if not domain_exists:
                logger.debug("Reserving IP with dnsmasq")
                management_mac = libvirtUtils.get_management_interface_mac_for_domain(device["name"])
                logger.debug('got management mac')
                logger.debug(management_mac)
                libvirtUtils.reserve_management_ip_for_mac(management_mac, device["ip"], device["name"])
                logger.debug('management ip is reserved for mac')

        except Exception as ex:
            logger.warn("Raising exception")
            logger.error(ex)
            logger.error(traceback.format_exc())
            raise Exception(str(ex))


def launch_web_console(request):
    logger.debug("Let's launch a console!")

    required_fields = set(['domain'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    response_data = {"result": True}
    domain = request.POST["domain"]
    logger.debug("Got domain of: " + domain)
    # this keeps a list of used ports around for us
    wc_dict = request.session.get("webConsoleDict")

    # server = request.META["SERVER_NAME"]
    server = request.get_host().split(":")[0]

    logger.debug(wc_dict)
    if wc_dict is None:
        logger.debug("no previous webConsoles Found!")
        wc_dict = {}
        request.session["webConsoleDict"] = wc_dict

    logger.debug("OK, do we have this domain?")
    if domain in wc_dict:
        wc_config = wc_dict[domain]
        wc_port = wc_config["wsPort"]
        vnc_port = wc_config["vncPort"]

        if wistarUtils.check_web_socket(server, wc_port):
            logger.debug("This WebSocket is already running")

            response_data["message"] = "already running on port: " + wc_port
            response_data["port"] = wc_port
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:

            # Let's verify the vnc port hasn't changed. Could happen if topology is deleted and recreated with
            # same VM names. Rare but happens to me all the time!
            d = libvirtUtils.get_domain_by_name(domain)

            if not libvirtUtils.is_domain_running(domain):
                libvirtUtils.start_domain_by_name(domain)

            # now grab the configured vncport
            true_vnc_port = libvirtUtils.get_domain_vnc_port(d)

            if true_vnc_port != vnc_port:
                logger.debug("Found out of sync vnc port!")
                vnc_port = true_vnc_port

            pid = wistarUtils.launch_web_socket(wc_port, vnc_port, server)
            if pid is not None:
                wc_config["pid"] = pid
                wc_config["vncPort"] = true_vnc_port
                wc_dict[domain] = wc_config
                request.session["webConsoleDict"] = wc_dict

                response_data["message"] = "started WebConsole on port: " + wc_port
                response_data["port"] = wc_port
                return HttpResponse(json.dumps(response_data), content_type="application/json")
            else:
                response_data["result"] = False
                response_data["message"] = "Could not start webConsole"
                return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        logger.debug("nope")
        # start the ws ports at 6900
        wc_port = len(list(wc_dict.keys())) + 6900

        logger.debug("using wsPort of " + str(wc_port))
        # get the domain from the hypervisor
        d = libvirtUtils.get_domain_by_name(domain)
        # now grab the configured vncport
        vnc_port = libvirtUtils.get_domain_vnc_port(d)

        logger.debug("Got VNC port " + str(vnc_port))
        pid = wistarUtils.launch_web_socket(wc_port, vnc_port, server)

        if pid is None:
            logger.debug("oh no")
            response_data["result"] = False
            response_data["message"] = "Could not start webConsole"
            logger.debug("returning")
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        logger.debug("Launched with pid " + str(pid))
        wcConfig = dict()
        wcConfig["pid"] = str(pid)
        wcConfig["vncPort"] = str(vnc_port)
        wcConfig["wsPort"] = str(wc_port)

        wc_dict[domain] = wcConfig
        request.session["webConsoleDict"] = wc_dict

        response_data["message"] = "started WebConsole on port: " + str(wc_port)
        response_data["port"] = wc_port
        return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_topology_config(request):
    """
        Grab a json object representing the topology config
        as well as the domain status for each object
        This is useful to get a list of all objects on the topolgy,
        filter for objects of a specific type, and verify their boot up state.
        i.e. to run a command against all Junos devices for example

    """
    if 'topologyId' not in request.POST:
        return render(request, 'ajax/ajaxError.html', {'error': "No Topology Id in request"})

    topology_id = request.POST['topologyId']

    try:
        topo = Topology.objects.get(pk=topology_id)
        # let's parse the json and convert to simple lists and dicts
        config = wistarUtils.load_config_from_topology_json(topo.json, topology_id)
        domain_status = libvirtUtils.get_domains_for_topology("t" + topology_id + "_")

        context = {'config': config, 'domain_status': domain_status, 'topologyId': topology_id}

        logger.debug("returning")
        return HttpResponse(json.dumps(context), content_type="application/json")
    except Exception as ex:
        logger.debug(ex)
        return render(request, 'ajax/ajaxError.html', {'error': "Topology not found!"})


# query libvirt for all instances that are currently running
# grab configured ip addresses from topology as well.
def get_available_instances(request):
    if 'scriptId' not in request.POST:
        return render(request, 'ajax/ajaxError.html', {'error': "No script Id in request"})

    script_id = request.POST['scriptId']
    script = Script.objects.get(pk=script_id)

    instances = []

    domains = libvirtUtils.list_domains()
    for domain in domains:
        if domain["state"] == "running":
            name = domain["name"]
            topo_id = name.split('_')[0].replace('t', '')
            # logger.debug(name + " " + topo_id)
            topology = Topology.objects.get(pk=topo_id)
            tj = json.loads(topology.json)
            for obj in tj:
                if "userData" in obj and "wistarVm" in obj["userData"]:
                    ip = obj["userData"]["ip"]
                    label = obj["userData"]["label"]
                    obj_type = obj["userData"]["type"]
                    if label == name.split('_')[1]:
                        instance = {
                            'name': name,
                            'ip': ip,
                            'type': obj_type,
                            'topo_id': topo_id
                        }

                        logger.debug("Found a running instance for this topology!")
                        instances.append(instance)
                        continue

    context = {'instances': instances, 'script': script}
    return render(request, 'ajax/availableInstances.html', context)


def manage_iso(request):
    required_fields = set(['domainName', 'path', 'topologyId', 'action'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    domain_name = request.POST['domainName']
    file_path = settings.MEDIA_ROOT + "/media/" + request.POST["path"]
    action = request.POST["action"]

    logger.debug(domain_name)
    logger.debug(file_path)
    if action == "attach":
        if libvirtUtils.attach_iso_to_domain(domain_name, file_path):
            context = {'result': "Success"}
            logger.debug("iso attached to domain successfully")
        else:
            context = {'result': False}
    else:
        if libvirtUtils.detach_iso_from_domain(domain_name):
            context = {'result': "Success"}
            logger.debug("iso detached from domain successfully")
        else:
            context = {'result': False}

    return HttpResponse(json.dumps(context), content_type="application/json")


def list_isos(request):
    required_fields = set(['domainName'])
    if not required_fields.issubset(request.POST):
        return render(request, 'ajax/ajaxError.html', {'error': "Invalid Parameters in POST"})

    domain_name = request.POST['domainName']
    current_iso = libvirtUtils.get_iso_for_domain(domain_name)

    dir_list = osUtils.list_dir(settings.MEDIA_ROOT + '/media')
    logger.debug(str(dir_list))

    context = {
        'media': dir_list,
        'currentIso': current_iso,
        'mediaDir': settings.MEDIA_ROOT + "/media",
        'domainName': domain_name
    }

    return render(request, 'ajax/manageIso.html', context)


def deploy_stack(request, topology_id):
    """
    :param request: Django request
    :param topology_id: id of the topology to export
    :return: renders the heat template
    """
    try:
        topology = Topology.objects.get(pk=topology_id)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'error': "Topology not found!"})

    try:
        # generate a stack name
        # FIXME should add a check to verify this is a unique name
        stack_name = topology.name.replace(' ', '_')

        # let's parse the json and convert to simple lists and dicts
        logger.debug("loading config")
        config = wistarUtils.load_config_from_topology_json(topology.json, topology_id)
        logger.debug("Config is loaded")
        heat_template = wistarUtils.get_heat_json_from_topology_config(config, stack_name)
        logger.debug("heat template created")
        if not openstackUtils.connect_to_openstack():
            return render(request, 'error.html', {'error': "Could not connect to Openstack"})

        # get the tenant_id of the desired project
        tenant_id = openstackUtils.get_project_id(configuration.openstack_project)
        logger.debug("using tenant_id of: %s" % tenant_id)
        if tenant_id is None:
            raise Exception("No project found for %s" % configuration.openstack_project)

        # FIXME - verify all images are in glance before jumping off here!

        ret = openstackUtils.create_stack(stack_name, heat_template)
        if ret is not None:
            inventory = wistarUtils.get_topology_inventory(topology)
            wistarUtils.send_new_topology_event(inventory)

        return HttpResponseRedirect('/topologies/' + topology_id + '/')

    except Exception as e:
        logger.debug("Caught Exception in deploy")
        logger.debug(str(e))
        return render(request, 'error.html', {'error': str(e)})


def delete_stack(request, topology_id):
    """
    :param request: Django request
    :param topology_id: id of the topology to remove from OpenStack
    :return: redirect to topology detail screen
    """

    try:
        topology = Topology.objects.get(pk=topology_id)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'error': "Topology not found!"})

    stack_name = topology.name.replace(' ', '_')
    if openstackUtils.connect_to_openstack():
        logger.debug(openstackUtils.delete_stack(stack_name))

    return HttpResponseRedirect('/topologies/' + topology_id + '/')
