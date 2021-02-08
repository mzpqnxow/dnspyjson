## dnspyjson: Seamlessly Serialize dnspython2.x Answers Into JSON or Native Python Objects

This package provides a `json.JSONEncoder` subclass for the standard cPython `json` package that allows a `dnspython>=2` response to be easily converted into a JSON string, native Python objects, or a JSON file. It also includes a public interfaces so you don't need to interact directly with the JSON encoder or even with `dnspython` (optional)

**NOTE**: See the usage examples below; you can not simply pass the JSON encoder class that is implemented in this package directly to `json.dump` using `cls=`

### Requirements

 * Python >= 3.5 (Python2 will not work, Python < 3.5 is not tested; note that PEP-484 type hints are used in this code)
 * dnspython >= 2 (dnspython < 2 will likely not work)

### Supported Answer Types

There aren't any known types that are lacking support at this time, though there are some enhancements to be made (see TODO section)

### Installing

Install master/latest stable:
```
$ pip install 'git+https://github.com/mzpqnxow/dnspyjson@master#egg=dnspyjson'
```

Install a specific release by tag:
```
$ pip install 'git+https://github.com/mzpqnxow/dnspyjson@0.0.8#egg=dnspyjson'
```

You can also use this syntax in `requirements.txt`

### Using In A Project As A setuptools Dependency

Master/latest stable:
```
install_requires = dnspyjson @ git+https://github.com/mzpqnxow/dnspyjson@master#egg=dnspyjson  # Master (latest stable)
```

Pin a specific release by tag:
```
install_requires = dnspyjson @ git+https://github.com/mzpqnxow/dnspyjson@0.0.8#egg=dnspyjson  # Pin to 0.0.8
```

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

If you already have an `dns.resolver.Answer` object from your own direct use of `dnspython`, you can use:

```
from dnspyjson import dns_answer_to_json
...
answer = resolver.resolve(qname, qtype)  # Using dnspython directly
json_string = dns_answer_to_json(answer)  # Returns a Python str containing JSON
native_object = dns_answer_to_json(answer, as_native_object=True)  # A native Python object (list of dict)
dns_answer_to_json(answer, to_file='response.out)  # Ouput the JSON to a file
```

If you don't want to use `dnspython` directly, you can use the `json_dns_query()` wrapper:

```
from dnspyjson import json_dns_query
...
qname = 'test.com'
qtype = 'A'
resolvers = ['1.1.1.1', '8.8.8.8']
result = json_dns_query('test.com', 'TXT', ['4.2.2.2', '8.8.8.8'])
```

All of the `kwargs` values supported by `dns_answer_to_json()` are accepted and passed along by `json_dns_query()`:

```
result = json_dns_query('test.com', 'TXT', ['4.2.2.2', '8.8.8.8'], as_native_object=True)
```

Finally, you can use the CLI app, `json-resolve` (or see the source in `dnspyjson/app.py`) by specifying a specific record type, or using the special type `"ALL"` which will query all of the known record types in succession

```
$ json-resolve test.com TXT | jq '.' -c
Nameservers
===========
- 1.1.1.1
- 8.8.8.8
{"qname":"test.com.","rdtype":16,"rdclass":1,"nameserver":"1.1.1.1","port":53,"chaining_result":{"canonical_name":"test.com.","answer":[{"ttl":3501,"rdclass":"IN","rdtype":"TXT","strings":["google-site-verification=kW9t2V_S7WjOX57zq0tP8Ae_WJhRwUcZoqpdEkvuXJk"]}],"minimum_ttl":3501,"cnames":[]},"canonical_name":"test.com.","rrset":[{"ttl":3501,"rdclass":"IN","rdtype":"TXT","strings":["google-site-verification=kW9t2V_S7WjOX57zq0tP8Ae_WJhRwUcZoqpdEkvuXJk"]}],"expiration":1612744578.296427,"isoformat_expiration":"2021-02-08T00:36:18","request_timestamp":"2021-02-07T23:37:57.296469"}
```

The CLI app is very primitive and is only meant as a test driver. If you would like to use it for very specialized tasks/queries, you will need to modify it. Contributing it back via a Pull Request would be nice of you

### Use-Case(s)

The use-case for development of this was for a simple web application that performed comprehensive DNS interrogation for a domain (e.g. MX, TXT, A, AAAA, ...) and returned them in a pretty printed way in the browser that a user could click into to expand and collapse with Javascript. If you want to do a very, very large amount of queries, you should use a specialized tool like `massdns`- this is meant as a replacement for tools like `dig`, `host` and `nslookup`, or for use as a backend for a web service/application

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

### TODO (Maybe)

- Intelligent handling of certain integer and floating-point values; no compelling use-case for the moment, though maybe at some point it will be useful
  - Detect epoch-times and (optionally) convert them to human-readable date format
  - Detect ttl values and (optionally) convert them from seconds to minutes, hours, days
- Support other `dnspython` data-types (e.g. `QueryMessage`)
  - I don't have any use-case for this currently
- Expand the scope to store responses in PostgreSQL or some none SQL datastore
  - I don't have a use-case for this, and it would be a significant change in scope, from an afternoon project to a week-long project, which I don't have the time for right now