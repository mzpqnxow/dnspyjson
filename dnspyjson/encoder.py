"""Specialized json.JSONEncoder class for serializing dns.resolver.Answer objects

Don't use this directly, you should use dnspyjson.answer_to_json

(C) 2020, copyright@mzpqnxow.com
"""
import json
import sys

import dns
import dns.name
import dns.resolver
import dns.rrset
import dns.rdatatype

DEVELOPER_MODE = False


class DNSEncoder(json.JSONEncoder):
    """JSON serialize dnspython answers"""
    KNOWN_TYPES = (set, bytes, tuple, list, str, int, float, dns.name.Name, dns.rdataclass.RdataClass)

    def __init__(self, *args, **kwargs):
        """Constructor to facilitate "enhanced" decoding of certain datatypes based on Answer rdtype

        Allow passing `enhanced_decode` as kwarg to communicate if "enhanced" decode should be
        performed on the Answer/RRsets

        What is "enhanced" decoding? This will most likely facilitate parsing of certain fields
        in certain types of well-known records that may not be straightforward without knowing
        the answer type

        An example, you say? Howe about TXT answers to parse, e.g. an SPF record?
        Or certain types of records that have epoch-time values in them, that can be detected
        with some basic heuristics, but would be better off with this extra contextual data

        Make sure that those two `kwargs` are popped off of the `kwargs` dict so they don't confuse
        the `json.JSONEncoder` constructor (that's why they're handled *before* `super()` is called
        """
        self._enhanced_decode = kwargs.pop('enhanced_decode', False)
        self._include_rdcomment = kwargs.pop('include_rdcomment', False)
        self._skipkeys = {'rdcomment'} if self._include_rdcomment is False else {}
        # It's possible another encoding may be preferred, but probably not
        # Maybe ISO-8859-1? Nah, I'm thinking probably not
        self._encoding = kwargs.pop('encoding', 'utf-8')
        # Just a way to track the first time `default()` is entered
        self._entered_default = False
        super(DNSEncoder, self).__init__(*args, **kwargs)


    def _simple_encode(self, obj):

        if isinstance(obj, (int, str, bool)):
            return obj

        if isinstance(obj, bytes):
            return obj.decode('utf-8')

        if isinstance(obj, (set, list, tuple)):
            # This works fine for now but theoretically it probably makes
            # more sense treating a length two tuple as a one member dictionary
            # Others should definitely just become lists. For now, everything
            # becomes a list
            return [self._simple_encode(o) for o in obj]

        if isinstance(obj, dict):
            return {k: self._simple_encode(v) for k, v in obj.items() if k not in self._skipkeys}

        if isinstance(obj, dns.rrset.RRset):
            return self._encode_rrset(obj)

        if hasattr(obj, 'to_text'):
            print(type(obj))
            return obj.to_text()

        return json.JSONEncoder.default(self, obj)

    def _encode_rrset(self, obj):
        encoded = list()
        # Extract the outer TTL and put it inside each answer
        # Otherwise, we don't see it at all because it's not contained within each
        # Need to look into what (if anything) is in the RRset that we may want to explicitly
        # extract and put somewhere
        ttl = obj.ttl
        for answer in obj.items:
            slots = answer._get_all_slots()  # noqa, pylint: disable=protected-access
            record = {
                'ttl': ttl}
            for slot in set(slots):
                if slot in self._skipkeys:
                    # Skip rdcomment
                    continue
                value = getattr(answer, slot)
                # This block intentionally cascades, it doesn't break or return and the order is important

                if isinstance(value, (set, tuple)):
                    value = list(value)

                if isinstance(value, dns.rdatatype.RdataType):
                    # There's a catch-all at the bottom that uses `to_text()` but it's done here explicitly
                    # for known types
                    value = dns.rdatatype.to_text(value)
                    if value is None:
                        # Not 100% sure this should be fatal, doesn't seem to happen
                        raise RuntimeError

                if isinstance(value, bytes):
                    value = value.decode('utf-8')

                if isinstance(value, list):
                    value = [v.decode('utf-8') for v in value if isinstance(v, bytes)]

                if hasattr(value, 'to_text'):
                    # Most of the main/common objects have a `to_text` method, either directly
                    # implemented or inherited from a higher-level class. This is the fallback
                    # and is what makes this whole thing relatively simple
                    value = value.to_text(value)

                # Fail: If not excluding rdcomment, you may hit this block with a None
                # value. That would be ok/expected, but you'll have to change this to permit
                # it. I prefer keeping it strict right now
                if not isinstance(value, self.KNOWN_TYPES):
                    if DEVELOPER_MODE:  # noqa
                        # noqa: Developer can uncomment this case
                        import pdb
                        pdb.set_trace()
                        pass
                    else:
                        # It would be nice to know about any unexpected data-types as they may not
                        # get encoded correctly. Silently losing data is probably the worst bug
                        # to have in something like this
                        print(type(obj))
                        print(obj)
                        sys.stderr.write('Unexpected datatype {} ({})\n'.format(value.__type__, str(value)))
                        raise RuntimeError(
                            'Developer trap. You can remove this if you want, but please enter an issue!')

                record[slot] = value

            encoded.append(record)

        return encoded

    def default(self, *args, **kwargs):  # pylint: disable=unused-argument
        assert args
        if self._entered_default is False:
            # It may (or may not) be useful to know if its the first time that
            # this method has been entered for future logic. Or it may not. But
            # it doesn't cost anything to track while I'm thinking about it
            self._entered_default = True

        assert len(args) == 1
        obj = args[0]

        if hasattr(dns.message, 'ChainingResult'):
            if isinstance(obj, dns.message.ChainingResult):
                return self._simple_encode(obj.__dict__)

        if isinstance(obj, dns.rrset.RRset):
            return self._encode_rrset(obj)

        return self._simple_encode(obj)
