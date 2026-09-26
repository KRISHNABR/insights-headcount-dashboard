"""Headcount dashboard — an interactive app on Insights Hub.

`web.type: spa` — this file is the backend; `static/` is the frontend. The platform
serves both from the same origin, which is what lets the browser hold nothing but a
session cookie it cannot read.

What is NOT in this file: login, session handling, a connection, a credential, a
table name, logging setup, a health endpoint, a Dockerfile, or a pipeline.
"""

from insights_sdk import current_user, fetch, get_logger, query, require_role, web_app

app = web_app()          # login, identity, structured logs, metrics and /healthz
log = get_logger()


@app.get("/api/headcount")
def headcount(month: str = "2026-09"):
    """Read the warehouse.

    `hr.headcount` is a dataset name, not a table. The platform resolves it to
    whichever physical table this environment uses, so this exact query runs in
    dev, uat and prod with no environment handling.
    """
    require_role("headcount-viewer")          # 403 if they aren't in the group

    rows = query(
        "hr.headcount",
        "SELECT dept, headcount FROM hr.headcount WHERE month = :month ORDER BY dept",
        month=month,
    )

    # Telemetry records the SHAPE of the result, never the result. Passing `rows`
    # here would raise — the logger refuses anything that isn't a scalar.
    log.info("headcount_viewed", month=month, rows=len(rows))
    return {"month": month, "departments": rows}


@app.get("/api/team")
def team(dept: str = "Engineering"):
    """The same pattern against a completely different shared connection.

    `directory.people` is an internal REST API rather than the warehouse. The only
    thing that changes in this code is the verb.
    """
    require_role("headcount-viewer")
    people = fetch("directory.people", params={"dept": dept})
    log.info("directory_viewed", dept=dept, rows=len(people))
    return {"dept": dept, "people": people}


@app.get("/api/me")
def me():
    """Who the platform says you are. Useful on day one, and it proves identity
    arrived from the front door rather than from anything the browser sent."""
    caller = current_user()
    return {"subject": caller.subject, "groups": list(caller.groups), "trusted": caller.trusted}
