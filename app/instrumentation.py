import inspect
import logging
import time

import aspectlib

from app import controllers

logger = logging.getLogger(__name__)

INDEX_FUNCTION_FRAME = 3
INDEX_FILE = 0
INDEX_LINE = 2
INDEX_FUNCTION_NAME = 3


PROFILED_TARGETS = list(controllers.__all__)
PROFILED_TARGETS.extend([
    'app.services.elastic',
    'app.services.elastic.ElasticSearchService',
])


def instrument(targets_to_profile, log_level):
    """
    Instruments the given targets with a profiler (timing) function if the log level is at least DEBUG or
    more verbose.
    """
    logger.info('Configured log level is "%s"', log_level)
    if log_level > logging.DEBUG:
        logger.info('Instrumentation requires level of DEBUG (%s). Not instrumenting.', logging.DEBUG)
        return

    logger.info('Instrumentation enabled. Profiling: %s', targets_to_profile)
    _profile_targets(targets_to_profile)


def _profile_targets(targets):
    for target in targets:
        aspectlib.weave(target, profile_call)


@aspectlib.Aspect
def profile_call(*args, **kwargs):
    """
    Aspect implementation that profiles the execution time of the function to which it is weaved.

    The outcome is logged to the function's parent logger, and includes the module, function name, line number, and time
    elapsed for the call, precise to 5 decimal places.
    """
    start_time = time.time()
    result = yield aspectlib.Proceed
    end_time = time.time()

    module, lineno, function_name, logger = _inspect_call()

    logger.info('Executed "%s:%s:%s" - time elapsed: %s s',
                module,
                lineno,
                function_name,
                '{:.5f}'.format(round(end_time - start_time, 5)))
    yield aspectlib.Return(result)


def _inspect_call():
    wrapped_frame = inspect.stack()[INDEX_FUNCTION_FRAME]
    module = inspect.getmodule(wrapped_frame[INDEX_FILE]).__name__
    logger = logging.getLogger(module)
    lineno = wrapped_frame[INDEX_LINE]
    function_name = wrapped_frame[INDEX_FUNCTION_NAME]
    return module, lineno, function_name, logger
