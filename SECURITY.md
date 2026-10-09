# Security

Report a suspected vulnerability through the repository's
[private vulnerability reporting page](https://github.com/kebag-logic/tsn-c-stack/security/advisories/new).
If private reporting is unavailable, request a private reporting channel from
the maintainers through the [repository](https://github.com/kebag-logic/tsn-c-stack)
without disclosing the exploit.

Include the affected revision, frame bytes or event sequence, expected behavior
and observed effect. Use synthetic identities and no credentials or private
network captures. The maintainer confirms scope and coordinates a fix.
There is no promised response time or supported release series yet.

The [port contract](docs/PORTING.md) requires serialized calls, valid callback
pointers and bounded transport service. The cores do not provide authentication
or secure random generation. See the [deviations](docs/DEVIATIONS.md).
