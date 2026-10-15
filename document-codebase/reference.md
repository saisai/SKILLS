# Topic playbooks

Pick the playbooks the user named. Skip a playbook when the inventory finds no signal, and write a short "not in this repo" note only if the user asked about that topic.

Signals are hints. The current tree wins when they disagree.

## HTTP framework

**Signals:** `echo`, `gin`, `chi`, `fiber`, `net/http`, Express, Fastify, Hono, Nest, FastAPI, Flask, Django, Spring `@RestController`, ASP.NET `MapGet` / controllers, Rails routes, Axum, Actix.

**Read first:** router or app factory, middleware registration, one read handler, one write handler, error writer, server `main`.

**Document:** framework version from the manifest; what a request object is; middleware order as registered (first registered is usually outermost — confirm in code); route table (method, path, auth); one read sequence and one write sequence; how errors become the response body; files table.

**Across stacks:** Go often splits `cmd/<server>` from `internal/transport`. Node often uses `src/app.ts` or `server.ts`. Python uses `main.py` or `app/`. Java uses a `@SpringBootApplication` class. .NET uses `Program.cs`. The page still answers: who listens, which middleware runs, which function handles the route, where business rules live (they should not be only in the route).

## API contract (OpenAPI and equivalents)

**Signals:** `openapi.yaml`, `swagger.json`, GraphQL `schema.graphql`, tRPC routers, Smithy, a generated `api-generated.ts` or OpenAPI client.

**Read first:** the spec file, the generator script, one implementation of a documented operation, the generated client or types.

**Document:** spec version and path; `info`, servers, paths, components (or the equivalent: schema, queries, mutations); that the spec describes the API and does not run it, unless this repo's server loads it at startup (confirm); a flowchart from spec → generator → client and from client → server; the operation table; how to change the contract and regenerate. If the server is hand-written, say the spec and the handlers can drift and list the steps that keep them together.

**Equivalents:** GraphQL — schema, resolvers, codegen. tRPC — router and inferred client types. Springdoc / Swashbuckle — spec generated from code; reverse the arrow in the diagram.

## IDL and RPC (protobuf, gRPC, and equivalents)

**Signals:** `*.proto`, `buf.yaml`, `*.pb.go`, `*_grpc.pb.go`, Thrift, Avro, Connect, gRPC server `main`.

**Read first:** the `.proto` (or IDL), generate config, generated stubs, server implementation, client example or test.

**Document:** syntax and package; message vs service; field numbers as the compatibility key; generate command and output paths; call sequence from client through the adapter to the use-case; RPC table; status or error mapping; how to add a field or method. State whether the port is public.

**Equivalents:** Connect and gRPC-Web still start from proto. Thrift and Avro use their own compilers — name the one in the repo. JSON-RPC or a message bus: document the envelope and the handler map instead of `protoc`.

## Cloud and Kubernetes deploy

**Signals:** `deploy/`, `k8s/`, Helm, Kustomize, Dockerfiles, Terraform, Pulumi, ECS task defs, Cloud Run, App Runner, serverless.yml, compose file used as the local stand-in.

**Read first:** Dockerfiles (build args, binary or start command, user), the manifests that exist, compose, env example, the migration command (who runs schema changes).

**Document:** a flowchart of edge → workloads → data stores, with ports and which ones are public; an ordered deploy workflow (images, cluster, data, secrets, migrate, workloads, ingress, smoke check); the commands from the Dockerfile and manifests; how to call the running system; rollout when schema and app change together. Label sample YAML as the shape to apply when those files are not in the tree. Do not invent account IDs, cert ARNs, or secrets.

**Other clouds:** same page shape. Swap EKS/ALB/RDS for the products this repo names (GKE and Cloud SQL, AKS and Azure Database, Fly, Render, a single VM). If only compose exists, document compose and add a short "cluster shape" section only when the user asked how to deploy beyond local.

## Entrypoints (`cmd/`, `apps/`, `src/main`)

**Signals:** `cmd/*/main.go`, `package main`, `apps/*/src/main.ts`, `__main__.py`, `Program.cs`, `Main.java`, `src/main.rs`, `bin/` scripts.

**Read first:** each entry file's `main` (or `if __name__`), the build script, the Dockerfile `BIN` or target, process flags.

**Document:** one directory (or module) is one process; how compile works (`go build ./cmd/<name>`, `npm run build`, `mvn package`, `dotnet publish`, `cargo build`); a table of output → source → role; a flowchart of launchers versus servers; which command to run for each goal; flags that are real (`-h` output or the flag definitions). Note when `go run` / `npm run dev` does not write the release binary.

## Commands

**Signals:** `Makefile`, `justfile`, `Taskfile.yml`, `package.json` `scripts`, `scripts/`, workflow `run` keys.

**Read first:** the Makefile or task runner, each script it calls, package scripts, CI steps, and compose or Dockerfile commands that the docs already mention.

**Document:** one `docs/commands.md` page. A table of goal → command → working directory. A `flowchart LR` of the launcher to the processes it starts. A `flowchart TD` of the main script’s real order, including branches that exist in the script (port already open, missing binary, stop only what this run started). Skip a box the tree does not contain.

**Depth:** quote the underlying command (`powershell -File`, `protoc` flags, `pg_dump` flags). Spell out side effects: files written, processes not stopped, data left on disk, env vars overridden. Point HTTP, deploy, and test behavior at those pages instead of repeating them. Explain a command in detail when the name is a wrapper. A one-line mapping is enough when the command is the tool itself.

**Do not:** invent targets, claim a command was executed, or paste lockfiles.

**How to change:** put behavior in the script; keep a task-runner target as a one-line wrapper; keep paired scripts (`.ps1` and `.sh`) on the same flags.

## Internal or library packages

**Signals:** `internal/`, `src/lib`, `pkg/` that apps import, a core module with no `main`, Python packages imported by apps, a class library project.

**Read first:** import graph (who imports whom), the use-case type, the persistence adapter, the HTTP or RPC adapter, the domain errors.

**Document:** the visibility rule (Go `internal` is compiler-enforced; other languages use convention or a published package); how the library is compiled (as a dependency of an entrypoint or test, not as its own server, unless it is); a dependency diagram with arrows pointing toward the core; boot sequence; package table with the public constructor (`NewX`, `createX`); how to add a behavior (domain → persistence → use case → adapter → test → build). Say which packages a small binary leaves out.

## Migrations and schema

**Signals:** `migrations/`, Flyway, Liquibase, Alembic, Prisma, Knex, Rails `db/migrate`, Entity Framework migrations, goose, golang-migrate, sqitch.

**Read first:** the runner `main` or CLI config, embed or path config, the latest migration, the schema history table name, whether the server process also migrates.

**Document:** file layout and naming; up versus down; whether SQL is embedded at compile time or read from disk at runtime; the apply flowchart including the history table; who starts the runner (dev, compose, CI, Job) and that the server does or does not migrate; commands; how to add the next version without editing an applied one. Point table shapes at a separate database page when one exists.

## Frontend

**Signals:** `web/`, `frontend/`, `app/`, `pages/`, `src/routes`, Next, Remix, Nuxt, SvelteKit, Angular, React Router, a mobile app.

**Read first:** route files, data-fetch module, API base URL env, auth storage, a client component that mutates, the rewrite or proxy config, the production start command.

**Document:** framework and router; URL → file table and which routes run on the server vs the client; a sequence for the main page (browser → UI server → API); where types come from (hand-written or generated); cache or revalidation if the API calls back; how to run dev and production. State the data store the UI talks to (HTTP, not the database) when that is true.

## End-to-end and other tests

**Signals:** `e2e/`, `cypress/`, `playwright.config.*`, `*.spec.ts`, `tests/`, `*_test.go`, `*_integration_test.go`, k6, CI workflow.

**Read first:** the test config, one spec, the CI jobs, any load script.

**Document:** the user-facing path as a flowchart even when no browser suite exists. Then a table of what actually runs (unit, integration, contract, load) and the command. If Playwright or Cypress is only a transitive dependency, say that. Do not describe a suite that is not in the tree. A "how to add a browser test" note is one short paragraph, not a new framework install, unless the user asked to add tests.

## Index page

When you write more than one topic page, add `docs/architecture.md`:

- one system flowchart
- a component table (role, port or entry, public or not)
- the request paths in a few numbered lines that link to the topic pages
- a layout tree of the directories you documented
- runtime modes (local, compose, cluster) that exist

Link that index from the README. When a commands page was written, link it from `docs/architecture.md` and the README list.
