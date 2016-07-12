import contextlib
import httplib
import json
import os
import shutil
import socket
import traceback
import uuid

import fabrika.constants
import fabrika.tasks.analysis
import fabrika.tasks.build
import fabrika.tasks.docker
import fabrika.tasks.testing
from fabric.api import env, execute, task
from fabric.operations import local
from fabric.tasks import Task
from lcpenv import tasks as lcpenv_tasks
from liblcp import context

import configuration as service_container_configuration
from app.controllers import api_builder
from fabfile.app_configuration import configured_for

DEFAULT_REGISTRY = 'prod_head'
DEFAULT_TAG = "1"
COVERAGE_OPTIONS = [
    '--with-coverage',
    '--cover-package={0}'.format('app'),
    '--cover-branches',
    '--cover-html',
    '--cover-html-dir={0}'.format(os.path.join('test_results', 'coverage')),
    '--cover-min-percentage=97'
]
BASE_REPOSITORY_TAG = "{}:procs25".format(fabrika.constants.BASE_IMAGE_REPO)
configuration_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'configuration')
env.use_ssh_config = True

context.set_headers_getter(lambda name: {context.HEADERS_EXTERNAL_BASE_URL: 'http://live.lcpenv',
                                         context.HEADERS_CORRELATION_ID: str(uuid.uuid4()),
                                         context.HEADERS_MODE: 'live',
                                         context.HEADERS_PRINCIPAL: str(uuid.uuid4())}[name])

# The gateway port will need to be updated later
configure_routing = lcpenv_tasks.GatewayRoutingConfigurationTask(
    gateway_port=2000, local_port=5000, service_name='list_loading_service', routing_endpoints=['/lists/'])

start_lcp = lcpenv_tasks.StartLcpTask()
stop_lcp = lcpenv_tasks.stop_lcp
destroy_lcp = lcpenv_tasks.destroy_lcp
preserve_logs = lcpenv_tasks.preserve_logs
generate_vagrantfile = lcpenv_tasks.generate_vagrantfile

local("mkdir -p list_loading_service_logs")


class ListLoadingServiceTestInContainerTask(fabrika.tasks.docker.TestInContainerTask, fabrika.tasks.testing.TestTask):

    def run(self, repo_type=DEFAULT_REGISTRY, tag=DEFAULT_TAG, host=None, keeplcp=False,
            configuration=os.path.join(configuration_path, 'testincontainer'),
            nose_options='-a system_integration',
            port=5000,
            services_profile='testincontainer',
            test_config='testincontainer.ini',
            logs_dir=None, volume_mappings=None, base_image_repo=BASE_REPOSITORY_TAG):

        if "-v" in nose_options or "--verbose" in nose_options:
            test_config += ";export LOG_LCP_REQUESTS=True"
        if "-a" not in nose_options and "--attr" not in nose_options:
            nose_options += " --attr container_integration "

        fabrika.tasks.testing.TestTask().test_requirements()
        execute(start_lcp)
        execute(configure_routing, host='vagrant@lcpenv')
        with container_profile(os.path.join(configuration_path, configuration, 'servicecontainer.cfg')):
            if not logs_dir:
                logs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        os.pardir,
                                        'list_loading_service_logs')
            try:
                with configured_for(services_profile):
                    file_upload_volume_mapping = {
                        os.path.join(configuration_path, '..', 'tests/samples/'):
                            service_container_configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET
                    }
                super(ListLoadingServiceTestInContainerTask, self).run(
                    repo_type, tag, configuration, nose_options, port, services_profile,
                    base_image_repo=base_image_repo, test_config=test_config, logs_dir=logs_dir,
                    volume_mappings=file_upload_volume_mapping
                )
            finally:
                execute(lcpenv_tasks.preserve_logs)
                if not keeplcp:
                    execute(lcpenv_tasks.stop_lcp)
                    execute(lcpenv_tasks.destroy_lcp)


@contextlib.contextmanager
def container_profile(configuration_profile_path):
    print("Creating configuration profile ....")

    def backed_up_configuration(profile_path):
        return profile_path + '.orig'

    def _ip():
        return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close())
                for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    print("Backing up current configuration ...{}".format(
        os.path.basename(backed_up_configuration(configuration_profile_path))))
    shutil.copyfile(configuration_profile_path, backed_up_configuration(configuration_profile_path))

    app_configuration = {}
    execfile(configuration_profile_path, app_configuration)
    del app_configuration['__builtins__']

    for key, value in app_configuration.iteritems():
        app_configuration[key] = (json.loads(json.dumps(value).replace('build_agent', _ip()))
                                  if not isinstance(value, basestring) else value.replace('build_agent', _ip()))

    with open(configuration_profile_path, 'w') as config_fp:
        for key, value in app_configuration.iteritems():
            config_fp.write("{} = {}\n".format(key, value)
                            if not isinstance(value, basestring) else '{} = "{}"\n'.format(key, value))
    try:
        yield
    except:
        print("Error {}".format(traceback.format_exc()))
        pass
    finally:
        print("Reverting to original configuration profile ....{}".format(os.path.basename(configuration_profile_path)))
        shutil.copyfile(backed_up_configuration(configuration_profile_path), configuration_profile_path)
        os.remove(backed_up_configuration(configuration_profile_path))
        print("Done!")


test_in_container_task = ListLoadingServiceTestInContainerTask(
    'list_loading_service', service_ready_endpoint='/_', service_ready_status=httplib.NOT_FOUND)


class ListLoadingServiceTestUnitsTask(fabrika.tasks.testing.TestUnitsTask):

    def __init__(self, app_package_name, coverage_options=None):
        super(ListLoadingServiceTestUnitsTask, self).__init__(app_package_name, coverage_options)

    def run(self, nose_options=None):
        self.test_requirements()
        execute(clean_task)
        execute(flake8_task)
        super(ListLoadingServiceTestUnitsTask, self).run(nose_options)


class CleanTask(fabrika.tasks.build.CleanTask):

    def __init__(self):
        super(CleanTask, self).__init__()

    def run(self):
        local('rm -f *.log')
        local('rm -rf list_loading_service_logs')
        local('rm -rf lcpenv_logs')
        super(CleanTask, self).run()


clean_task = CleanTask()
complexity_task = fabrika.tasks.analysis.ComplexityTask()
create_app_image_task = fabrika.tasks.docker.CreateAppImageTask('list_loading_service')
flake8_task = fabrika.tasks.analysis.Flake8Task()
package_task = fabrika.tasks.build.PackageTask()
push_task = fabrika.tasks.docker.PushToRegistryTask('list_loading_service')
runserver_task = fabrika.tasks.testing.RunServerTask(api_builder.build_server, configuration_path)
test_units_task = ListLoadingServiceTestUnitsTask('list_loading_service', COVERAGE_OPTIONS)
remove_images_task = fabrika.tasks.docker.RemoveImagesTask('list_loading_service')
remove_containers_task = fabrika.tasks.docker.RemoveContainersTask('list_loading_service')


@task()
def test_integration(test_config='local.ini', run_server=True, nose_options='--attr local_integration',
                     services_profile='localhost'):
    if "-v" in nose_options or "--verbose" in nose_options:
        test_config += ";export LOG_LCP_REQUESTS=True"
    if "-a" not in nose_options and "--attr" not in nose_options:
        nose_options += " --attr local_integration "
    with configured_for(services_profile):
        test_integration_task = fabrika.tasks.testing.TestIntegrationTask()
        test_integration_task.run(test_config, run_server, nose_options, services_profile)


class AutoPep8Task(Task):

    """Run autopep8 on modified files as per 'hg status'."""
    name = 'autopep8'

    def __init__(self, autopep8_options=None):
        super(AutoPep8Task, self).__init__()

        if autopep8_options is None:
            self.autopep8_options = ["-i $(hg status -ma | cut -c 3- | grep '\.py$' | tr '\n' ' ') ", ]
        else:
            self.autopep8_options = autopep8_options
        self.autopep8_options.append('--max-line-length=120')

    def run(self):
        local('autopep8 {}'.format(' '.join(self.autopep8_options)))


autopep8_task = AutoPep8Task()


@task
def test_all():
    """Run flake8 then unit and integration tests"""
    execute(test_units_task)
    execute(test_integration)
