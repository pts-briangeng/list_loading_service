import logging

from liblcp import context, lcp_logging


def context_mode_adder(value):
    try:
        context_mode = context.get_headers().get(context.HEADERS_MODE, None)
    except:
        context_mode = None
    return '{} [{}]'.format(value, context_mode)


class ApplicationLoggingFormatter(logging.Formatter):
    message_editors = (
        lcp_logging.cid_adder,
        context_mode_adder
    )

    def format(self, record):
        value = super(ApplicationLoggingFormatter, self).format(record)
        for editor in self.message_editors:
            value = editor(value)
        return value


def install_required_root_formatter():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        old_formatter = handler.formatter
        handler.setFormatter(ApplicationLoggingFormatter(old_formatter._fmt, old_formatter.datefmt))
