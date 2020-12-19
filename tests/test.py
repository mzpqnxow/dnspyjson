#!/usr/bin/env python3
"""Test driver for dns_answer_to_json"""
import json
import sys

import dns
import dns.rdtypes.ANY

from dnspyjson import dns_answer_to_json

ALL_Q_TYPES = dns.rdtypes.ANY.__all__


def wrap_query(qname, qtype, nameservers=None, *args, **kwargs):
    try:
        resolver = dns.resolver.Resolver(configure=nameservers is None)
        if nameservers is not None:
            resolver.nameservers = nameservers
        print(resolver.nameservers)
        answer = resolver.resolve(qname, qtype)
        return dns_answer_to_json(answer, *args, **kwargs)
    except (dns.exception.Timeout, dns.resolver.NoAnswer, dns.resolver.NoMetaqueries, dns.resolver.NoNameservers, dns.resolver.NXDOMAIN) as err:
        print(err.args[0])
        return None


def main():
    """Some simple tests"""
    if len(sys.argv) < 2:
        print('Usage: {} <qname> [qtype]'.format(sys.argv[0]))
        exit(1)

    q_name = sys.argv[1]
    q_type = 'A' if len(sys.argv) < 3 else sys.argv[2]
    nameservers = sys.argv[3:] if len(sys.argv) > 3 else ['1.1.1.1', '8.8.8.8']

    print('Nameservers')
    print('===========')
    for nameserver in nameservers:
        print('- {}'.format(nameserver))
    if q_type.lower() != 'all':
        obj = wrap_query(q_name, q_type, nameservers, as_native_object=True)
        if obj is not None:
            print(json.dumps(obj, indent=2))
    else:
        for q_type in ALL_Q_TYPES:
            outfile = 'dns.out/{q_type}_{q_name}.json'.format(q_type=q_type, q_name=q_name)
            obj = wrap_query(q_name, q_type, nameservers, as_native_object=True, to_file=outfile)
            if obj is not None:
                print(json.dumps(obj, indent=2))


if __name__ == '__main__':
    main()
