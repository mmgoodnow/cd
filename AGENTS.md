<<<<<<< HEAD
# Repository Guidelines

## Scope and Purpose
This repository contains GitHub Actions workflows that build and publish Docker images to GHCR and optionally trigger a Watchtower update through Tailscale. There is no application source code checked in; the workflows assume a root-level Docker build context when present.

## Project Structure & Module Organization
- `.github/workflows/docker.yml`: Multi-arch build (amd64 + arm64), manifest creation, and Watchtower update.
- `.github/workflows/docker-amd64.yml`: amd64-only build and manifest flow.
- `Dockerfile` (expected at repo root when images are built) along with any build context files.
- Generated artifacts: `digest-amd64.txt` and `digest-arm64.txt` created during CI runs.

## Build, Test, and Development Commands
- `docker buildx build --platform linux/amd64 -t ghcr.io/<org>/<repo>:local .`
  builds a local amd64 image using the root `Dockerfile`.
- `docker buildx build --platform linux/arm64 -t ghcr.io/<org>/<repo>:local --load .`
  builds an arm64 image on compatible hosts.
- `docker buildx imagetools create --tag ghcr.io/<org>/<repo>:local ghcr.io/<org>/<repo>@<digest>`
  assembles a manifest from published digests.
- CI runs on push and supports workflow dispatch for manual runs.

## Coding Style & Naming Conventions
- GitHub Actions YAML uses 2-space indentation with ordered, explicit steps (checkout → buildx → login → build/push).
- Job and step identifiers use kebab-case (e.g., `build-amd64`, `watchtower-update`).
- Secrets and environment variables are uppercase with underscores (e.g., `WATCHTOWER_API_TOKEN`).

## Testing Guidelines
- There is no local test suite in this repository.
- Verify changes by running the relevant GitHub Actions workflow and checking GHCR tags and manifest output.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative, and sentence case (e.g., "Split reusable workflows for multiarch and amd64").
- After every change (or logical set of changes), commit and push.
- PRs should explain workflow behavior changes, list required secrets, and link to a successful workflow run.

## Security & Configuration Tips
- Watchtower updates require `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_CLIENT_SECRET`, `WATCHTOWER_UPDATE_URL`, and `WATCHTOWER_API_TOKEN`.
- Do not echo secret values; rely on masked environment variables in CI logs.
=======
# Agent Instructions

- After every change (or logical set of changes), commit and push.
>>>>>>> bd78bc6 (Pass git metadata build args)
