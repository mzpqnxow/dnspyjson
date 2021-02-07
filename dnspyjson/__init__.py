"""Convenient wrapper around the dnspyjson.encoder.DNSEncoder

Call dnspython_answer_json with a dns.resolver.Answer() and it will automatically
invoke json.dumps with the custom serializer

(C) 2020, copyright@mzpqnxow.com
"""
import datetime
import json
import os
from typing import Dict, Iterable, Optional, Union
from sys import stderr
import dns.resolver
from dns.resolver import Answer

from dnspyjson.encoder import DNSEncoder


def dns_answer_to_json(answer: Answer,
                       include_response_blob: bool = False,
                       as_native_object: bool = False,
                       include_rdcomment: bool = False,
                       to_file: Optional[str] = None, **kwargs) -> Union[dict, str]:
    """Serialize a dnspython Answer into JSON or a native Python object, optionally writing to a file

    :param answer: Answer from a dnspython query
    :type answer: dns.resolver.Answer
    :param include_response_blob: Include the string representation of the answer from dnspython
    :type include_response_blob: bool
    :param as_native_object: Return a native Python object instead of a JSON string
    :param to_file: Write the JSON string to a file
    :type to_file: (None, str)
    :param kwargs: Optional keyword arguments to pass to json.dumps (e.g. indent=2)
    :type kwargs: dict
    :return: A serialized representation of the answer to be used as JSON or a native Python object
    :rtype: dict if `as_native_object` is True, otherwise str
    :param include_rdcomment: Include the rdcomment field, which will usually be null except in special cases
    :type include_rdcomment: bool

    Notes
    -----
    By default, include_response_blob is set to False. This filters out the `response` attribute
    from the dns.resolver.Answer object. This attribute is an unstructured string representation
    of the Answer object and is of little value alongside a structured representation. If you
    really want to have it in the output, you can set `include_response_blob=True`

    By default, you'll get a Python str type containing valid JSON as a return value. You can
    override this an receive a native Python object by setting `as_native_object=True`

    If you would like to save the JSON string to a file, set `to_file` to a str value with
    the path to the file to be created"""

    if not isinstance(answer, Answer):
        raise TypeError('Argument must be a dns.resolver.Answer from dnspython>=2 (not %s)' % type(answer))

    exclude_keys = [] if include_response_blob is True else ['response']

    # Create some artificial values for prettier output
    # Assigning attributes to objects you don't define yourself is a
    # pretty poor practice, so eyes wide open :>
    answer.__dict__['isoformat_expiration'] = datetime.datetime.utcfromtimestamp(int(answer.expiration)).isoformat()
    answer.__dict__['request_timestamp'] = datetime.datetime.utcnow().isoformat()

    structured_answer_string = json.dumps(
        {k: v for k, v in answer.__dict__.items() if k not in exclude_keys},
        cls=DNSEncoder, enhanced_decode=True, include_rdcomment=include_rdcomment, **kwargs)

    if to_file is not None:
        try:
            with open(to_file, mode='w') as outfd:
                outfd.write(structured_answer_string)
        except OSError as err:
            stderr.write('ERROR: While writing file ({})\n'.format(os.strerror(err.errno)))
            stderr.write('WARN:  Unable to write file {}, returning {} result from function anyway\n'.format(
                to_file, 'string' if as_native_object is False else 'Python object'))
            raise

    if as_native_object is True:
        return json.loads(structured_answer_string)

    return structured_answer_string


def json_dns_query(qname: str, qtype: str, resolvers: Optional[Iterable[str]] = None, **kwargs) -> Optional[Union[Dict, str]]:
    """Simple interface for a DNS query

    >>> from dnspyjson import json_dns_query
    >>> json_dns_query('test.com', 'TXT', ['4.2.2.2', '8.8.8.8'])

    """
    try:
        resolver = dns.resolver.Resolver(configure=resolvers is None)
        if resolvers is not None:
            resolver.nameservers = resolvers
        answer = resolver.resolve(qname, qtype)
        return dns_answer_to_json(answer, **kwargs)
    except (dns.exception.Timeout, dns.resolver.NoAnswer, dns.resolver.NoMetaqueries,
            dns.resolver.NoNameservers, dns.resolver.NXDOMAIN) as err:
        stderr.write('Failed query with type={}, name={}, resolvers={} ({})\n'.format(
            qtype, qname, ', '.join(resolvers) if resolvers else 'system', err))
        return None


from ._version import get_versions  # noqa, pylint: disable=wrong-import-position
__version__ = get_versions()['version']
del get_versions
