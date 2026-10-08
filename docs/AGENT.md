# AGENT.md — SNAP Records project map

> **Read this first.** Other agents and contributors should start here before changing anything.

## Product (one paragraph)

**SNAP Records** is a private web portal for a single record label. The label shares unreleased recordings (demos, stems, masters), lyrics, setlists, tour riders, contracts, photos, videos, and press kits with band members, crew/management, press/partners, and fans — with access controlled per user, role, band, and time window. The only label in the system is **SNAP Records**. The only roster band for now is **SNAP**. This is not a multi-tenant / multi-label product.

## Phase status

| Area | Status |
|------|--------|
| Design documentation | **Complete** (this `docs/` folder) |
| Application implementation (Flask, UI, DB) | **In progress** — Phase 2 functional app |
| Security features from Delivery 01 | **Deferred** — document only; do not implement yet |

## Source of truth

1. Course brief: [`Delivery 1 AppSec (SNAP)-1.pdf`](../Delivery%201%20AppSec%20(SNAP)-1.pdf) (project root)
2. Design docs in this folder (canonical for product framing, data model, pages, and access rules)
3. If docs and PDF disagree on branding: prefer **SNAP Records** (label) + **SNAP** (band) as framed here

## File index

| Path | What it is |
|------|------------|
| [AGENT.md](AGENT.md) | This file — agent entrypoint, constraints, next steps |
| [PLAN.md](PLAN.md) | Product/tech plan, feature scope, deferred security, roadmap |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component diagram and planned stack |
| [DATA_MODEL.md](DATA_MODEL.md) | ER diagram, tables, fields, relationships, indexes |
| [PAGES.md](PAGES.md) | Page inventory, role availability, user flows |
| [ACCESS_CONTROL.md](ACCESS_CONTROL.md) | Functional access rules; XACML deferred |
| [CONTENT_TYPES.md](CONTENT_TYPES.md) | Content categories and metadata |
| `../Delivery 1 AppSec (SNAP)-1.pdf` | Original Delivery 01 practice report |

## Do

- Keep a **single label**: SNAP Records
- Keep roster assumptions at **SNAP only** for seeds/examples; keep `bands` multi-band-ready in the schema
- Align implementation with [DATA_MODEL.md](DATA_MODEL.md) and [PAGES.md](PAGES.md)
- Put authorization behind a single conceptual surface: `can_access(user, item, action)` (see [ACCESS_CONTROL.md](ACCESS_CONTROL.md))
- Log view / stream / download attempts (allowed and denied) as designed in the access log

## Do not

- Do **not** implement Delivery 01 security features yet: custom TLS CA, OAuth/Google login, XACML/AuthzForce, Argon2/2FA, file encryption at rest, field-level DB encryption, watermarking, Docker secrets for crypto keys
- Do **not** design or build multi-label / multi-tenant tenancy
- Do **not** treat this as a generic public band marketing site; it is a private label content portal
- Do **not** invent parallel schemas or page inventories that diverge from these docs without updating them first

## Next phase (when implementation starts)

1. Scaffold Flask + PostgreSQL from [DATA_MODEL.md](DATA_MODEL.md)
2. Implement pages and flows from [PAGES.md](PAGES.md) with simple session auth (no OAuth/2FA yet)
3. Enforce rules from [ACCESS_CONTROL.md](ACCESS_CONTROL.md) in application code
4. Store uploaded files on a local/Docker volume **unencrypted** for now (encryption deferred)
5. Seed: label = SNAP Records, band = SNAP, sample users per role

## Quick glossary

| Term | Meaning |
|------|---------|
| Label | SNAP Records (singleton in this app) |
| Band | Roster act under the label; currently SNAP |
| Professional account | Invited by admin (band, crew, press, etc.) |
| Fan account | Self-registered (fan club / registered user) |
| Content item | One uploaded resource with category, audience, availability windows |
| Grant | Explicit per-user permission override or extension on a content item |
