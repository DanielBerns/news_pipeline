After pushing the repo into github, I got the following error

Warning: Unexpected input(s) 'uv', valid inputs are ['python-version', 'python-version-file', 'cache', 'architecture', 'check-latest', 'token', 'cache-dependency-path', 'update-environment', 'allow-prereleases', 'freethreaded']
Run actions/setup-python@v5
  with:
    python-version: 3.11
    uv: latest
    cache: uv
    check-latest: false
    token: ***
    update-environment: true
    allow-prereleases: false
    freethreaded: false
Installed versions
  Successfully set up CPython (3.11.13)
Error: Caching for 'uv' is not supported
