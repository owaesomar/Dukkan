# ADR 0004: Keep product image objects private

- Status: Accepted
- Date: 2026-10-27

## Context

Merchant product images need to be stored outside PostgreSQL and must not be exposed through a client-selected object key or public bucket write.

## Decision

The API accepts only bounded JPEG, PNG, and WebP uploads, determines type from content signatures, creates a random object key under the authenticated store/product path, and writes to an S3-compatible bucket without public ACLs. The database stores object metadata and the uploading user. Authorized merchant reads receive a 15-minute signed GET URL.

## Consequences

S3-compatible credentials and bucket configuration are required for actual uploads. Public product responses use short-lived signed GET URLs; a CDN cache policy remains future work. Image decode/re-encoding, EXIF stripping, deletion lifecycle, and malware scanning are still open hardening work.
