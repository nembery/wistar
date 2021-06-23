import os
from . import configuration as config


def setup_configuration():
    """
    Check environment for any variables that start with 'WISTAR_' then compares those
    with wistar configuration attributes. If any are found that match, override the configuration
    with that value. Useful for docker deployments
    :return: None
    """
    for e in os.environ:
        print('Looking for env var %s' % e)
        if str(e).startswith('WISTAR_'):
            config_item = str(e).split('WISTAR_')[1]
            config_value = os.environ.get(e)
            if hasattr(config, config_item):
                setattr(config, config_item, config_value)


setup_configuration()
