def Any(cls):
    class Any(object):

        def __eq__(self, other):
            return type(other) == cls

    return Any()


def generator(data):
    yield data
