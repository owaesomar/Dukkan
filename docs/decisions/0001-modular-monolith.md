# ADR 0001: Start with a modular monolith

- Status: Accepted
- Date: 2026-10-27

## Context

Dukkan is an early product with closely related commerce workflows. Independent services would add deployment, data consistency, and operational costs before scale or team boundaries justify them.

## Decision

Use one FastAPI application and one React application, organized into business modules. Keep persistence in shared PostgreSQL with explicit tenant ownership and constraints. Extract services only when measured operational needs justify it.

## Consequences

The product can be developed and deployed simply while retaining module boundaries. Tenant isolation must be explicit in every module and reinforced by database constraints and tests.
