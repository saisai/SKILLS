# Topic playbooks

Pick the playbooks the user named. Skip a playbook when the inventory finds no signal, and write a short "not in this repo" note only if the user asked about that topic.

Signals are hints. The current tree wins when they disagree.

## HTTP framework

**Signals:** `echo`, `gin`, `chi`, `fiber`, `net/http`, Express, Fastify, Hono, Nest, FastAPI, Flask, Django, Spring `@RestController`, ASP.NET `MapGet` / controllers, Rails routes, Axum, Actix.

**Read first:** router or app factory, middleware registration, one read handler, one write handler, error writer, server `main`.

**Document:** framework version from the manifest; what a request object is; middleware order as registered (first registered is usually outermost — confirm in code); route table (method, path, auth); one read sequence and one write sequence; how errors become the response body; files table.

**Across stacks:** Go often splits `cmd/<server>` from `internal/transport`. Node often uses `src/app.ts` or `server.ts`. Python uses `main.py` or `app/`. Java uses a `@SpringBootApplication` class. .NET uses `Program.cs`. The page still answers: who listens, which middleware runs, which function handles the route, where business rules live (they should not be only in the route).

## API contract (OpenAPI and equivalents)

**Signals:** `openapi.yaml`, `swagger.json`, tRPC routers, Smithy, a generated `api-generated.ts` or OpenAPI client. GraphQL has its own playbook.

**Read first:** the spec file, the generator script, one implementation of a documented operation, the generated client or types.

**Document:** spec version and path; `info`, servers, paths, components (or the equivalent: schema, queries, mutations); that the spec describes the API and does not run it, unless this repo's server loads it at startup (confirm); a flowchart from spec → generator → client and from client → server; the operation table; how to change the contract and regenerate. If the server is hand-written, say the spec and the handlers can drift and list the steps that keep them together.

**Equivalents:** tRPC — router and inferred client types. Springdoc / Swashbuckle — spec generated from code; reverse the arrow in the diagram. GraphQL — use the GraphQL playbook, not this page.

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

**Document:** file layout and naming; up versus down; whether SQL is embedded at compile time or read from disk at runtime; the apply flowchart including the history table; who starts the runner (dev, compose, CI, Job) and that the server does or does not migrate; commands; how to add the next version without editing an applied one. Point table shapes and relationship diagrams at the database design page. Do not paste the ERD here.

## Frontend

**Signals:** `web/`, `frontend/`, `app/`, `pages/`, `src/routes`, Next, Remix, Nuxt, SvelteKit, Angular, React Router, a mobile app.

**Read first:** route files, data-fetch module, API base URL env, auth storage, a client component that mutates, the rewrite or proxy config, the production start command.

**Document:** framework and router; URL → file table and which routes run on the server vs the client; a sequence for the main page (browser → UI server → API); where types come from (hand-written or generated); cache or revalidation if the API calls back; how to run dev and production. State the data store the UI talks to (HTTP, not the database) when that is true.

## End-to-end and other tests

**Signals:** `e2e/`, `cypress/`, `playwright.config.*`, `*.spec.ts`, `tests/`, `*_test.go`, `*_integration_test.go`, k6, CI workflow.

**Read first:** the test config, one spec, the CI jobs, any load script.

**Document:** the user-facing path as a flowchart even when no browser suite exists. Then a table of what actually runs (unit, integration, contract, load) and the command. If Playwright or Cypress is only a transitive dependency, say that. Do not describe a suite that is not in the tree. A "how to add a browser test" note is one short paragraph, not a new framework install, unless the user asked to add tests.

## Database design diagram

**Signals:** SQL or ORM models (`migrations/`, Prisma, Entity Framework, Alembic, `schema.rb`, `*.dbml`), an existing ERD or UML page. The user asked for a database design, ERD, or UML diagram.

**Read first:** the schema source of truth (latest applied migration or model), declared foreign keys and unique keys, indexes that encode access paths, enums or status check constraints, columns that look like foreign keys but are not declared.

**Page:** update an existing diagram page (`ERD.md`, `UML_DATABASE.md`, `database-design.md`) when one is already the schema picture. Otherwise write `docs/database-design.md`. One diagram page. A column-by-column catalog stays a separate data-dictionary page only when the user asked for one or the repo already has one.

**Document:** engine and what this store is the system of record for; ID and tenancy conventions that the schema enforces; a bounded-context table (package or module → tables) when the code groups them; a Mermaid `erDiagram` using real table names, keys, and relationship columns (not every column); cardinality taken from declared foreign keys. Call out relationships the code assumes that are not foreign keys, and why. A second diagram: `flowchart LR` of those contexts, or a `sequenceDiagram` of one write that inserts or updates related rows. Name the migration or model file as the source. Link the migrations page for how a change is applied.

**Do not:** invent tables, paste SQL dumps, or draw a store the tree does not use.

## System design

**Signals:** the user asked for system design. Several processes, stores, or failure paths exist.

**Read first:** entrypoints, the persistence and queue or cache adapters, the status or lifecycle enum, retry or lease logic, and any existing design note so you update it instead of forking it.

**Page:** update an existing system-design page (`SYSTEM_DESIGN.md`, `system-design.md`) when one exists. Otherwise write `docs/system-design.md`. This page is the why: problem, goals, non-goals, invariants, failure behavior, and tradeoffs that the code actually implements. Keep `docs/architecture.md` as the short index. Do not copy the HLD interface list or the LLD function list onto this page.

**Document:** the problem this tree solves, in terms of the features that exist; a goals table whose "how" column names a real type, table, or process; non-goals you can see (a protocol or store the README or code explicitly skips, or a guarantee the code does not make); one `flowchart LR` of clients, processes, and stores; one `sequenceDiagram` of the core job or request; the invariant that keeps those stores consistent; failure modes the code handles (crash, duplicate delivery, store loss) and the recovery path; a short tradeoff table grounded in this tree. Link HLD, LLD, database design, and topic pages instead of repeating them.

**Do not:** describe a scaling tier, region, or product that is not in the tree or the deploy docs.

## High-level design (HLD)

**Signals:** the user asked for an HLD or high-level design.

**Read first:** process entrypoints, the public API surface (HTTP, GraphQL, RPC), the module boundaries, and the external systems each process opens (database, cache, queue, object store).

**Page:** update an existing HLD page (`HLD.md`, `hld.md`) when one exists. Otherwise write `docs/hld.md`. Component responsibilities and the contracts between them. No function bodies, no column lists.

**Document:** one sentence per component (what it owns, what it must not own); a `flowchart LR` of those components with the protocol on the edge (`HTTP /api/v1`, SQL, Redis command family, gRPC service) using names from this repo; a component table (responsibility, entry or port, public or not, state it owns); one `sequenceDiagram` of the main use case naming components, not functions; external dependencies and which component talks to them; boundaries the code enforces (auth, tenant, sync vs async). Link system design for goals and failure modes, and LLD for types and functions.

**Do not:** turn the HLD into a second architecture index or a second system-design essay.

## Low-level design (LLD)

**Signals:** the user asked for an LLD or low-level design.

**Read first:** the use-case type for the main path, the repository or store methods it calls, the handler or resolver that invokes it, the status enum and the transition function, the tables or keys written on that path.

**Page:** update an existing LLD page (`LLD.md`, `lld.md`) when one exists. Otherwise write `docs/lld.md`. How one path is implemented: types, functions, state, and rows. Pick the main path (the write or job the system exists for). Mention sibling paths in one table; do not give every endpoint its own sequence.

**Document:** the types and functions on that path (real names, one job each); a `sequenceDiagram` whose messages are those functions and store calls; a `stateDiagram-v2` or `flowchart TD` when a status enum drives transitions, with the guard the code checks; the tables or keys read and written, in order; error and retry branches that exist in that function; an ordered "how to change" list (domain → persistence → use case → adapter → test). Link the HLD for the box this path sits in and the database design page for relationships.

**Do not:** paste implementations, or restate component boxes that the HLD already drew.

## GraphQL

**Signals:** `schema.graphql`, `*.graphqls`, `*.graphql`, gqlgen, graphql-go, Apollo, Yoga, Pothos, Nexus, Strawberry, Graphene, Ariadne, Hot Chocolate, Absinthe, Tartiflette, a `graphql` dependency used by the server.

**Read first:** the schema file, resolver registration, one query resolver, one mutation resolver, auth or tenant directive, dataloader or batch loader, codegen config and the generate command.

**Page:** update an existing GraphQL page (`graphql.md`) when one exists. Otherwise write `docs/graphql.md`. If the inventory finds no schema and no server, write a short page that says GraphQL is not in this repo and name the endpoint or handler that serves those reads (REST, RPC). Do not invent types, queries, or a server.

**Document:** server library and version from the manifest; schema path; what this API does not replace when REST or RPC also exists; a `flowchart LR` from client → transport → resolver → use case → store; a `sequenceDiagram` of one real query or mutation, including auth; a table of queries, mutations, and subscriptions that exist (name, resolver, auth); where types come from (hand-written schema or code-first) and the generate command; N+1 handling if a dataloader exists; how to add a field (schema → resolver → use case → regenerate → caller). State whether the route is public.

**Do not:** document a GraphQL client that only calls a third-party API as this repo's server. That is a frontend data call; mention it on the frontend page.

## Index page

When you write more than one topic page, add `docs/architecture.md`:

- one system flowchart
- a component table (role, port or entry, public or not)
- the request paths in a few numbered lines that link to the topic pages
- a layout tree of the directories you documented
- runtime modes (local, compose, cluster) that exist

Link that index from the README. When a commands page was written, link it from `docs/architecture.md` and the README list.

System design, HLD, LLD, database design, and GraphQL are topic pages, not extra copies of the index. Link each one from `docs/architecture.md` when it was written. Share one flowchart across those pages only as a link back to the index; each topic page keeps the diagram the playbook names. Write a design page only when the user asked for that topic.
