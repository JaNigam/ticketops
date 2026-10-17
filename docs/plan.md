# TicketOps Agent: Learning and Build Plan

> Companion file: `documentation.md` (architecture, stack, conventions).
> Budget: **12 weeks at 6-10 hours per week** (about 100 hours). Everything is free and open source.

---

## How each module works

Every module follows the same four steps:

1. **Learn:** a detailed lesson in chat (concepts, why, trade-offs, pitfalls). Read it before touching code.
2. **Build:** hands-on tasks that add one increment to TicketOps.
3. **Verify:** a "done when" checklist. Do not move on until every box is ticked.
4. **Drill:** interview questions on the module. Answer them out loud or in writing, then paste for review.

**Review loop:** paste your code or trace into chat and I review it like an interviewer: what works, what breaks, what to tighten. Targeted fixes, not rewrites of your style.

---

## Roadmap at a glance

| # | Module | Weeks | Increment shipped | Project progress |
|---|---|---|---|---|
| 0 | Setup and foundations | 1 | Repo, infra, local LLM, hello-world across layers | 1/9 |
| 1 | Agent foundations | 1-2 | Raw agent loop with validated tools and traces | 2/9 |
| 2 | Tools and MCP | 3 | Java MCP server with guarded tools on Postgres | 3/9 |
| 3 | Orchestration, RAG, memory | 4-5 | LangGraph ticket graph with policy RAG and approval pause | 4/9 |
| 4 | Event-driven backend | 6-7 | Webhooks in and out, queue, resumable worker | 5/9 |
| 5 | Real-time and console | 8 | WebSocket live trace and React approval console | 6/9 |
| 6 | Evals and guardrails | 9 | Eval harness, injection suite, CI gate | 7/9 |
| 7 | Observability, security, production | 10-11 | Tracing, Keycloak auth, Kubernetes, CI/CD | 8/9 |
| 8 | Multi-agent, design, interviews | 12 | Multi-agent comparison, final polish, interview kit | 9/9 |

---

## Weekly rhythm (about 8 hours)

| Block | Hours | What |
|---|---|---|
| Learn | 1.5 | Read the lesson, take notes |
| Build | 4 | Module tasks |
| DSA | 1 | 2-3 problems per week, steady |
| Design and interview prep | 1 | System design practice (from week 4), behavioral stories (from week 8) |
| Notes and writing | 0.5 | Update learning log, commit messages, README |

**Parallel tracks**
- **DSA:** 2-3 problems per week throughout; increase in the last 4-5 weeks.
- **System design:** one timed mock per week from week 4.
- **Behavioral:** write 6 stories (impact, ownership, conflict, failure) during weeks 8-12.
- **Applications:** start referral outreach around week 6; begin applying in waves around week 8-9.

---

## Module 0: Setup and foundations (Week 1)

**Learn:** monorepo structure, containers and compose, what a local LLM runtime is, environment configuration, why we pin versions.

**Build**
- [ ] Install prerequisites: Git, JDK 21 (Temurin), Maven, Python 3.11+, Node 20+, a container runtime, Ollama
- [ ] Run `bootstrap.sh` to create the repo skeleton, then `git init` and first commit
- [ ] `docker compose up -d` starts Postgres (with pgvector) and Valkey
- [ ] Pull a small tool-capable model with Ollama and call it from a Python script
- [ ] Generate a Spring Boot project (Web, Actuator, JPA, PostgreSQL driver) in `services/tools-java`
- [ ] Create a GitHub repo and push

**Done when**
- [ ] `docker compose ps` shows both services healthy
- [ ] Python script prints a model reply
- [ ] `curl localhost:8080/actuator/health` returns `UP`
- [ ] Code is pushed to GitHub

**Drill:** What does `docker compose` give you over running services by hand? Why pgvector instead of a separate vector database at this scale?

---

## Module 1: Agent foundations (Weeks 1-2)

**Learn:** anatomy of an LLM API call, roles and messages, tokens and context windows, function calling, structured outputs with JSON schema and Pydantic, the agent loop, ReAct, plan-and-execute, reflection, stop conditions, error handling, why logging every step matters.

**Build** (`services/agent-py/`)
- [ ] Two fake tools: `get_order(order_id)` and `check_refund_policy(order_id)`
- [ ] Raw agent loop, **no framework**, with `MAX_STEPS`, token budget, and timeout
- [ ] Tool arguments validated with Pydantic before execution
- [ ] Tool errors returned to the model as tool results
- [ ] JSON trace per run: step, tool, args, result, latency, tokens
- [ ] Three test tickets: simple refund, bad order ID, vague ticket with no order ID

**Done when**
- [ ] All three tickets end in a sensible final answer or a clean escalation
- [ ] A runaway loop is stopped by the limits (prove it with a deliberate test)
- [ ] Traces are saved and readable

**Drill:** Write the agent loop from memory. ReAct vs plan-and-execute: when does each win? What stops an agent from looping forever?

---

## Module 2: Tools and MCP (Week 3)

**Learn:** principles of good tool design (names, descriptions, granularity, idempotency, error messages), MCP architecture (host, client, server; tools, resources, prompts; stdio vs streamable HTTP), mapping JPA entities to tools, authorization and write-guards, dry-run and approval patterns, audit logging.

**Build** (`services/tools-java/`)
- [ ] Schema and seed data: customers, orders, order items, refunds, audit log (Flyway or Liquibase migrations)
- [ ] MCP server exposing: `get_order`, `get_customer_history`, `propose_refund` (dry-run), `execute_refund` (guarded)
- [ ] Guards in Java: refund limit per tier, order-state checks, one refund per order, every write audited
- [ ] Python agent connects as an MCP client and replaces the fake tools

**Done when**
- [ ] The agent resolves a refund ticket end to end against Postgres
- [ ] A refund above the limit is rejected by Java **even if the prompt says to approve it**
- [ ] Every write appears in `audit_log`
- [ ] Tool descriptions were revised at least once based on observed model mistakes

**Drill:** Why enforce limits in the tool layer instead of the prompt? How would you design tools so a weak model still uses them correctly? Stdio vs HTTP transport: trade-offs?

---

## Module 3: Orchestration, RAG, and memory (Weeks 4-5)

**Learn:** LangGraph (state, nodes, edges, conditional routing, reducers), checkpointing with a Postgres checkpointer, human-in-the-loop interrupts, embeddings, chunking strategies, vector search with pgvector, hybrid search, reranking basics, citations, agentic RAG, short-term vs long-term memory, summarization, workflow vs autonomous agent.

**Build**
- [ ] Policy documents (write 8-10 realistic refund, shipping, and warranty policies) chunked and embedded into `policy_chunk`
- [ ] Retrieval tool that returns chunks with source IDs
- [ ] LangGraph graph: classify, retrieve policy, plan, act, approval interrupt, respond
- [ ] Postgres checkpointer so runs persist
- [ ] Per-customer long-term memory (past tickets summarized and retrievable)
- [ ] Answers cite the policy chunk they relied on

**Done when**
- [ ] Graph pauses at the approval node and **resumes after you restart the process**
- [ ] Every policy-based decision includes a citation
- [ ] Context stays bounded on a long ticket thread (summarization works)

**Drill:** Explain checkpointing and why it enables human approval. Chunk size trade-offs? When is a fixed workflow better than a free agent? How do you reduce hallucinated policy claims?

---

## Module 4: Event-driven backend (Weeks 6-7)

**Learn (from first principles):** sync vs async systems; webhooks; HMAC signing, timestamp tolerance, replay protection; idempotency keys; at-most-once vs at-least-once vs exactly-once; queues and streams (Valkey Streams, consumer groups, acknowledgements, pending entries); retries with exponential backoff and jitter; dead-letter queues; the outbox pattern; backpressure; resumable jobs.

**Build**
- [ ] `POST /webhooks/tickets` in Spring Boot: verify signature and timestamp, dedupe by idempotency key, store ticket, enqueue
- [ ] Python worker consuming a Valkey stream via a consumer group, running the agent graph
- [ ] Outbound webhook dispatcher: signed payloads, retries with backoff and jitter, DLQ
- [ ] `scripts/simulator`: sends signed ticket webhooks (including duplicates and bad signatures)
- [ ] Tiny receiver stub that can be told to fail on purpose

**Done when**
- [ ] A duplicate webhook does not create a duplicate ticket or a second agent run
- [ ] A bad signature or stale timestamp is rejected
- [ ] Killing the worker mid-run leads to the job being retried and completed
- [ ] A failing receiver causes retries, then a DLQ entry you can inspect

**Drill:** Why is exactly-once delivery a myth, and how do you get "effectively once"? Design a webhook system with retries. What is the outbox pattern and what problem does it solve? Queue vs pub/sub?

---

## Module 5: Real-time and console (Week 8)

**Learn:** WebSocket vs SSE vs long polling, STOMP, pub/sub fan-out, event schemas, reconnect and replay, authentication on sockets, backpressure, streaming state in React.

**Build** (`services/console-web/`)
- [ ] Agent worker publishes `agent_event` messages to Valkey pub/sub and stores them
- [ ] Spring Boot WebSocket (STOMP) gateway fans events out to subscribers
- [ ] React console: ticket list, live trace view, pending-approvals panel
- [ ] Approve and reject buttons that resume the paused graph
- [ ] Reconnect logic that replays missed events by last event ID

**Done when**
- [ ] A trace step appears in the browser within about a second
- [ ] Approving from the UI resumes the run and the result appears live
- [ ] Refreshing the page or dropping the network loses no events

**Drill:** WebSocket vs SSE: when each? How do you scale a socket gateway horizontally? How do you avoid losing events on reconnect?

---

## Module 6: Evals and guardrails (Week 9)

**Learn:** eval layers (tool-level, task success, trajectory), golden dataset design, LLM-as-judge and its biases, handling non-determinism (fixed seeds, repeated runs, confidence intervals), regression gates, direct vs indirect prompt injection, least privilege, content isolation, red-teaming.

**Build** (`evals/`)
- [ ] 60+ labeled scenarios: easy, ambiguous, policy edge cases, adversarial
- [ ] Runner that executes scenarios and records outcome, tool-call correctness, unnecessary calls, escalation correctness, cost, latency
- [ ] LLM-as-judge for free-text quality, checked against a hand-labeled sample
- [ ] Injection suite (ticket text, order notes, retrieved documents)
- [ ] One-command scorecard report and a CI job that fails on regression

**Done when**
- [ ] `make eval` (or equivalent) prints a scorecard
- [ ] The injection suite shows **zero unauthorized actions**
- [ ] You can show a before/after number from a prompt or tool change

**Drill:** How do you evaluate a non-deterministic agent? What are the failure modes of LLM-as-judge? Walk through defending against indirect prompt injection.

---

## Module 7: Observability, security, and production (Weeks 10-11)

**Learn:** OpenTelemetry (traces, metrics, logs), context propagation across services and queues, SLIs and SLOs, cost and latency budgets; OAuth2, OIDC, JWT, service-to-service auth, secrets handling; Docker multi-stage builds; Kubernetes basics (deployments, services, config maps, probes, autoscaling); CI/CD with GitHub Actions; rate limiting, caching, scaling.

**Build**
- [ ] OpenTelemetry in Java and Python, with the trace ID carried through the queue
- [ ] Jaeger, Prometheus, and Grafana in compose; dashboard for latency, cost per ticket, error rate, queue depth
- [ ] Keycloak secures the console and APIs (JWT); service-to-service tokens for the worker
- [ ] Rate limiting on the webhook endpoint; caching for hot reads
- [ ] Multi-stage Dockerfiles; Kubernetes manifests; deploy to a local `kind` cluster
- [ ] GitHub Actions: build, unit tests, eval gate, container build

**Done when**
- [ ] One trace spans webhook, queue, worker, tool call, and approval
- [ ] Unauthenticated requests are rejected; role checks work
- [ ] One command deploys the system to `kind`
- [ ] CI runs tests and evals on every push

**Drill:** How do you trace a request across an async queue? JWT vs opaque tokens? What would you alert on for an LLM system? Walk through a zero-downtime deploy.

---

## Module 8: Multi-agent, system design, and interviews (Week 12)

**Learn:** supervisor/worker pattern, handoffs, shared state, cost vs quality trade-offs; a repeatable LLM system design framework; general high-level design patterns (rate limiter, notification system, queue-based pipelines); writing design docs and ADRs; behavioral story structure; framing the project and your day-job experience at senior scope.

**Build**
- [ ] Supervisor-plus-specialists variant of the ticket graph
- [ ] Run both variants through the eval suite; write a comparison report (accuracy, cost, latency)
- [ ] Final README: architecture diagram, eval results, failure analysis ("what broke and how I fixed it")
- [ ] 3-minute demo video and one blog post
- [ ] Interview kit: 8 LLM system design questions practiced, 6 behavioral stories, a project deep-dive script

**Done when**
- [ ] Comparison numbers are published in the repo
- [ ] Six timed design mocks completed and reviewed
- [ ] You can explain every design decision and its trade-off without notes

---

## Progress tracker

| Module | Lesson read | Tasks done | Verified | Drill reviewed | Date finished |
|---|---|---|---|---|---|
| 0 Setup | [ ] | [ ] | [ ] | [ ] | |
| 1 Agent foundations | [ ] | [ ] | [ ] | [ ] | |
| 2 Tools and MCP | [ ] | [ ] | [ ] | [ ] | |
| 3 Orchestration, RAG, memory | [ ] | [ ] | [ ] | [ ] | |
| 4 Event-driven backend | [ ] | [ ] | [ ] | [ ] | |
| 5 Real-time and console | [ ] | [ ] | [ ] | [ ] | |
| 6 Evals and guardrails | [ ] | [ ] | [ ] | [ ] | |
| 7 Observability and production | [ ] | [ ] | [ ] | [ ] | |
| 8 Multi-agent and interviews | [ ] | [ ] | [ ] | [ ] | |

---

## Rules of engagement

- Do not skip the "Done when" checks; they are what make each increment solid.
- If a module runs over, cut scope inside it (fewer scenarios, fewer tools) before cutting the Verify or Drill steps.
- If you fall behind by more than a week, merge Module 5 into a lighter version (SSE only) rather than dropping evals. Evals are the strongest interview signal.
- Keep a short learning log: what you built, what broke, what you learned. It becomes your blog post and interview material.
- Commit after every working step; small commits make debugging and storytelling easier.
