# Implementation Plan

- Add `FrontendRuntimePolicy` with local/production profile validation.
- Wire runtime policy into `fixture_server.py` without changing default fixture behavior.
- Add bearer read-token guard for protected read endpoints when `auth_mode=read-token`.
- Add CLI flags and environment variable defaults for runtime profile, allowed origin, auth mode, and read token env name.
- Add tests for default local behavior, production startup guard, non-loopback guard, and token-protected reads.
- Add runtime boundary verification script.
- Update architecture/runtime docs and roadmap.
- Run fixture server verification, runtime boundary verification, AWH, placeholder scan, and diff check.
