import json
import sys
from datetime import datetime
from time import mktime

from osmread.parser import Parser
from osmread.elements import Node, Way, Relation, RelationMember

# Support for Python 3.x & 2.x
if sys.version_info > (3,):
    long = int
    unicode = str


# TODO use streaming JSON parser like https://pypi.org/project/jsonslicer/ instead of reading the whole JSON file into memory
class JsonParser(Parser):

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)
        self._compression = kwargs.get('compression', None)

    def parse(self, fp):
        d = json.load(fp)
        de = d["elements"]

        # common
        _type = None
        _id = None
        _version = None
        _changeset = None
        _timestamp = None
        _uid = None
        _tags = None
        # node only
        _lon = None
        _lat = None
        # way only
        _nodes = None
        # relation only
        _members = None

        for elem in de:
            tag = elem["type"]
            attrs = elem

            if tag in ('node', 'way', 'relation'):
                _id = long(attrs['id'])
                try:
                    _version = int(attrs['version'])
                except:
                    _version = 0

                try:
                    _changeset = int(attrs['changeset'])
                except:
                    _changeset = 0

                # TODO: improve timestamp parsing - dateutil too slow
                try:
                    _tstxt = attrs['timestamp']
                    _timestamp = int((
                                             datetime(
                                                 year=int(_tstxt[0:4]),
                                                 month=int(_tstxt[5:7]),
                                                 day=int(_tstxt[8:10]),
                                                 hour=int(_tstxt[11:13]),
                                                 minute=int(_tstxt[14:16]),
                                                 second=int(_tstxt[17:19]),
                                                 tzinfo=None
                                             ) - datetime(
                                         year=1970,
                                         month=1,
                                         day=1,
                                         tzinfo=None
                                     )
                                     ).total_seconds())
                except:
                    _timestamp = 0

                try:  # An object can miss an uid (when anonymous edits were possible)
                    _uid = int(attrs['uid'])
                except:
                    uid = 0

                _tags = {}

                if tag == 'node':
                    _type = Node
                    _lon = float(attrs['lon'])
                    _lat = float(attrs['lat'])
                elif tag == 'way':
                    _type = Way
                    _nodes = []
                elif tag == 'relation':
                    _type = Relation
                    _members = []

            if "tags" in elem:
                _tags = elem["tags"]

            if "nodes" in elem:
                _nodes = [long(x) for x in elem["nodes"]]

            if 'members' in elem:
                for m in elem["members"]:
                    _members.append(
                        RelationMember(
                            unicode(m['role']),
                            {
                                'node': Node,
                                'way': Way,
                                'relation': Relation
                            }[m['type']],
                            long(m['ref'])
                        )
                    )

            args = [
                _id, _version, _changeset,
                _timestamp, _uid, _tags
            ]

            if tag == 'node':
                args.extend((_lon, _lat))

            elif tag == 'way':
                args.append(tuple(_nodes))

            elif tag == 'relation':
                args.append(tuple(_members))

            yield _type(*args)
