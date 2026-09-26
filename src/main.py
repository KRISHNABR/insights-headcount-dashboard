"""Headcount dashboard - an interactive web app on Insights Hub.

Deliberately trivial. The interesting thing about this file is how SHORT it is: there is
no auth code, no connection setup, no logging configuration, no health endpoint and no
Dockerfile logic, because none of that is this team's problem.

Everything this app knows about the platform is the four imports below.
"""

from insights_sdk import current_user, fetch, get_logger, query, require_role, web_app

app = web_app()
log = get_logger()


@app.get("/")
def index() -> dict:
    """Who am I? Useful on day one, and it proves identity arrived from the edge."""
    caller = current_user()
    return {
        "app": "headcount-dashboard",
        "you": caller.subject,
        "your_groups": list(caller.groups),
        "try": ["/headcount?month=2026-09", "/team?dept=Engineering", "/healthz"],
    }


@app.get("/headcount")
def headcount(month: str = "2026-09") -> dict:
    """Read the warehouse.

    Note what is absent: no connection, no credential, no table name. `hr.headcount` is
    a logical dataset; the platform knows it is `hr_headcount` here and something else
    in production, and this code never finds out.
    """
    require_role("headcount-viewer")

    rows = query(
        "hr.headcount",
        "SELECT dept, headcount FROM hr.headcount WHERE month = :month ORDER BY dept",
        month=month,
    )
    # Telemetry records the SHAPE of the result, never the result. The SDK would raise
    # if this tried to pass `rows` itself.
    log.info("headcount_viewed", month=month, rows=len(rows))
    return {"month": month, "departments": rows}


@app.get("/team")
def team(dept: str = "Engineering") -> dict:
    """Read the internal REST API - a different shared connection, declared the same way.

    The only difference visible from here is the verb.
    """
    require_role("headcount-viewer")
    people = fetch("directory.people", params={"dept": dept})
    log.info("directory_viewed", dept=dept, rows=len(people))
    return {"dept": dept, "people": people}
