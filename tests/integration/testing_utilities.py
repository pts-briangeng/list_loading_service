import os
import random
import shutil
import uuid

from liblcp import context

import configuration
import fabfile


def generate_headers(mode=context.MODE_SANDBOX,
                     base_url=None,
                     cid=None,
                     principal=None):
    return dict({'Content-Type': 'application/json',
                 context.HEADERS_MODE: mode,
                 context.HEADERS_EXTERNAL_BASE_URL: configuration.data.list_loading_service_base_url,
                 context.HEADERS_CORRELATION_ID: cid or str(uuid.uuid4()),
                 context.HEADERS_PRINCIPAL: principal or configuration.data.lcp_principal})


def copy_test_file(file_name='normal.csv'):

    old_file = file_name.rsplit(".", 1)
    destination_file_name = old_file[0] + str(random.randint(0, 99999)) + "." + old_file[1]

    source_file_path = os.path.join(fabfile.configuration_path, '..', 'tests/samples/', file_name)
    destination_file_path = os.path.join(fabfile.configuration_path, '..', 'tests/samples/', destination_file_name)
    shutil.copy(source_file_path, destination_file_path)
    return destination_file_path.split("/")[-1]


def delete_test_files(file_name):
    file_path = os.path.join(fabfile.configuration_path, '..', 'tests/samples/', file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)
