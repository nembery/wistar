# Cloud init templates

This directory contains some example Cloud init templates. By default wistar will search

the directory configured via the `scripts_dir` configuration parameter and will use all files found there ending with
`j2` as options for cloud-init templates for each cloud-init enabled VM.


You can pass extra local configuration information via the `cloud_init_params` option in the configuration.py file.
Any entries in that dict will be made available to the jinja environment. This allows you to keep secrets and other
local information in a single file. 


If using the docker image, you should mount this directory as the `/opt/wistar/scripts` directory. 