# Security Policy

## Supported Versions

The following versions of `redlock-ng` are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

Distributed locking is a critical component of many systems. If you discover a security vulnerability in `redlock-ng`, please report it responsibly.

**Do not open a public issue.**

Instead, please email **vivekdagar212@gmail.com** with a description of the vulnerability. I will attempt to respond within 48 hours.

### Critical Considerations
Please note that the [Redlock algorithm itself](https://redis.io/docs/manual/patterns/distributed-locks/) has known limitations regarding clock drift and timing guarantees. Issues inherent to the algorithm design should be discussed on the Redis mailing list or documentation, whereas implementation bugs in this library are valid security reports.
