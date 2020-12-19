#!/usr/bin/env python3
"""Test driver for dns_answer_to_json"""
import json
import sys
from dnspyjson import dns_answer_to_json


def main():
    if 3 < len(argv) < 2:
        print('Usage: {} <qname> [qtype]'.format(argv[0]))
        exit(1)

    qtype = 'A' if len(argv) != 3 else argv[2]

    if qtype == 'ALL':
        exit(1)

    answer = dns.resolver.resolve(qname, qtype)
    obj = dns_answer_to_json(answer, as_native_object=False)
    print(json.dumps(obj, indent=2))


if __name__ == '__main__':
    main()
