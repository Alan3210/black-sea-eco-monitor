AIR-1.4C.1 — Node Test Compatibility Fix v0.1
==============================================

Problem
-------
frontend/package.json runs:

  node --test src/*.test.js

The initial AIR-1.4C test file imported Vitest:

  import { describe, expect, it } from 'vitest';

Vitest is not installed in this project, so npm test failed with:

  ERR_MODULE_NOT_FOUND: Cannot find package 'vitest'

Fix
---
Only the TROPOMI test file is changed.

It now uses built-in Node.js test APIs:

  import { describe, it } from 'node:test';
  import assert from 'node:assert/strict';

No production runtime code is changed.
No new npm dependency is added.

Expected regression
-------------------
Before AIR-1.4C:
  146 pass

After AIR-1.4C.1:
  existing 146 tests + 5 TROPOMI tests
  = 151 pass, 0 fail
