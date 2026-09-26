"""Headcount dashboard — an interactive app on Insights Hub.

`web.type: spa` — this file is the backend; `static/` is the frontend. The platform
serves both from the same origin, which is what lets the browser hold nothing but a
session cookie it cannot read.

Two connections, two engines, one call shape: a warehouse and an internal REST API.
Both are declared in app.yaml; neither credential appears anywhere in this repo.

What is NOT in this file: login, session handling, a credential, a host, logging
setup, a health endpoint, or a pipeline.
"""

from insights_sdk import connect, current_user, get_logger, require_role, web_app

app = web_app()          # login, identity, structured logs, metrics and /healthz
log = get_logger()


@app.get("/api/headcount")
def headcount(month: str = "2026-09"):
    """Read our warehouse.

    The connection is declared in app.yaml, so the host differs per environment and
    this line does not. We already have access to this data - the platform ships the
    connector and holds the credential slot; it does not broker the read and never
    sees a row.
    """
    require_role("reader")                    # 403 unless they are listed in app.yaml

    rows = connect("hr-warehouse").query(
        "SELECT dept, headcount FROM hr_headcount WHERE month = :month ORDER BY dept",
        month=month,
    )

    # Telemetry records the SHAPE of the result, never the result. Passing `rows`
    # here would raise — the logger refuses anything that isn't a scalar.
    log.info("headcount_viewed", month=month, rows=len(rows))
    return {"month": month, "departments": rows}


@app.get("/api/team")
def team(dept: str = "Engineering"):
    """The same pattern against a completely different engine.

    `people-directory` is an internal REST API rather than a warehouse, and it needs
    a bearer token where the warehouse needed none. Neither difference shows up here:
    the connector resolves the credential, and `query` takes a path instead of SQL.
    """
    require_role("reader")
    people = connect("people-directory").query("/people", dept=dept)
    log.info("directory_viewed", dept=dept, rows=len(people))
    return {"dept": dept, "people": people}


@app.get("/api/me")
def me():
    """Who the platform says you are. Useful on day one, and it proves identity
    arrived from the front door rather than from anything the browser sent."""
    caller = current_user()
    return {"subject": caller.subject, "groups": list(caller.groups), "trusted": caller.trusted}
