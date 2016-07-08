import os
from contextlib import contextmanager

from liblcp import configuration as liblcp_config

import configuration

configuration_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'configuration')


@contextmanager
def configured_for(environment=''):
    configuration_file = os.path.abspath(os.path.join(configuration_path, environment, 'list_loading_service.cfg'))
    configuration.configure_from(configuration_file)
    liblcp_config_data = {}
    try:
        execfile(os.path.abspath(os.path.join(configuration_path, environment, 'servicecontainer.cfg')),
                 liblcp_config_data)
    except IOError:
        execfile(os.path.abspath(os.path.join(configuration_path, 'servicecontainer.cfg')), liblcp_config_data)
    liblcp_config.set_configuration(liblcp_config_data)
    yield
