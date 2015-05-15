import yaml
import os
import fabrika
import configuration as sys_config

from fabric.decorators import roles
from fabric.api import task
from fabric.api import env
from fabric.api import execute
from fabrika.tasks.docker import SetupLoadBalancerBehindGateway

CONTAINER_HOSTNAME = 'node'
DEPENDENCIES = 'dependencies'
DNS_SERVER_2 = 'dns2'
DNS_SERVER_1 = 'dns1'
LOAD_BALANCER_NODES = 'nodes'
LOAD_BALANCER_PORT = 'load_balancer_port'
LOAD_BALANCER_HOST = 'load_balancer_host'
LOAD_BALANCER_MODE = 'mode'
NODE_PORT = 'node_port'
ENABLE_NSCD = 'enable_nscd'

FABRIC_ROLE_DOCKER_HOST = 'docker_host'
FABRIC_ROLE_LOAD_BALANCER = 'lb_config_node'
FABRIC_ROLE_ELASTIC_SEARCH_LOAD_BALANCER = 'elastic_search_lb_config_node'

NSCD_SOCKET_SOURCE = '/var/run/nscd'
NSCD_SOCKET_TARGET = '/tmp/nscd-extern'

deploy_task = fabrika.tasks.docker.DeployTask('list_loading_service')
load_balancer_task = SetupLoadBalancerBehindGateway()


@task()
def full_deploy(environment, full_image_name, configuration_dir, run_migrate=False, enable_nscd=None):
    _parse_deployment_yaml(environment)
    env_properties = """
    roledefs  : {roledefs}
    hosts     : {hosts}
    properties: {properties}
    """
    print(env_properties.format(roledefs=env.roledefs, hosts=env.hosts, properties=env.host_role_properties))

    execute(deploy_docker_image, full_image_name, configuration_dir, enable_nscd=enable_nscd)
    execute(setup_elastic_search_service_load_balancer)
    execute(setup_lls_service_load_balancer)


def _associate_host_to_a_role(host, role):
    if role not in env.roledefs:
        env.roledefs[role] = []
    env.roledefs[role].append(host)


def _parse_deployment_yaml(environment):
    env.host_role_properties = {}
    deploy_cfg_file = os.path.join(os.getcwd(), "fabfile/deploy/{}.yml".format(environment))
    yaml_config = yaml.load(open(deploy_cfg_file, 'r'))
    for host in yaml_config:
        for role in yaml_config[host]['roles']:
            _associate_host_to_a_role(host, role)
            env.host_role_properties[(host, role)] = yaml_config[host]['roles'][role]


def set_load_balancer(role):
    load_balancer_config = env.host_role_properties[(env.host, role)]
    execute(load_balancer_task,
            load_balancer_config[LOAD_BALANCER_HOST],
            load_balancer_config[LOAD_BALANCER_PORT],
            load_balancer_config[LOAD_BALANCER_NODES],
            load_balancer_config[NODE_PORT],
            load_balancer_config.get(LOAD_BALANCER_MODE))


@roles(FABRIC_ROLE_LOAD_BALANCER)
def setup_lls_service_load_balancer():
    print(">>>>>>> setting up load balancer on host {}".format(env.host_string))
    set_load_balancer(FABRIC_ROLE_LOAD_BALANCER)


@roles(FABRIC_ROLE_ELASTIC_SEARCH_LOAD_BALANCER)
def setup_elastic_search_service_load_balancer():
    print(">>>>>>> setting up search service load balancer on host {}".format(env.host_string))
    set_load_balancer(FABRIC_ROLE_ELASTIC_SEARCH_LOAD_BALANCER)


def _process_nscd_mapping(volume_mappings, configuration, override):
    option_overridden = override is not None

    if option_overridden:
        if override:
            volume_mappings[NSCD_SOCKET_SOURCE] = NSCD_SOCKET_TARGET
        return volume_mappings

    if configuration.get(ENABLE_NSCD):
        volume_mappings[NSCD_SOCKET_SOURCE] = NSCD_SOCKET_TARGET
    return volume_mappings


@roles(FABRIC_ROLE_DOCKER_HOST)
def deploy_docker_image(fully_qualified_image_name, app_container_config_path, enable_nscd=None, stop_existing=True):
    print(">>>>>>> deploy_docker_image on host {}".format(env.host))
    node_deploy_configuration = env.host_role_properties[(env.host, FABRIC_ROLE_DOCKER_HOST)]

    volume_mappings = _process_nscd_mapping({}, node_deploy_configuration, enable_nscd)
    # FIXME: will be fixed soon, B.G.
    # volume_mappings[sys_config.volumn_mappings_file_upload_source] = sys_config.volumn_mappings_file_upload_target
    volume_mappings['/content/list_upload'] = '/content/list_upload'

    print "*************************************************************************************"
    print volume_mappings
    print "*************************************************************************************"

    deploy_task = fabrika.tasks.docker.DeployTask('list_loading_service', volume_mappings=volume_mappings)

    execute(deploy_task,
            fully_qualified_image_name,
            node_deploy_configuration.get(DEPENDENCIES),
            node_deploy_configuration.get(DNS_SERVER_1),
            node_deploy_configuration.get(DNS_SERVER_2),
            node_deploy_configuration.get(CONTAINER_HOSTNAME),
            app_container_config_path,
            stop_existing=stop_existing)
