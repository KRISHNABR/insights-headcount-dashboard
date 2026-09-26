# YOUR Dockerfile. Generated once by `insights new-app`; yours to edit from here.
#   app: headcount-dashboard
#
# The platform does not rewrite this file, does not publish a base image, and does not
# patch one for you. It is an ordinary Python image and you own it - which also means
# you can change the Python version on the next line whenever you need to.
#
# TWO THINGS CI CHECKS, and only two:
#
#   1. the base is PINNED, not :latest   an image you cannot name is one you cannot
#                                        roll back to
#   2. the final USER is not root        a container breakout should land on a user
#                                        that owns nothing
#
# Everything else is a suggestion. Add build stages, system packages, a different
# distro - CI will not stop you.
FROM python:3.12-slim

# uv, pinned, from its official image. It resolves dependencies in the image exactly
# as it does on your laptop.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

RUN useradd --create-home --uid 10001 app
WORKDIR /app

# Your dependencies, from YOUR pyproject.toml, installed from the COMMITTED lockfile.
# --frozen means the lock must already be current: the image resolves exactly what your
# laptop resolved, or the build fails.
#
# Copied before your source so a code change does not reinstall the world.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY src/ /app/src/
COPY app.yaml /app/app.yaml
COPY static/ /app/static/

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
