"""Specialized json.JSONEncoder class for serializing dns.resolver.Answer objects

Don't use this directly, you should use dnspyjson.answer_to_json

(C) 2020, copyright@mzpqnxow.com
"""
import json
from sys import stderr
from typing import Any, Dict, List

import dns
import dns.name
import dns.rdatatype
import dns.resolver
import dns.rrset
from dns.rdatatype import RdataType
from dns.rrset import RRset


DEVELOPER_MODE = False


class DNSEncoder(json.JSONEncoder):
    """JSON serialize dnspython answers"""
    KNOWN_TYPES = (set, bytes, tuple, list, str, int, float, dns.name.Name, dns.rdataclass.RdataClass)

    def __init__(self, *args, **kwargs):
        """Constructor to facilitate "enhanced" decoding of certain datatypes based on Answer rdtype

        Allow passing `enhanced_decode` as kwarg to communicate if "enhanced" decode should be
        performed on the Answer/RRset list

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
        super().__init__(*args, **kwargs)

    # pylint: disable=too-many-return-statements, too-many-branches
    def _robust_encode(self, obj: Any) -> Any:
        """Versatile serializer/encoder for most types to JSON, tuned to handle dnspython types/patterns"""

        if isinstance(obj, (int, str, bool)):
            return obj

        if isinstance(obj, bytes):
            return obj.decode('utf-8')

        if isinstance(obj, (set, list, tuple)):
            # This works fine for now but theoretically it probably makes
            # more sense treating a length two tuple as a one member dictionary
            # Others should definitely just become lists. For now, everything
            # becomes a list
            return [self._robust_encode(o) for o in obj]

        if isinstance(obj, dict):
            return {k: self._robust_encode(v) for k, v in obj.items() if k not in self._skipkeys}

        if isinstance(obj, RRset):
            return self._encode_rrset(obj)

        if hasattr(obj, 'to_text'):
            # This should always produce what we want, but leave this note
            # for later troubleshooting / development
            if DEVELOPER_MODE is True:
                stderr.write('Developers Note: Type is {}\n'.format(type(obj)))
            return obj.to_text()

        return json.JSONEncoder.default(self, obj)

    def _encode_rrset(self, obj: RRset) -> List[Dict]:
        """Convert and RRset into a list of dicts consisting of native Python types so it can serialized

        Notes
        -----
        This function cascades in some spots so pay close attention to what is if/elif vs if/fall-through
        """
        if not isinstance(obj, RRset):
            raise TypeError('Expected RRset, got type {}'.format(type(obj)))

        encoded = list()
        # Extract the outer TTL and put it inside each answer
        # Otherwise, we don't see it at all because it's not contained within each
        # Need to look into what (if anything) is in the RRset that we may want to explicitly
        # extract and put somewhere
        ttl = obj.ttl
        for answer in obj.items:
            slots = answer._get_all_slots()  # noqa, pylint: disable=protected-access
            record = {'ttl': ttl}
            for slot in set(slots):

                if slot in self._skipkeys:
                    # Skip some attributes/keys; for example, `rdcomment`
                    continue

                value = getattr(answer, slot)

                if isinstance(value, RdataType):
                    # There's a catch-all at the bottom that uses `to_text()` that would
                    # catch this, but it's a known type so do it explicitly here to serve
                    # as documentation/reference
                    pre_value = value  # Just for error reporting
                    value = dns.rdatatype.to_text(value)
                    if value is None:
                        # Not 100% sure this should be fatal, doesn't seem to ever happen
                        raise ValueError('Unexpected None value when converting {} to text using to_text()'.format(pre_value))
                elif isinstance(value, (set, tuple)):
                    value = list(value)
                elif isinstance(value, bytes):
                    value = value.decode('utf-8')

                if isinstance(value, list):
                    value = [v.decode('utf-8') for v in value if isinstance(v, bytes)]

                # Don't make this an elif, the dnspython may extend list and then we'll be sunk
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
                        import pdb  # pylint: disable=import-outside-toplevel
                        pdb.set_trace()
                    else:
                        # It would be nice to know about any unexpected data-types as they may not
                        # get encoded correctly. Silently losing data is probably the worst bug
                        # to have in something like this
                        stderr.write('Unexpected datatype {} ({})\n'.format(type(value), str(value)))
                        stderr.write('Developer debug trap. You can remove this if you want, but please enter an issue\n')

                record[slot] = value
            encoded.append(record)

        return encoded

    def default(self, *args, **kwargs) -> Any:  # pylint: disable=unused-argument
        """The highest level encoding class, only handling ChainingResult and RRset as special"""
        if not args:
            raise ValueError('Unexpected empty *args tuple!')

        if self._entered_default is False:
            # It may (or may not) be useful to know if its the first time that
            # this method has been entered for future logic. It doesn't cost much
            # to track it for now just in case it proves useful later
            self._entered_default = True

        if len(args) != 1:
            raise ValueError('Unexpected length for *args tuple: {}, expected 1 ({})'.format(len(args), str(args)))

        obj = args[0]

        # dnspython 2.0.0 did not have this type, only RRset needed to be handled
        # Safely check for it and handle it correctly
        if hasattr(dns.message, 'ChainingResult'):
            if isinstance(obj, dns.message.ChainingResult):
                return self._robust_encode(obj.__dict__)

        if isinstance(obj, RRset):
            return self._encode_rrset(obj)

        # Fallback to the more versatile encoding method
        return self._robust_encode(obj)
