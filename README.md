# headcount-dashboard

An interactive web app on [Insights Hub](https://github.com/KRISHNABR/insights-platform/blob/main/README.md). Owned by **people-ops**.

Shows headcount by department, and looks people up in the internal directory.

| | |
|---|---|
| What we wrote | [`src/main.py`](src/main.py) (~50 lines) and [`app.yaml`](app.yaml) |
| What we inherited | auth, data access, logging, health, deployment, the base image |
| How to run it | `insights run` from the platform repo, or see the [root README](https://github.com/KRISHNABR/insights-platform) |

Everything in this repo except `src/` and `app.yaml` was generated and is not ours to
maintain. When the platform changes them, we get the change by upgrading the SDK.

---

*New to the platform? Start at the [platform README](https://github.com/KRISHNABR/insights-platform/blob/main/README.md), which maps everything, then [ONBOARDING.md](https://github.com/KRISHNABR/insights-platform/blob/main/ONBOARDING.md).*
