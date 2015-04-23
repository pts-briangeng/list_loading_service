import logging
import mock
import unittest

from nose.tools import assert_equal, assert_false, assert_true

from app import instrumentation


class NoOp(object):

    def no_op(self):
        pass


class InstrumentationTestCase(unittest.TestCase):

    @mock.patch('app.instrumentation.profile_call')
    def test_no_instrumentation_at_info_level(self, mock_profile):
        instrumentation.instrument([NoOp], logging.INFO)

        NoOp().no_op()

        assert_false(mock_profile.called)

    @mock.patch('app.instrumentation.profile_call')
    def test_no_instrumentation_at_warn_level(self, mock_profile):
        instrumentation.instrument([NoOp], logging.WARN)

        NoOp().no_op()

        assert_false(mock_profile.called)

    @mock.patch('app.instrumentation.profile_call')
    def test_instrumentation_at_debug_level(self, mock_profile):
        instrumentation.instrument([NoOp], logging.DEBUG)

        NoOp().no_op()

        assert_true(mock_profile.called)

    @mock.patch('app.instrumentation._inspect_call')
    def test_profile_call_logs_profiling_outcome(self, mock_inspection):
        mock_inspection.return_value = 'module', 1, 'function', mock.MagicMock()

        wrapper = instrumentation.profile_call(NoOp.no_op)
        assert_true(hasattr(wrapper, '__call__'))
        wrapper()

        assert_true(mock_inspection.called)

    def test_inspect_call_returns_expected_stack_information(self):
        module, lineno, function_name, _ = instrumentation._inspect_call()
        assert_equal('unittest.case', module)
        assert_equal('__call__', function_name)
