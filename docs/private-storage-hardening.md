# Private storage hardening (source-only)

Reuse:
- Credential persistence: EXTEND: `app/server.py:atomic` and startup `initialize` — keep JSON schema and existing atomic0600 writer; repair all known secret files and `.tinfoil/user_cache_secret` with metadata-only chmod.
- SDK isolation: EXTEND: `worker` and `live.serve` — child umask077; fixed HTTP error logging. Provider keys remain in private stdin pipes, never argv or an API readback.

Based on deployed revision `9a32d0869618`, preserving router-granted realtime and verified Connect behavior. Latest upstream main is not equivalent to this live app lineage. No deployment or installed skill edit.

## Verify

`uv run --no-project --with wsproto==1.2.0 python -m unittest -v test_private_storage`

`uv run --no-project --with wsproto==1.2.0 python -m unittest discover -s tests -p 'test_*.py' -v`

`wsproto` is the same version pinned in requirements. The new tests use synthetic keys only: legacy0777 startup repair with original bytes retained, secret JSON create/replace/failure, actual synthetic child cache creation, fixed exception logs, no full-key status readback and symlink refusal. Official SDK/enclave live attestation is not claimed by these tests.

Local full-suite caveat without npm dependencies: `test_ws_unsupported_format_and_signed_out` returns provider_error rather than unsupported_format. The same failure reproduces at unmodified base9a32d08. The built-image actual SDK test is skipped when the SDK is absent. Do not call the full suite green; stage the pinned image/realtime tests on forum.

## Boundary and release gate

**Modes are hardening, not encryption or same-UID isolation.** The source recipe declares `tinfoil-private-data:/data` as a named volume. The prior cleanup also found secret files under host app-data; do not infer the active engine mount from either fact alone. Active volume-to-host mapping was not independently re-read in this source-only task. Runtipi recursively chmods app-data0777 on lifecycle actions; any binding/rewrite into that tree remains vulnerable even while the app runs. These fixes repair known storage on startup and before/after SDK worker operations, not against concurrent privileged chmod. Verify actual mount placement before claiming lifecycle isolation.

Do not hide existing connection.json under an empty volume. A future custody change must preserve complete original bytes, optional admin key and SDK cache, existing local gateway bearer and grants. Prove actual status/inference/refresh where applicable, rollback to the generation-current value and independent recovery before plaintext removal. No key rotation, broker installation, provider/model change or live restart occurs in this branch. Heavy Docker/browser tests belong on forum.
