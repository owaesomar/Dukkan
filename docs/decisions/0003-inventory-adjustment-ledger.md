# ADR 0003: Record inventory changes as locked adjustments

- Status: Accepted
- Date: 2026-10-27

## Context

Inventory edits need to avoid negative stock under concurrent requests and retain a reason and actor for each manual change.

## Decision

Store one inventory row per store/variant and serialize updates with a PostgreSQL row lock. Apply each signed delta and insert an immutable adjustment record in the same transaction. Database checks prevent negative on-hand/reserved values and reserved quantities above on-hand stock.

## Consequences

Concurrent adjustments and checkout reservations lock inventory rows to prevent overselling. Checkout idempotency prevents duplicate orders for a repeated client key. Payment collection and idempotent payment webhooks remain future work.
