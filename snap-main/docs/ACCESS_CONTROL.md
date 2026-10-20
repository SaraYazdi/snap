# Access control (functional)

Authorization is **application-enforced** in Phase 2 via a single policy surface. XACML / AuthzForce is **deferred** to Phase 3 and should replace or wrap the same surface without rewriting page controllers.

## Policy surface

```text
can_access(user, content_item, action) -> allow | deny
```

| Argument | Meaning |
|----------|---------|
| `user` | Authenticated principal (or anonymous → deny for non-public future cases) |
| `content_item` | Target resource |
| `action` | `view` \| `stream` \| `download` \| `manage` |

`manage` covers edit metadata, replace/delete file, and change permissions/grants.

Every evaluation that backs a user-facing view/stream/download (and optionally manage) should produce an `access_logs` row.

## Inputs to a decision

```mermaid
flowchart TD
  Start[can_access] --> Deleted{is_deleted}
  Deleted -->|yes| DenyDeleted[deny]
  Deleted -->|no| AdminGrant{admin_with_explicit_grant}
  AdminGrant -->|manage_without_grant| DenyAdminContent[deny_content]
  AdminGrant -->|has_grant| AllowGrant[allow]
  Start --> Role[Resolve_memberships_for_band]
  Role --> Rules[Apply_role_audience_time_grant_rules]
  Rules --> Decision[allow_or_deny]
```

Decision order (recommended):

1. If `content_item.is_deleted` → deny (except future admin recovery tools).
2. If explicit active `content_grants` for `(user, item, action)` within validity window and not revoked → **allow**.
3. If user is `administrator` with no grant → **deny** for content actions (`view`/`stream`/`download`/`manage`). Admins still access Admin Panel and access logs via separate checks.
4. Apply role + audience + time-window rules for the item's `band_id`.
5. Else → deny.

## Role rules (for band SNAP)

Assume memberships are scoped to the content item's band unless noted.

### Administrator

| Capability | Allowed? |
|------------|----------|
| Admin panel, invites, roles | Yes (not via `can_access` on content) |
| View/stream/download band content | Only with explicit grant |
| Manage content | Only with explicit grant |
| View access logs | Yes (all bands) |

### Band Member

| Capability | Allowed? |
|------------|----------|
| `manage` on own band's items | Yes |
| `view` / `stream` / `download` on own band's items | Yes |
| Other bands | No (unless grant or other membership) |

### Crew / Management

| Capability | Allowed? |
|------------|----------|
| Categories oriented to tour/schedule: `schedule`, `setlist`, `tour_rider`, and other items with `audience_level` in (`crew`, `public`) | `view` (and `download` if appropriate) |
| Demos/masters/contracts at `band` / `restricted` | No unless grant |
| `manage` | No |

Exact crew category set: `schedule`, `setlist`, `tour_rider` plus any item with `audience_level = crew`. See [CONTENT_TYPES.md](CONTENT_TYPES.md).

### Press / Partner

| Capability | Allowed? |
|------------|----------|
| Item with `audience_level` in (`press`, `public`) or `is_public` | After press window |
| `audience_level` in (`fan_club`, `crew`, `band`, `restricted`) | No unless grant |
| Time window | `now >= available_from_press` if set; if null, treat as immediately available for press-level items |
| `manage` | No |

### Fan club member

| Capability | Allowed? |
|------------|----------|
| `audience_level` in (`fan_club`, `public`) or `is_public` | After fan window |
| Press-only / crew / band / restricted | No unless grant |
| Time window | `now >= available_from_fans` if set; if null, immediate for fan_club-level items |
| `manage` | No |

### Registered user

| Capability | Allowed? |
|------------|----------|
| `is_public = true` or `audience_level = public` | Yes (`view`; stream/download per product choice — default allow both for public) |
| Everything else | No unless grant |

## Audience level summary

| Audience level | Who gets role-based access (after windows) |
|----------------|--------------------------------------------|
| `public` | Registered+ (and everyone above) |
| `fan_club` | Fan club, band members |
| `press` | Press, band members |
| `crew` | Crew, band members |
| `band` | Band members only |
| `restricted` | Explicit grants only (+ band members who can still `manage`) |

Band members always retain `manage` and full access to their band's items regardless of audience level (they own the catalog).

## Time windows

| Field | Applies to |
|-------|------------|
| `available_from_press` | Press role accessing press-tier (or public) material |
| `available_from_fans` | Fan club accessing fan-tier (or public) material |

Band members and crew (for crew-visible categories) are **not** blocked by press/fan embargo dates unless a future rule says otherwise. Embargoes exist to protect pre-release leaks to press/fans.

## Grants

An active grant allows the specified `action` when:

- `revoked = false`
- `valid_from` is null or `<= now`
- `valid_until` is null or `>= now`

Grants can open access early for a journalist, extend download rights, or give an admin temporary access to one file.

## Separate capability checks (not content `can_access`)

| Capability | Rule |
|------------|------|
| Open Admin Panel | `role = administrator` |
| Invite users | `administrator` |
| Upload new content | `band_member` for target band |
| View access log for item | `administrator` OR `band_member` of item's band |

## Logging

| Event | Log |
|-------|-----|
| Allowed view/stream/download | `outcome = allowed` |
| Denied attempt | `outcome = denied`, set `deny_reason` (e.g. `embargo`, `role`, `restricted`, `deleted`) |
| Manage actions | Optional but recommended |

## Deferred: XACML 3.0 / AuthzForce

Phase 3 may map:

| XACML attribute | Source |
|-----------------|--------|
| Subject | user id, roles, account_type |
| Resource | content id, band, category, audience_level |
| Action | view/stream/download/manage |
| Environment | current time vs availability windows |

Flask would build a request, call AuthzForce, and keep the same `can_access` facade so pages do not change.

Until then: implement rules in Python (or SQL predicates) only. Do not stand up AuthzForce.

## Related docs

- [DATA_MODEL.md](DATA_MODEL.md)  
- [PAGES.md](PAGES.md)  
- [CONTENT_TYPES.md](CONTENT_TYPES.md)  
