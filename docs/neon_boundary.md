# Neon Boundary

Issue: #2

Status: Neon target boundary approved. Live execution remains gated by issue #4.

This document records the human decision boundary for future live PostgreSQL work in Neon. It must not contain real credentials or connection-string values.

## Neon project

gdt-tooling-coach

## Database

gdt_tooling_coach

## Connection owner

neondb_owner

The real `DATABASE_URL` value must stay outside version control. Store it only in a local `.env` file or in approved deployment/runtime secrets.

## Allowed live actions

The following actions are allowed only after explicit human approval in GitHub issue #2 or its successor gate issue:

- Run non-destructive migrations that create tables, constraints, indexes, functions, and triggers.
- Create or replace review/export views from `db/views`.
- Run read-only verification queries after migrations.

## Forbidden live actions

Until explicitly approved, all live Neon actions are forbidden.

Always forbidden without separate approval:

- Dropping tables, views, schemas, or databases.
- Truncating or deleting live data.
- Running destructive schema changes.
- Committing credentials or connection-string values.
- Ingesting PDFs or normative source content.

## Human approval

The Neon target boundary was approved by the human on 2026-05-22:

- Neon project: `gdt-tooling-coach`
- Database: `gdt_tooling_coach`
- Connection owner: `neondb_owner`

Live Neon execution still requires an explicit approval comment in GitHub issue #4 or its successor gate issue.

The live execution approval must name:

- Neon project.
- Database.
- Connection owner.
- Allowed live actions.
- Forbidden live actions.
