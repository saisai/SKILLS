---
name: document-codebase
description: >-
  Writes in-repo docs that explain how a subsystem works, with Mermaid
  workflows and diagrams, from the current code. Use when the user asks to
  explain and document a framework, OpenAPI or other API contract, GraphQL,
  protobuf or gRPC, cloud or Kubernetes deploy, cmd or entrypoints, commands
  (Makefile targets, npm or other package scripts, scripts/, CI run steps),
  internal packages, migrations, a database design diagram (ERD or UML),
  system design, high-level design (HLD), low-level design (LLD), a frontend,
  or end-to-end tests, or asks for architecture docs with a workflow or
  diagram in any project.
---

# Document a codebase

Put the explanation in the project as markdown. Ground every command, port, path, and file name in the tree you just read. The chat summary points at those files.

Works for any language or layout. Topic playbooks are in [reference.md](reference.md). The page shape is in [template.md](template.md).

## Workflow

1. Inventory the repo: entrypoints, command sources (`Makefile`, `package.json` / `pyproject.toml` / `*.csproj` scripts, `scripts/`, Dockerfile `ENTRYPOINT` / `CMD`, CI `run` steps), HTTP or RPC adapters, contracts (OpenAPI, GraphQL schema, proto), schema and migrations, UI, deploy, and tests. Read the README and any existing `docs/` before writing.
2. Match each requested topic to a playbook. If the topic is not in this repo, say so in the doc and document the closest real path. Do not invent a suite, manifest, or binary.
3. Read the playbook's "read first" files, then the code they point at. Versions and flags come from `go.mod`, `package.json`, `*.csproj`, `pyproject.toml`, Dockerfiles, or the Makefile — whichever this repo uses.
4. Write one page per topic under `docs/`. If that page already exists, update it.
5. Add or update a short index (`docs/architecture.md` when the system has several moving parts, plus a README list) that links every page.
6. Cross-link related pages at the top of each doc.

## Page rules

- Open with what this piece is in **this** project, and what it does not do.
- Include at least two Mermaid diagrams when the user asked for a workflow or diagram: one structural `flowchart`, and one `sequenceDiagram` or decision `flowchart` of the main path.
- A "how to use" section uses commands that already exist (`Makefile`, `package.json` scripts, `scripts/`, CI, Docker). Show the compile or generate step when the topic is a program, schema, or generated client.
- Explain a command in detail when the name is a wrapper: a Make target that only launches a script, or a script with conditionals, cleanup, or flags that change what is left running. A one-line mapping is enough when the command is the tool itself (`npm run lint` → `eslint .`).
- A "how to change" section is a short ordered list.
- End with a files table: path and the one job of that file.
- Do not paste generated code, SQL dumps, or lockfiles into the doc.

## Diagram rules

- `flowchart LR` or `TB` for where the piece sits.
- `sequenceDiagram` for one real request or job.
- `flowchart TD` for boot order or "which command do I run".
- Node labels use names from this repo (binary, route, table, env var).
- Omit a box the tree does not contain.

## Chat reply

After the files are written, explain each topic in a few sentences and link the page. Do not paste the full doc back into chat.

## Do not

- Create tests, deploy manifests, or application code unless the user asked for that separately.
- Commit unless the user asked.
- Copy a worked example from another repo into this one. Depth can match a thorough architecture page; facts must come from the current tree.
