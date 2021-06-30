# some basic configuration parameters for wistar

from . import vm_definitions
# What should we show as the title across all pages?
# Useful to customize this if you have multiple wistar instances on different servers / clusters
wistar_title = 'Automated Solutions POC Cloud (C126)'

# shortcut to fill in default instance password in 'New VM' screen
# Make sure this meets the complexity requirements for your VMs!
# i.e. for junos you need 3 of these 4: upper / lower / special / number
default_instance_password = 'Paloalto1!'

# user that will be configured via cloud-init - override this to your username if desired!
ssh_user = "paloalto"
# this key will be added to cloud-init enabled hosts in the user-data file
# by default this is a dummy key! Replace this with your own key generated from 'ssh-keygen'
ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDaS/onir4QchoABVamLXX/1swh2z41sTcfzN9reHQ6om/mHL7svpaiKiSRHR5RDOw4kib10+l3w03i0lkaNqXjDYpfoymT7+cRciuyUU1E/TTQ8jtgkpeFh0ZsFcGscUtlpiGJPWXJBK/pA48TUkeAOBiIoARZESEtPJUQji99U3jKTfOZopADKg6J6HYMr2CwcccNdNcEqSpwe6bwKoWmTDowPOO/L/jmtt4Ev2qeGIIXPKZ5O/XWXhQKwL1MDoNsv0BDuEaOqMXrwCpcYmBM/zpdahUxqkjrLvw0KEC0kIqSL0SmqV+it3fElWeV2qzxkAyauMkRrNriBqyx3VIL root@sps-controller-01"
# Registered VM Image types
# this list will register the javascript VM configuration settings in
# common/static/js/vm_types

# images director
user_images_dir = "/opt/wistar/user_images"

# deployment backend to use!
# defaults to kvm
# options are 'openstack', 'vagrant', 'virtualbox'
# deployment_backend = 'kvm'
deployment_backend = 'openstack'

# KVM configuration
# cache mode, controls the cache mode:
# https://www.suse.com/documentation/sles11/book_kvm/data/sect1_1_chapter_book_kvm.html
# some filesystems do not support cache='none'
# valid options are 'none', 'writeback', 'writethrough', 'unsafe', 'directsync'
# it's possible there is some performance gain with 'none' and 'native' but this is not supported on all platforms!
filesystem_cache_mode = 'writethrough'
# io mode can be 'native' or 'threads'
filesystem_io_mode = 'threads'

# Openstack configuration
# show openstack options even if not the primary deployment option
# i.e. upload to glance is available but still deploy locally to kvm
use_openstack = True

# openstack horizon url is used to create Horizon URLs
# some version of openstack use '/dashboard', '/horizon', or '/'
openstack_horizon_url = "http://10.48.56.33"

# authentication parameters
openstack_host = '10.48.56.33'
openstack_user = 'wistar-as'
openstack_password = '6h#Re733&Yb&MhzSEtHPP?XhkSL8'

# project under which to place all topologies/stacks
openstack_project = 'as'

openstack_mgmt_network = 'as_cloud_mgmt'
openstack_external_network = 'external_10_48_58'

# Parameters for use with the VirtualBox deployment backend
# Host only network name in VirtualBox
virtual_box_host_only_net_name = 'vboxnet0'

# default external bridge name
kvm_external_bridge = "br0"

# Use OVS bridges - THIS IS EXPERIMENTAL AND WILL ALMOST CERTAINLY NOT WORK IN MOST CASES
# Best to keep this as false for now until ovs libvirt support has matured a bit
use_openvswitch = False

# Define the starting port number for VM's VNC
# This is needed if the system is using port 5900 or subsequent ports
# that may conflict qemu's assignemnt
vnc_start_port = 6000

# VM management network prefix
# this should match your Openstack mgmt_network subnet or the config of virbr0 when using KVM
management_subnet = '192.168.126.0/24'
management_prefix = '192.168.126.'
management_gateway = '192.168.126.1'
management_mask = '255.255.255.0'

# wistar cloud init seeds director / temp directory
seeds_dir = "/opt/wistar/seeds/"

scripts_dir = "/opt/wistar/scripts"


# keep vm_image_types in a separate file and just include them here
vm_image_types = vm_definitions.vm_image_types

# check vm boot status via network reachability
# set to false if wistar running in docker container with VMs on same host
check_vm_network_state = True
# extra configuration parameters to pass into cloud-init scripts
cloud_init_params = {
    'salt_master': '10.70.221.10',
    'wistar_key': '81BC461D-59F4-4A24-A72D-30923634AAB0'
}

# notification_url - where to send web hooks for new topology deployments
#notification_url = 'https://10.70.221.10:8000/hook'
# set these to use authenticated web hooks
#notification_login_url = 'https://10.70.221.10:8000/login'
#notification_login_payload = {
#"username": "salt",
#"password": "BqFRpSZxezKckwVQgtibBZa6GcVK",
#"eauth": "sharedsecret"
#}

# make our defined roles here
defined_roles = ['docker', 'kvm', 'pan-ecs']