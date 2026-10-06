# InsightForge AI database and Alembic repair

**Date:** 2026-09-26  
**Scope:** SQLAlchemy persistence models, database metadata/session setup, Alembic environment and revisions. No frontend code was changed. No revision IDs were changed or removed.

> Historical audit snapshot: the migration head below describes the repository
> as inspected on 2026-09-26. The current repository has one later head,
> `20261001_student_verification`; see the current verification results in
> [FINAL_VERIFICATION.md](FINAL_VERIFICATION.md). Historical migration IDs and
> results below are retained as records of that earlier audit.

## Outcome

- The migration graph has one head: `42420889e6ec`.
- `alembic upgrade head` succeeded against a newly created, empty PostgreSQL 16 database.
- `alembic check` reported `No new upgrade operations detected` on both the fresh database and a populated database upgraded from revision `48e8bbad6175`.
- A populated legacy billing schema at `20240901abc12` converted its subscription/status and notification values to enums while retaining subscription, payment, and notification rows.
- The populated-database test preserved a user, dataset and analysis. The dataset's null `uploaded_at` was safely backfilled; the Analysis received `summary_text = ''` and `quality_score = 100`.
- A separate null-owner test stopped with an actionable error and left both the row and Alembic revision unchanged. No owner was invented.
- The fresh database contained the three expected enum types once each: `plan_type`, `subscription_status`, and `notification_type`.

These PostgreSQL tests ran on disposable local databases in an ephemeral PostgreSQL 16 container bound to loopback. They are not a test against a deployed or production database.

## Migration graph

```text
48379796b0ac  users (root)
└── 68daab538788  datasets (initial)
    └── 3523d78a50b6  datasets.rows, datasets.columns
        └── f957ba39a00d  historical no-op
            └── 48e8bbad6175  analyses (initial)
                └── c29672287d79  historical no-op
                    └── f259af705ecd  analyses.summary_text
                        └── 0179eb8e1705  analyses.quality_score
                            ├── a1b2c3d4e5f6  professional analysis fields ───┐
                            └── c2cdee296c8e  chat tables; dataset repair     │
                                └── 55aa91c462ea  users.profile_picture ──────┴── 658de0610bd9  merge
                                                                               └── 20240901abc12  subscriptions,
                                                                                   payment_history, notifications
                                                                                   └── 42420889e6ec  billing reconciliation (head)
```

The two branch parents of merge revision `658de0610bd9` are `55aa91c462ea` and `a1b2c3d4e5f6`. `f957ba39a00d` and `c29672287d79` are retained as historical no-op revisions; the merge revision is also intentionally schema-neutral. These revisions remain in place to preserve deployed databases' revision ancestry.

## Analysis migration verification

The `Analysis` model is in [`backend/app/models/analysis.py`](../backend/app/models/analysis.py). Its original fields are created by `48e8bbad6175`. `c29672287d79` is a no-op; `f259af705ecd` actually adds `summary_text`; `0179eb8e1705` actually adds `quality_score`; and `a1b2c3d4e5f6` adds the six nullable professional-analysis fields. The merge revision and billing migration do not add Analysis columns.

The confusing historical filenames/docstrings have been clarified without changing revision IDs or filenames. Non-null columns use temporary server defaults during `ADD COLUMN`, so pre-existing Analysis rows are backfilled; the defaults are then removed to leave runtime default behavior aligned with the model.

## Column-by-column model and migration audit

**Default notation:** “Python default” means SQLAlchemy applies it when constructing/inserting through the ORM; it is not necessarily a database server default. Server defaults are identified separately. `NOT NULL`/`NULL` refer to the final model/schema. Indexes and foreign keys are noted in the status where useful.

### `users`

Model: [`backend/app/models/user.py`](../backend/app/models/user.py). Table is created by `48379796b0ac`; `profile_picture` is added by `55aa91c462ea`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `48379796b0ac` | NOT NULL; no default | Match |
| `full_name` | `String(100)` | `48379796b0ac` | NOT NULL; no default | Match |
| `email` | `String(255)`, unique, indexed | `48379796b0ac` | NOT NULL; no default | Match; unique index |
| `hashed_password` | `String(255)` | `48379796b0ac` | NOT NULL; no default | Match |
| `profile_picture` | `String(500)` | `55aa91c462ea` | NULL; no default | Match |
| `is_active` | `Boolean` | `48379796b0ac` | NOT NULL; Python default `True` | Match; no server default |
| `is_superuser` | `Boolean` | `48379796b0ac` | NOT NULL; Python default `False` | Match; no server default |
| `created_at` | `DateTime` | `48379796b0ac` | NOT NULL; Python default `datetime.utcnow` | Match; no server default |
| `updated_at` | `DateTime` | `48379796b0ac` | NOT NULL; Python default/on-update `datetime.utcnow` | Match; no server default |

### `datasets`

Model: [`backend/app/models/dataset.py`](../backend/app/models/dataset.py). Table is created by `68daab538788`; `rows` and `columns` are added by `3523d78a50b6`; `c2cdee296c8e` backfills/enforces required fields and replaces the owner foreign key.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `68daab538788` | NOT NULL; no default | Match |
| `filename` | `String(255)` | `68daab538788` | NOT NULL; no default | Present; initial PostgreSQL column is unbounded `VARCHAR`, which is wider than the model |
| `original_filename` | `String(255)` | `68daab538788` | NOT NULL; no default | Present; initial PostgreSQL column is unbounded `VARCHAR`, which is wider than the model |
| `file_type` | `String(20)` | `68daab538788` | NOT NULL; no default | Present; initial PostgreSQL column is unbounded `VARCHAR`, which is wider than the model |
| `file_size` | `Integer` | `68daab538788` | NOT NULL; no default | Match |
| `file_path` | `String(500)` | `68daab538788` | NOT NULL; no default | Present; initial PostgreSQL column is unbounded `VARCHAR`, which is wider than the model |
| `rows` | `Integer` | `3523d78a50b6` | NOT NULL; Python default `0`; migration server default `0` | Present once; no data rewrite |
| `columns` | `Integer` | `3523d78a50b6` | NOT NULL; Python default `0`; migration server default `0` | Present once; no data rewrite |
| `uploaded_at` | `DateTime` | `68daab538788` | NOT NULL; Python default `datetime.utcnow` | Initially nullable; `c2cdee296c8e` backfills nulls with `CURRENT_TIMESTAMP` before enforcing NOT NULL |
| `owner_id` | `Integer`, FK to `users.id`, `ON DELETE CASCADE` | `68daab538788` | NOT NULL; no default | Initially nullable/no cascade; `c2cdee296c8e` checks that every existing row has a known owner, then enforces NOT NULL and cascade FK |

The PostgreSQL database retains wider unbounded `VARCHAR` columns for the four filename/type/path values. The current PostgreSQL Alembic comparison reports no pending operation; no narrowing migration was added because narrowing existing user data is not required for the startup/migration goal and could reject or truncate legitimate existing values.

### `analyses`

Model: [`backend/app/models/analysis.py`](../backend/app/models/analysis.py). Initial table: `48e8bbad6175`; historical no-op: `c29672287d79`; `summary_text`: `f259af705ecd`; `quality_score`: `0179eb8e1705`; professional fields: `a1b2c3d4e5f6`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `48e8bbad6175` | NOT NULL; no default | Match |
| `dataset_id` | `Integer`, unique FK to `datasets.id`, `ON DELETE CASCADE` | `48e8bbad6175` | NOT NULL; no default | Match; unique one-analysis-per-dataset |
| `summary` | `JSON` | `48e8bbad6175` | NOT NULL; no default | Match |
| `column_info` | `JSON` | `48e8bbad6175` | NOT NULL; no default | Match |
| `statistics` | `JSON` | `48e8bbad6175` | NOT NULL; no default | Match |
| `missing_values` | `JSON` | `48e8bbad6175` | NOT NULL; no default | Match |
| `duplicates` | `JSON` | `48e8bbad6175` | NOT NULL; no default | Match |
| `correlations` | `JSON` | `48e8bbad6175` | NULL; no default | Match |
| `outliers` | `JSON` | `48e8bbad6175` | NULL; no default | Match |
| `summary_text` | `Text` | `f259af705ecd` (`c29672287d79` is a no-op) | NOT NULL; Python default `""`; temporary migration backfill `''` | Present once; safely backfilled; temporary server default removed |
| `quality_score` | `Integer` | `0179eb8e1705` | NOT NULL; Python default `100`; temporary migration backfill `100` | Present once; safely backfilled; temporary server default removed |
| `executive_summary` | `Text` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `key_insights` | `JSON` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `recommendations` | `JSON` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `business_opportunities` | `JSON` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `distributions` | `JSON` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `data_quality_issues` | `JSON` | `a1b2c3d4e5f6` | NULL; no default | Match |
| `created_at` | `DateTime` | `48e8bbad6175` | NOT NULL; Python default `datetime.utcnow` | Match |

### `chat_sessions`

Model: [`backend/app/models/chat_session.py`](../backend/app/models/chat_session.py). Created by `c2cdee296c8e`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `c2cdee296c8e` | NOT NULL; no default | Match |
| `dataset_id` | `Integer`, FK to `datasets.id`, `ON DELETE CASCADE` | `c2cdee296c8e` | NOT NULL; no default | Match |
| `user_id` | `Integer`, FK to `users.id`, `ON DELETE CASCADE` | `c2cdee296c8e` | NOT NULL; no default | Match |
| `title` | `String(255)` | `c2cdee296c8e` | NOT NULL; Python default `"Dataset Chat"` | Match |
| `created_at` | `DateTime` | `c2cdee296c8e` | NOT NULL; Python default `datetime.utcnow` | Match |
| `updated_at` | `DateTime` | `c2cdee296c8e` | NOT NULL; Python default/on-update `datetime.utcnow` | Match |

### `chat_messages`

Model: [`backend/app/models/chat_message.py`](../backend/app/models/chat_message.py). Created by `c2cdee296c8e`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `c2cdee296c8e` | NOT NULL; no default | Match |
| `session_id` | `Integer`, indexed FK to `chat_sessions.id`, `ON DELETE CASCADE` | `c2cdee296c8e` | NOT NULL; no default | Match |
| `role` | `String(20)` | `c2cdee296c8e` | NOT NULL; no default | Match |
| `content` | `Text` | `c2cdee296c8e` | NOT NULL; no default | Match |
| `created_at` | `DateTime` | `c2cdee296c8e` | NOT NULL; Python default `datetime.utcnow` | Match |

### `subscriptions`

Model: [`backend/app/models/subscription.py`](../backend/app/models/subscription.py). Base table: `20240901abc12`; missing provider field, enum conversion, indexes and uniqueness: `42420889e6ec`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `20240901abc12` | NOT NULL; no default | Match |
| `user_id` | `Integer`, indexed FK to `users.id`, `ON DELETE CASCADE` | `20240901abc12` | NOT NULL; no default | Match; model relationship is one-to-one but the database does not enforce uniqueness on `user_id` |
| `plan` | Enum `plan_type` (`free`, `pro`, `business`) | `20240901abc12`, converted in `42420889e6ec` | NOT NULL; Python and server default `free` | Enum values/type match model |
| `status` | Enum `subscription_status` (`active`, `canceled`, `incomplete`, `incomplete_expired`, `trialing`, `past_due`, `unpaid`, `paused`) | `20240901abc12`, converted in `42420889e6ec` | NOT NULL; Python and server default `active` | Enum values/type match model |
| `provider_customer_id` | `String(255)`, indexed | `42420889e6ec` | NULL; no default | Match |
| `provider_subscription_id` | `String(255)`, unique | `20240901abc12`; unique constraint in `42420889e6ec` | NULL; no default | Match |
| `current_period_start` | `DateTime` | `20240901abc12` | NULL; no default | Match |
| `current_period_end` | `DateTime` | `20240901abc12` | NULL; no default | Match |
| `cancel_at_period_end` | `Boolean` | `20240901abc12` | NOT NULL; Python and server default `False` | Match |
| `canceled_at` | `DateTime` | `20240901abc12` | NULL; no default | Match |
| `started_at` | `DateTime` | `20240901abc12` | NULL; no default | Match |
| `created_at` | `DateTime` | `20240901abc12` | NOT NULL; Python default `datetime.utcnow`; migration server default `now()` | Match |
| `updated_at` | `DateTime` | `20240901abc12` | NOT NULL; Python default/on-update `datetime.utcnow`; migration server default `now()` | Match |

The existing `uselist=False` relationship is not enforced by a unique constraint on `subscriptions.user_id`. No uniqueness migration was added: existing data cardinality and whether historical subscription rows are retained require a business decision before constraining this column.

### `payment_history`

Model: [`backend/app/models/subscription.py`](../backend/app/models/subscription.py). Base table: `20240901abc12`; additional columns, type reconciliation, indexes and uniqueness: `42420889e6ec`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `20240901abc12` | NOT NULL; no default | Match |
| `user_id` | `Integer`, indexed FK to `users.id`, `ON DELETE CASCADE` | `20240901abc12` | NOT NULL; no default | Match |
| `subscription_id` | `Integer`, indexed FK to `subscriptions.id`, `ON DELETE SET NULL` | `20240901abc12`; index in `42420889e6ec` | NULL; no default | Match |
| `amount` | `Float` | `20240901abc12` | NOT NULL; no default | Match |
| `currency` | `String(3)` | `20240901abc12`; narrowed in `42420889e6ec` | NOT NULL; Python and server default `"USD"` | Match |
| `payment_status` | `String(50)`, indexed | `20240901abc12`; widened/indexed in `42420889e6ec` | NOT NULL; no default | Match |
| `payment_provider` | `String(50)` | `42420889e6ec` | NOT NULL; Python and server default `"stripe"` | Match |
| `provider_payment_id` | `String(255)`, unique | `20240901abc12`; unique constraint in `42420889e6ec` | NULL; no default | Match |
| `plan_type` | `String(50)` | `20240901abc12`; widened in `42420889e6ec` | NOT NULL; no default | Match |
| `description` | `Text` | `20240901abc12`; widened to `Text` in `42420889e6ec` | NULL; no default | Match |
| `metadata_json` | `Text` | `42420889e6ec` | NULL; no default | Match |
| `created_at` | `DateTime` | `20240901abc12` | NOT NULL; Python default `datetime.utcnow`; migration server default `now()` | Match |

### `notifications`

Model: [`backend/app/models/notification.py`](../backend/app/models/notification.py). Base table: `20240901abc12`; added metadata/expiry, title width, enum conversion and indexes: `42420889e6ec`.

| Column | Model definition | Migration that creates it | Nullable/default | Status |
|---|---|---|---|---|
| `id` | `Integer`, primary key, indexed | `20240901abc12` | NOT NULL; no default | Match |
| `user_id` | `Integer`, indexed FK to `users.id`, `ON DELETE CASCADE` | `20240901abc12` | NOT NULL; no default | Match |
| `title` | `String(200)` | `20240901abc12`; narrowed in `42420889e6ec` | NOT NULL; no default | Match |
| `message` | `Text` | `20240901abc12` | NOT NULL; no default | Match |
| `type` (model attribute `notification_type`) | Enum `notification_type` (`info`, `success`, `warning`, `error`, `payment`, `system`), indexed | `20240901abc12`; converted/indexed in `42420889e6ec` | NOT NULL; Python and server default `info` | Enum values/type match model |
| `is_read` | `Boolean`, indexed | `20240901abc12` | NOT NULL; Python and server default `False` | Match |
| `action_url` | `String(500)` | `20240901abc12` | NULL; no default | Match |
| `metadata_json` | `Text` | `42420889e6ec` | NULL; no default | Match |
| `created_at` | `DateTime`, indexed | `20240901abc12`; index in `42420889e6ec` | NOT NULL; Python default `datetime.utcnow`; migration server default `now()` | Match |
| `expires_at` | `DateTime` | `42420889e6ec` | NULL; no default | Match |

## Changes made and why

1. **`f259af705ecd`: safe Analysis summary backfill.** Adds `summary_text` as NOT NULL with a temporary empty-string server default, then drops that server default. Existing rows receive a valid value before the NOT NULL constraint applies; new ORM behavior continues to use the model's Python default.
2. **`0179eb8e1705`: safe Analysis score backfill.** Same pattern, using `100` for pre-existing rows, then removing the temporary server default.
3. **`c2cdee296c8e`: safe dataset nullability/FK migration.** Existing null `uploaded_at` values are backfilled with the migration timestamp. The migration refuses to guess owners for rows with null `owner_id`, raising an actionable error before schema changes. The replacement cascade foreign key now has a stable explicit name, which also makes downgrade operations valid.
4. **Historical migration descriptions corrected.** `f957ba39a00d` and `c29672287d79` are explicitly described as historical no-ops; `f259af705ecd` is identified as the summary migration; `0179eb8e1705` is identified as the quality-score migration. This fixes misleading `alembic history` descriptions while retaining every revision ID and filename.
5. **No model or Pydantic schema change was needed.** `app.models` is imported by [`backend/alembic/env.py`](../backend/alembic/env.py), populating the same `Base.metadata` imported from [`backend/app/db/base.py`](../backend/app/db/base.py). The inspected Pydantic schema modules describe API payloads and do not define database columns.

### Existing-data safety boundaries

- A dataset with no owner cannot be migrated to a required `owner_id` without an authoritative ownership mapping. The migration intentionally fails and preserves the row/revision; assign verified owners, then rerun.
- The billing reconciliation converts existing text to enums and adds unique constraints. PostgreSQL rejects unknown enum values or duplicate non-null provider IDs; its transactional DDL rolls back the failed migration instead of silently rewriting rows. Review/map invalid values or resolve duplicates explicitly before rerunning.
- PostgreSQL also rejects the existing `notifications.title` to `VARCHAR(200)` and `payment_history.currency` to `VARCHAR(3)` changes if stored values exceed the model limits; these failures roll back rather than truncate data.
- No historical revision was deleted, squashed, reset, or assigned a new revision ID.

## Validation results

All commands below ran with the backend virtual environment and an isolated PostgreSQL 16 container. The database URLs used were process-local loopback URLs; no repository `.env` values were printed or placed in this report.

| Validation | Database/state | Result |
|---|---|---|
| `python -m alembic heads` | Current graph | PASS — one head, `42420889e6ec` |
| `python -m alembic history` | Current graph | PASS — every parent resolves; both branch parents merge at `658de0610bd9` |
| `python -m alembic upgrade head` | New empty PostgreSQL database | PASS — all 14 revisions applied |
| `python -m alembic check` | Fresh database at head | PASS — no pending model/schema operations |
| Enum catalog query | Fresh database at head | PASS — one PostgreSQL type for each of the three expected names |
| Existing-data upgrade | Disposable database seeded at `48e8bbad6175` with user, dataset (`uploaded_at=NULL`), and analysis row | PASS — reaches head; user/dataset/analysis preserved; timestamp and Analysis defaults backfilled |
| `python -m alembic check` | Populated database at head | PASS — no pending model/schema operations |
| Billing schema upgrade | Disposable database seeded at `20240901abc12` with existing subscription, payment and notification rows | PASS — enum conversion retains values and rows; added fields/defaults present; each enum type count is one |
| Null-owner guard | Disposable database at `48e8bbad6175` with dataset `owner_id=NULL` | PASS — expected refusal; row and revision `48e8bbad6175` preserved |

Commands used (with `DATABASE_URL` set in the process to the relevant disposable local database and `SECRET_KEY` set to a throwaway value):

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\backend'
python -m alembic heads
python -m alembic history
python -m alembic upgrade head
python -m alembic check
```

The test database container was ephemeral and did not use a persistent volume. These checks do not establish that an actual deployed database contains only valid enum values, unique provider IDs, or non-null known dataset owners. Run the same migration commands against a backup/clone of each deployed database before production rollout.
