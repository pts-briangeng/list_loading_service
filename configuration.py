import logging

from os import path


logger = logging.getLogger(__name__)


CONFIGURATION_PATH = path.abspath(path.join(path.dirname(__file__), 'configuration'))


class Container(dict):
    def __init__(self, **data):
        self.__dict__.update(data)


data = Container()


def configure_from(absolute_path):
    execfile(absolute_path, data.__dict__)
    _log_configuration(absolute_path)


def _log_configuration(filename, indent=4):
    configuration_items = []
    for key, value in data.items():
        configuration_items.append('{}{:<35}= {}'.format(' '*2*indent, key, value))
    logger.info("Loaded configuration from: '{}'".format(filename))
    logger.info('\n'.join(configuration_items))
