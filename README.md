## dnspyjson: Seamlessly Serialize dnspython2.x Answers Into JSON or Native Python Objects

This package (which started as a Gist, and is really just a glorified Gist, at least for now) provides a `json.JSONEncoder` for the standard cPython `json` package that allows a `dnspython>=2` response to be easily converted into a JSON string, native Python objects, or a JSON file. It also includes a wrapper function that will invoke the JSON serialization properly for you

*NOTE: It is not recommended to use the `json.JSONEncoder` subclass directly as it's not as simple as passing `cls=` to `json.dump()` or `json.dumps()`; use the wrapper unless you need to customize/tweak how it behaves*


### Requirements

 * Python >= 3.5 (Python2, Python < 3.5 not tested)
 * dnspython >= 2 (dnspython < 2 not tested)

### Supported Answer Types

There aren't any known types that are lacking support at this time, though there are some enhancements to be made (see TODO section)

#### Known Working Query Types

Confirmed working against all sorts of different Answer types, including but not limited to:

 - A
 - AAAA
 - CERT
 - SRV
 - NS
 - SOA
 - PTR
 - SPF
 - DNSKEY
 - MX
 - RRSIG
 - TXT

#### Example Pretty Print Output

```
{
  "qname": "walmart.com.",
  "rdtype": 6,
  "rdclass": 1,
  "nameserver": "127.0.0.1",
  "port": 53,
  "canonical_name": "walmart.com.",
  "rrset": [
    {
      "rname": "hostmaster.walmart.com.",
      "minimum": 300,
      "mname": "pdns1.ultradns.net.",
      "refresh": 3600,
      "retry": 3600,
      "expire": 604800,
      "serial": 2016113072,
      "rdclass": 1,
      "rdtype": "SOA"
    }
  ],
  "expiration": 1602519121.0416613
}
```

### Usage

You can just call the wrapper/public interface and pass a `dnspython` `Answer` object as the first argument:

```
import dnspython

answer = resolver.resolve(qname, qtype)
dns_answer_to_json(answer)
```

For more details, see `wrap_query()` in `tests/test.py`

It is recommended that you use that wrapper function `dnspyjson.dns_answer_to_json` as opposed to trying to use the `json.JSONEncoder` subclass () directly. For one, it's not as straightforward as specifying `cls=dnspyjson.DNSEncoder` on an `Answer` object. If you do so, you will be missing the isoformat of the expiration time, though this may not be important to you. You're welcome to do it anyway if you'd like, but model it after the wrapper function to see how to do it properly! Roughly, it looks as follows:

```
    assert isinstance(answer, dns.resolver.Answer)
    # Create some artificial values for prettier output
    answer.__dict__['expiration_isoformat'] = datetime.datetime.utcfromtimestamp(int(answer.expiration)).isoformat()    
    exclude_keys = [] if include_response_blob is True else ['response']
    structured_answer_string = json.dumps(
        {k: v for k, v in answer.__dict__.items() if k not in exclude_keys},
        cls=DNSEncoder, **kwargs)
```

### Use-Case(s)

The use-case for development of this was for a simple web application that performed comprehensive DNS interrogation for a domain (e.g. MX, TXT, A, AAAA, ...) and returned them in a pretty printed way in the browser that a user could click into to expand and collapse with Javascript. There are plenty of other uses

#### Example Use-Cases

* Storage of JSON directly into a PostgreSQL JSONB column, to sidestep the need to create a complex schema capable of properly storing all different types of answers
* Render JSON as a response in a web application that performs DNS lookups as part of its functionality
* Conversion into `pandas.DataFrame` objects, where large-scale analysis/processing can be done efficiently
* Conversion into native Python objects, if that's more comfortable for you (that's a pretty lame one)

### Example Applications: PostgreSQL: Creating indexes and querying `JSONB` (structured JSON) columns in PostgreSQL >= 9.2

PostgreSQL supported `JSON` columns for quite some time, but there wasn't much value as the data wasn't indexable. The addition of `JSONB` to PostgreSQL 9.2 was a game-changer as it allowed JSON objects to be easily stored as well as efficiently indexed and searched as if the keys were predefined columns. You can refer [here](https://www.postgresql.org/docs/9.4/datatype-json.html) for some information on the difference between `JSON` and `JSONB` in PostgreSQL

What follows are a few *very* brief example of how you can use `JSONB` columns in PostgreSQL to store and then search on DNS data. For comprehensive reference covering the syntax for accessing deeply nested, how to operate on arrays/lists and anything else you can think of, see the PostgreSQL 'JSONB' documentation [here](https://www.postgresql.org/docs/current/functions-json.html)

#### Create a very basic table with a `JSONB` column

Create a table with an auto-incrementing ID, a creation timestamp, and a `JSONB` column to store the JSON data in an indexable way:

```
CREATE TABLE dns_answer (
    id BIGSERIAL PRIMARY KEY,
    queried_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answer JSONB);
```

#### Create a few simple indexes on 'JSONB' columns

Create an index on the creation timestamp and one across both the creation timestamp and the canonical name from the answer, to optimize queries using those columns

```
CREATE INDEX dns_answer_data_queried_ts_idx ON dns_answer (queried_ts);
CREATE INDEX dns_answer_data_queried_ts_canonical_name_idx ON dns_answer (queried_ts, (data->>'canonical_name'));
```

You can create alternate index types such as `GiST` and `GIN` indexes on specific keys within the 'JSONB' column as well. Dealing with the 'JSONB' column is much like dealing with a table.

#### Make some simple queries on 'JSONB' columns using indexes


```
SELECT * FROM dns_answer WHERE data->>'canonical_name' = 'somesite.com';
SELECT data->>'canonical_name', data->>'rrset' FROM dns_answer WHERE queried_ts
```

For more advanced queries, see PostgreSQL documentation [here](https://www.postgresql.org/docs/current/functions-json.html)

### TODO

- Intelligent handling of certain integer and floating-point values using simple heuristics; no compelling use-case for the moment, though maybe at some point it will be useful
  - Detect epoch-times and (optionally) convert them to human-readable date format
  - Detect ttl values and (optionally) convert them from seconds to minutes, hours, days
- Support other `dnspython` datatypes (e.g. `QueryMessage`); I don't have any use-case for this, so I don't see the value in even looking into it
- Expand the scope to store responses in PostgreSQL or some none SQL datastore; I don't have a compelling use-case for this, and it would be a significant change in scope, from an afternoon project to a week-long project, which I don't have the time for right now