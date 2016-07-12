"""
Define the WSGI application callable that will be run by a WSGI gateway
such as mod_wsgi under Apache. For Flask, this is just an instance of the
Flask app, but must be named 'application' as per the WSGI standard.
"""
import os
import sys

from newrelic import agent

config_home = os.environ['SERVICES_CONFIG_HOME'] = '/config'
new_relic_config = os.path.join(config_home, 'newrelic.ini')

try:
    agent.initialize(config_file=new_relic_config)
except Exception:
    pass

sys.path.append('/content')

from app.controllers import api_builder  # noqa

application = api_builder.build_server()
