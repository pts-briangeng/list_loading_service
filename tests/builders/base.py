import abc
import re
import random
import string
import uuid


DATA = {
    "id": str(uuid.uuid4()),
    "total_count": 1
}

_re_range = re.compile(r"\w+\|(\d+)-(\d+)")
_re_strip_key = re.compile(r"\|(\d+-\d+|\+\d+)")
_re_increments = re.compile(r"\w+\|\+(\d+)")
_re_key = re.compile(r"(@[a-zA-Z_0-9\(\),]+)")
_re_numeric_function = re.compile(r"^@(float|int)\(\w+\)")
_re_numeric_function_extract = re.compile(r'^@(?P<function>.*)\((?P<parameter>.*)\)')


FUNC = {
    'float': float,
    'int': int
}


def mock_object(template, increments={}, name=None, **data):
    length = 0

    _data = dict(DATA.items() + data.items())
    if name:
        matches = _re_range.search(name)
        if matches:
            groups = matches.groups()
            length_min = int(groups[0])
            length_max = int(groups[1])
            length = random.randint(length_min, length_max)

    t_type = type(template)
    if t_type is dict:
        generated = {}
        for key, value in template.iteritems():
            # handle increments
            inc_matches = _re_increments.search(key)
            if inc_matches and type(template[key]) is int:
                increment = int(inc_matches.groups()[0])
                if key in increments:
                    increments[key] += increment
                else:
                    increments[key] = 0

            stripped_key = _re_strip_key.sub('', key)
            generated[stripped_key] = mock_object(value, increments, key, **data)
        return generated
    elif t_type is list:
        return [mock_object(template[i], increments, name=None, **data) for i in xrange(len(template))]
    elif t_type is int:
        if name in increments:
            return increments[name]
        else:
            return length if matches else template
    elif t_type is bool:
        # apparently getrandbits(1) is faster...
        return random.choice([True, False]) if matches else template
    # is this always just going to be unicode here?
    elif t_type is str or t_type is unicode:
        if template:
            length = length if length else 1
            generated = ''.join(template for _ in xrange(length))
            if re.search(r'[\w.-]+@[\w.-]+', generated):
                return generated
            matches = _re_key.findall(generated)
            if matches:
                for key in matches:
                    if not _re_numeric_function.match(key):
                        value = _data[key.lstrip('@')]
                        generated = generated.replace(key, value, 1)
                    else:
                        match_groups = _re_numeric_function_extract.match(key)
                        value = _data[match_groups.group('parameter')]
                        if value == 0:
                            generated = FUNC[match_groups.group('function')](value)
                        else:
                            generated = FUNC[match_groups.group('function')](value) if value else None
            return generated
        else:
            return ''.join(random.choice(string.letters) for _ in xrange(length))
    else:
        return template


def mock_json(template, **data):
    return mock_object(template, **data)


class BuilderCollection(list):

    def __init__(self, *args):
        list.__init__(self, *args)

    def singleton(self):
        return self[0]


class BaseBuilder(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.collection = BuilderCollection()

    @abc.abstractmethod
    def build(self):
        raise NotImplementedError(
            "The Base build must be extended with a specific implementation of the functionality needed")
