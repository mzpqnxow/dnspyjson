#!/usr/bin/env python3
"""Test driver for dns_answer_to_json"""
import json
import sys
from sys import (stderr, stdout)

import dns.rdtypes.ANY

from dnspyjson import json_dns_query


ALL_Q_TYPES = dns.rdtypes.ANY.__all__


def status(msg):
    # pylint: disable=missing-function-docstring
    stderr.write(msg + '\n')


def output(msg):
    # pylint: disable=missing-function-docstring
    stdout.write(msg + '\n')


def json_resolve_main():
    """Entrypoint for json-resolve"""
    if len(sys.argv) < 2:
        status('Usage: {} <qname> [qtype]\n'.format(sys.argv[0]))
        exit(1)

    q_name = sys.argv[1]
    q_type = 'A' if len(sys.argv) < 3 else sys.argv[2]
    nameservers = sys.argv[3:] if len(sys.argv) > 3 else ['1.1.1.1', '8.8.8.8']

    status('Nameservers')
    status('===========')
    for nameserver in nameservers:
        status('- ' + nameserver)
    if q_type.lower() != 'all':
        obj = json_dns_query(q_name, q_type, nameservers, as_native_object=True)
        if obj is not None:
            output(json.dumps(obj, indent=2))
    else:
        for q_type in ALL_Q_TYPES:
            outfile = 'dns.out/{q_type}_{q_name}.json'.format(q_type=q_type, q_name=q_name)
            obj = json_dns_query(q_name, q_type, nameservers, as_native_object=True, to_file=outfile)
            if obj is not None:
                output(json.dumps(obj, indent=2) + '\n')
