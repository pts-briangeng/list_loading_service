"""
Define the WSGI application callable that will be run by a WSGI gateway
such as mod_wsgi under Apache. For Flask, this is just an instance of the
Flask app, but must be named 'application' as per the WSGI standard.
"""
import os
import sys

sys.path.append('/content')

from app import api_builder  # noqa

os.environ['SERVICES_CONFIG_HOME'] = os.path.abspath('/config')

application = api_builder.build_server()
