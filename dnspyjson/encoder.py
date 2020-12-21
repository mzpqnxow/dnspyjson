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
        # It's possible another encoding may be preferred, but probably not
        # Maybe ISO-8859-1? Nah, I'm thinking probably not. Meh.
        self._encoding = kwargs.pop('encoding', 'utf-8')
        # Just a way to track the first time `default()` is entered
        self._entered_default = False

        super(DNSEncoder, self).__init__(*args, **kwargs)

    def default(self, *args, **kwargs):  # pylint: disable=unused-argument
        assert args
        if self._entered_default is False:
            # It may (or may not) be useful to know if its the first time that
            # this method has been entered for future logic. Or it may not. But
            # it doesn't cost anything to track, so meh
            self._entered_default = True

        # In practice, *args is always a single-item list I believe. But it's more
        # correct to declare it "properly" as `*args`, even if just to please any
        # linters or static analysis tools that may want a declaration that matches
        # the parent class. This isn't a strict requirement
        assert len(args) == 1
        obj = args[0]

        if isinstance(obj, set):
            obj = list(obj)

        if isinstance(obj, bytes):
            return obj.decode('utf-8')

        if isinstance(obj, dns.rrset.RRset):
            encoded = list()
            # Extract the outer TTL and put it inside each answer
            # Otherwise, we don't see it at all because it's not contained within each
            # Need to look into what (if anything) is in the RRset that we may want to explicitly
            # extract and put somewhere
            ttl = obj.ttl
            for answer in obj.items:
                # There may be a more correct way to do this, without having to directly
                # access the protected method, but I kind of doubt it. I'm not too worried
                # about it, doing it this way allows it to work on any type of Answer
                slots = answer._get_all_slots()  # noqa, pylint: disable=protected-access
                record = {'ttl': ttl}
                for slot in set(slots):
                    value = getattr(answer, slot)
                    # This block intentionally cascades, it doesn't break or return and
                    # the order is important :>

                    if isinstance(value, (set, tuple)):
                        # Could do:
                        # if len(value) == 1:
                        #     value = value[0]
                        # But that would be an arbitrary decision just for cosmetic reasons, and
                        # may have undesired side-effects. This was only considered because Answers
                        # for certain records like TXT pass each "row" of the TXT data as a one item
                        # list. But it's probably a better idea to just leave it alone because of
                        # the high-potential for unintended side-effects. The user can flatten it
                        # later if they really want to
                        value = list(value)

                    if isinstance(value, dns.rdatatype.RdataType):
                        # There's a catch-all at the bottom that uses `to_text()` but might as well
                        # do it here for explicitly known types
                        value = dns.rdatatype.to_text(value)

                    if isinstance(value, bytes):
                        value = value.decode('utf-8')

                    if isinstance(value, list):
                        value = [v.decode('utf-8') for v in value if isinstance(v, bytes)]

                    if hasattr(value, 'to_text'):
                        # Pretty much all of the objects have a `to_text` method, either directly
                        # implemented or inherited from a higher-level class. This is the fallback
                        # and is what makes this whole thing relatively simple
                        value = value.to_text(value)

                    with open('types.out', mode='a') as outfd:
                        outfd.write('{} ({})\n'.format(type(value), str(value)))

                    # Fail
                    if not isinstance(value, self.KNOWN_TYPES):
                        if DEVELOPER_MODE:  # noqa
                            # noqa: Developer can uncomment this case
                            import pdb
                            pdb.set_trace()
                        else:
                            # It would be nice to know about any unexpected data-types as they may not
                            # get encoded correctly. Silently losing data is probably the worst bug
                            # to have in something like this
                            sys.stderr.write('Unexpected datatype {} ({})\n'.format(value.__type__, str(value)))
                            raise RuntimeError('Developer trap. You can remove this if you want, but please enter an issue!')

                    record[slot] = value

                encoded.append(record)

            return encoded

        if hasattr(obj, 'to_text'):
            # It seems like, at this point, any remaining "unknown" object types are classes with a `to_text` method
            # It's the last ditch effort to get the value to a string
            return obj.to_text()

        return json.JSONEncoder.default(self, obj)
