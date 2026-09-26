# headcount-dashboard

An interactive web app on [Insights Hub](https://github.com/KRISHNABR/insights-platform), owned
by **people-ops**. Shows headcount by department, and looks people up in the internal directory.

It exists to prove the consumption model, so it is deliberately trivial. **The interesting thing
about this repo is how little is in it.**

---

## What we wrote, and what we got

| We wrote | Lines |
|---|---|
| [`src/main.py`](src/main.py) — three JSON endpoints | ~45 |
| [`static/index.html`](static/index.html) — the frontend | ~70 |
| [`app.yaml`](app.yaml) — our contract with the platform | ~90, mostly comments |

| We inherited, and wrote none of | |
|---|---|
| Corporate sign-in, sessions, group membership | |
| Permission checks (`require_role`) | |
| Data access — no connection, no credential, no table name | |
| Structured logs, metrics, audit records | |
| `/healthz`, which opens every connection we declared | |
| The container image | |
| Four CI/CD pipelines across three environments | |

There is **no pipeline code, no auth code and no connection string** in this
repository. That is the platform's value proposition, stated as a file listing.

---

## Setup

```bash
# 1 · get all four repos side by side (the local loop finds siblings by name)
mkdir insights-hub && cd insights-hub
for r in insights-platform insights-sdk insights-headcount-dashboard insights-comp-report; do
  git clone "https://github.com/KRISHNABR/$r.git"
done

# 2 · start the whole platform
cd insights-platform && uv run insights up          # add --port 9100 if 8080 is taken

# 3 · sign in. Appending ?as= is the entire local login
open "http://localhost:8080/a/headcount-dashboard/?as=krishna@corp.example"
```

Needs Python 3.12 and [uv](https://docs.astral.sh/uv/). No Docker, no cloud account.

### Working on this app

```bash
uv sync                      # install
uv run insights doctor       # everything CI will check, checked locally — same code path
uv run insights connections  # what we talk to, and whether we can
uv run insights build --show # the exact container image the platform will build for us
```

### The users you can sign in as

| User | Groups | What you'll see |
|---|---|---|
| `krishna@corp.example` | `MG-PEOPLE-OPS`, `headcount-viewer` | Everything — she holds the role |
| `vidya@corp.example` | `MG-PEOPLE-ANALYTICS`, `comp-analyst` | **403.** Signed in, but not a `headcount-viewer` |
| `suraj@corp.example` | `MG-PLATFORM` | **403.** Platform team has no special access to tenant apps |

That middle row is the useful one: authentication and authorization are different questions.

---

## How a request actually works

```mermaid
flowchart TB
  B["browser<br/><i>static/index.html</i>"] -->|"fetch('/api/headcount')<br/>same origin, cookie rides along<br/><b>no token in the browser</b>"| E

## How a request works

```mermaid
flowchart TB
  U["krishna opens the dashboard"] --> E1["the edge: is there a session?"]
  E1 -->|no| L(["401 — sign in"])
  E1 -->|yes| E2{"<b>LAYER 1</b><br/>in a group that may use this app?"}
  E2 -->|no| F(["403 — before any of our code runs"])
  E2 -->|yes| E3["STRIP every X-Auth-* the client sent<br/>INJECT validated ones + an edge token"]
  E3 --> A["our handler"]
  A --> R{"<b>LAYER 2</b><br/>require_role('reader')"}
  R -->|no| F2(["403"])
  R -->|yes| C["connect('hr-warehouse')"]
  C --> C1["resolve the secret as this app's identity"]
  C1 --> C2["open the connection, run our SQL"]
  C2 --> C3["record connection, engine, ms, rows<br/><i>never the SQL, never a row</i>"]
  C3 --> OUT(["JSON"])
```

---

## Two engines, one call shape

```yaml
connections:
  - name: hr-warehouse
    engine: sqlite               # databricks-sql in dev and prod
    path: ...

  - name: people-directory
    engine: rest
    base_url: ${INSIGHTS_DIRECTORY_URL}
    secret: directory-api-token
    timeout: 10
```

```python
rows   = connect("hr-warehouse").query("SELECT dept, headcount FROM hr_headcount ...")
people = connect("people-directory").query("/people", dept=dept)
```

A warehouse and an internal REST API. One needs a bearer token; the other needs none.
Neither difference appears in our code — for a REST connection `query()` takes a path
instead of SQL, and the connector attaches the credential.

**We already have access to both.** The platform is not in that loop: it ships the
connector, holds the credential where we can reach it and the platform team cannot, and
translates the driver's error into something that says who has to fix it.

---

## Local vs production

| Concern | Local | Production | Changes in `src/` |
|---|---|---|---|
| Sign-in | `?as=` stub | ALB native OIDC | nothing |
| Identity to our code | `X-Auth-*` from the local edge | `X-Auth-*` from the gateway | nothing |
| The warehouse | sqlite | Databricks SQL | nothing — swap `engine:` and `host:` |
| The directory | a local REST stub | the real internal API | nothing |
| Credentials | files in the fake store | Secrets Manager, scoped to `sp-headcount-dashboard` | nothing |
| Column masks, row filters | — | **Unity Catalog**, per principal, on every path | nothing |
| Telemetry | JSONL on disk | stdout → CloudWatch | nothing |

**User identity reaches the data in production.** An interactive request uses OAuth token
exchange, so Unity Catalog sees `krishna@corp.example` and applies *their* grants and
masks — not the app's. A scheduled run uses workload identity federation and UC sees the
service principal. Either way the decision is made by the data platform, against a real
principal, on every path including a notebook.

**What the platform team can see:** that this app queried `hr-warehouse`, how long it took
and how many rows came back. Not the SQL, not a row. There is no identity here for them to
impersonate, and no credential of ours they can read.

---

*Start at the [platform README](https://github.com/KRISHNABR/insights-platform), then
[ONBOARDING.md](https://github.com/KRISHNABR/insights-platform/blob/main/ONBOARDING.md).*
