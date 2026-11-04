# Shared container CD

Call `.github/workflows/docker.yml` for amd64 + arm64, or
`docker-amd64.yml` for amd64 only. The calling repository supplies the Docker
context and credentials. Build jobs upload immutable image digests in parallel.

## Publication ordering

Manifest publication and Watchtower updates share a repository/ref-scoped
concurrency group across both workflow variants. They queue rather than cancel
each other; builds do not hold that lock. `queue: max` preserves up to 100 pending
jobs instead of letting a late old run replace a pending new run.

Inside the lock, each side-effect job checks the calling source ref against its
build SHA using GitHub's commits API. A stale build cannot update image tags or
trigger Watchtower, including when verification finishes out of order or an old
run is retried. Failed lookups fail closed. If a ref advances after publication,
the second check skips that old run's deployment. Push a new commit (including a
revert) for an intentional rollback; rerunning a superseded commit is not a
rollback mechanism. Branches and tags have separate locks and freshness checks.

Watchtower remains scoped to the calling repository's image, never unrelated
applications. No consumer-specific concurrency configuration is required.

The current-commit check also means a new, unverified source revision can prevent
an older build from deploying; the newest revision must pass its normal checks.

## Validation

`python3 -m unittest discover -v` exercises the actual embedded shell guards with
stubbed GitHub responses, publication/deployment wiring, out-of-order completions,
branch/tag refs, failed lookups, and Watchtower image scoping. YAML parsing and
shell syntax should also be checked before pushing. Deployment itself remains
normal GitHub Actions CD, never a manual container replacement.
