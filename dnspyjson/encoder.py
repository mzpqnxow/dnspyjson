"""Specialized json.JSONEncoder class for serializing dns.resolver.Answer objects

Don't use this directly, you should use dnspyjson.answer_to_json

(C) 2020, copyright@mzpqnxow.com
"""
import json

import dns
import dns.resolver
import dns.rrset
import dns.rdatatype


class DNSEncoder(json.JSONEncoder):
    """JSON serialize dnspython answers"""
    def default(self, *args, **kwargs):  # pylint: disable=unused-argument
        assert args

        obj = args[0]
        if isinstance(obj, set):
            obj = list(obj)

        if isinstance(obj, bytes):
            return obj.decode('utf-8')

        if isinstance(obj, dns.rrset.RRset):
            encoded = list()
            for answer in obj.items:
                # There may be a more correct way to do this, without having to directly
                # access the protected method, but I kind of doubt it. I'm not too worried
                # about it, doing it this way allows it to work on any type of Answer
                slots = answer._get_all_slots()  # noqa, pylint: disable=protected-access
                record = {}
                for slot in set(slots):
                    value = getattr(answer, slot)
                    # This block intentionally cascades, it doesn't break or return and
                    # the order is important :>

                    if isinstance(value, (set, tuple)):
                        # It may make sense to do:
                        # if len(value) == 1:
                        #     value = value[0]
                        # But that would be an arbitrary decision just for cosmetic purposes
                        # and could make programmatic processing unpredictable later on. TXT
                        # records are always a single item list in practice, so you *could*
                        # flatten the list out to a scalar string, but that's up to you. It
                        # seems prudent to stay true to the original structure
                        value = list(value)

                    if isinstance(value, dns.rdatatype.RdataType):
                        value = dns.rdatatype.to_text(value)

                    if isinstance(value, bytes):
                        value = value.decode('utf-8')

                    if isinstance(value, list):
                        value = [v.decode('utf-8') for v in value if isinstance(v, bytes)]

                    record[slot] = value

                encoded.append(record)
            return encoded

        if hasattr(obj, 'to_text'):
            # All Answer objects have a `to_text` method
            return obj.to_text()

        return json.JSONEncoder.default(self, obj)
