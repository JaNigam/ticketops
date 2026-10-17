# TicketOps Agent: Project Documentation

> A free, open-source, learn-by-building project that teaches agentic AI engineering at senior-engineer depth.
> Companion file: `plan.md` (schedule, tasks, checklists). This file explains **what we build and why**.

---

## 1. Purpose

Two goals, one project:

1. **Learn** the concepts AI/Agent Engineer roles test: agent loops, tools and MCP, orchestration, RAG, memory, event-driven backends, real-time streaming, evals, guardrails, observability, security, deployment, and system design.
2. **Produce** a portfolio-grade flagship project with measured results (eval scores, cost and latency numbers, a failure write-up) that you can defend in interviews.

## 2. What we are building

**TicketOps** is a resolution agent for customer-support tickets. A ticket arrives (via webhook), the agent investigates by calling business tools (orders, customers, refunds), retrieves the relevant policy, decides what to do, and either resolves it or pauses for human approval when the action is risky. Reviewers watch the agent work live and approve or reject actions from a web console.

**Example flow**

1. External system sends `POST /webhooks/tickets` ("my order arrived damaged, I want a refund").
2. The gateway verifies the signature, deduplicates by idempotency key, stores the ticket, and enqueues a job.
3. A worker picks up the job and runs the agent graph.
4. The agent calls tools (via MCP) to fetch the order and customer history, and retrieves the refund policy (RAG).
5. It proposes an action. Low-risk actions execute automatically; risky ones pause at an approval node.
6. Progress events stream to the React console over WebSocket. A reviewer approves or rejects.
7. The graph resumes from its checkpoint, the Java tool layer enforces limits and executes, and an outbound webhook announces the result.

## 3. Ground rules

- **Free and open source only.** No paid APIs, no paid SaaS. Everything runs locally or in free tiers of open-source tools.
- **Personal project, personal machine.** Use generated or public data only. Never use employer code, data, accounts, or hardware.
- **Learn, then build.** Each module starts with a detailed lesson (taught in chat), then hands-on tasks, then a verification checklist.
- **Each module ships one increment.** The project grows in nine slices (Module 0 to Module 8). Nothing is thrown away.
- **Own your code.** Existing code style and naming are preserved when reviewing; targeted fixes over rewrites.

## 4. Architecture

```
                  +-----------------------------+
 External systems | Webhook simulator / helpdesk|
                  +--------------+--------------+
                                 | HTTPS + HMAC signature
                                 v
+--------------------------------------------------------------+
|  Spring Boot "gateway + tool layer" (Java 21)                |
|  - Webhook receiver (verify, dedupe, store, enqueue)         |
|  - MCP server: order / customer / refund tools + guards      |
|  - WebSocket (STOMP) gateway to the console                  |
|  - Outbound webhook dispatcher (retries, DLQ)                |
|  - Audit log, authN/authZ (Keycloak JWT)                     |
+-----+---------------------+------------------+---------------+
      | enqueue             | MCP (tools)      | events (pub/sub)
      v                     v                  v
+-----------+       +-------------------------------+     +--------------+
| Valkey    |<----->|  Python agent worker          |---->| React console|
| streams + |       |  LangGraph graph + raw loop   |     | (Vite + TS)  |
| pub/sub   |       |  RAG, memory, guardrails      |     +--------------+
+-----------+       +---------------+---------------+
                                    |
                    +---------------+----------------+
                    v                                v
            +---------------+                +---------------+
            | PostgreSQL    |                | Ollama (local |
            | + pgvector    |                | LLM runtime)  |
            +---------------+                +---------------+

 Cross-cutting: OpenTelemetry -> Jaeger / Prometheus / Grafana
```

**Why two languages?** Java owns the *system of record and the safety boundary* (data, permissions, webhooks, sockets), which is where your strength is and where senior-level judgment shows. Python owns the *agent logic* because the agent ecosystem lives there. The boundary between them (MCP and the queue) is itself a design lesson.

## 5. Tech stack (all free / open source)

| Layer | Choice | Why | License / cost |
|---|---|---|---|
| LLM runtime | **Ollama** with a tool-calling-capable open model (Qwen or Llama family) | Local, free, no API keys, OpenAI-compatible API | MIT / free |
| LLM fallback (optional) | Free tiers of hosted APIs (e.g. Gemini, Groq) behind one interface | For weak hardware; limits change, so check current terms | Free tier |
| Embeddings | `nomic-embed-text` via Ollama, or `sentence-transformers` | Local embeddings | Open source |
| Agent logic | **Python 3.11+**, raw loop first, then **LangGraph** | Learn the loop, then the framework | MIT |
| Tool layer | **Java 21, Spring Boot 3**, Spring AI MCP server starter or the official MCP Java SDK | Safety boundary and system of record | Apache 2.0 |
| Database | **PostgreSQL 16 + pgvector** | Relational data, vectors, and LangGraph checkpoints in one engine | Open source |
| Queue / pub-sub | **Valkey** (BSD fork of Redis; same commands) with Streams | Queues, consumer groups, pub/sub, caching | BSD |
| Real-time | Spring WebSocket + STOMP (SSE for comparison) | Live traces and approvals | Apache 2.0 |
| Frontend | **React + Vite + TypeScript** | Reviewer console | MIT |
| Auth | **Keycloak** (OAuth2 / OIDC / JWT) | Realistic senior-level security | Apache 2.0 |
| Observability | **OpenTelemetry**, Jaeger, Prometheus, Grafana | Traces, metrics, dashboards | Open source |
| Evals | `pytest` + custom harness (optionally promptfoo or DeepEval) | Regression-gated quality | Open source |
| Containers | Docker Engine / Colima / Podman, **docker compose** | Local infra | Free (see note) |
| Kubernetes | **kind** (Kubernetes in Docker) | Practice deployments locally | Apache 2.0 |
| CI/CD | **GitHub Actions** | Free for public repos | Free tier |

**Docker note:** Docker Desktop is free for personal use, but has licensing limits for larger companies. On a work machine, avoid it; on a personal machine either is fine. Colima, Podman, and plain Docker Engine are fully free alternatives.

**Hardware note:** a quantized 7-8B parameter model wants roughly 8 GB of free RAM; a 3B model runs on much less. Start small and move up if answers are poor. Check the Ollama library for current tool-capable models and confirm tool support before relying on one.

## 6. Repository layout

```
ticketops/
  docs/                   documentation.md, plan.md, ADRs, notes
  services/
    tools-java/           Spring Boot: gateway + MCP tools (Module 2+)
    agent-py/             Python: agent loop, LangGraph, worker (Module 1+)
    console-web/          React console (Module 5)
  evals/                  datasets, harness, reports (Module 6)
  infra/
    postgres/             init.sql
    k8s/                  manifests (Module 7)
  scripts/                helpers (simulator, seeders)
  docker-compose.yml
  .env.example
```

## 7. Design principles (interview talking points)

1. **Enforce safety in the tool layer, not the prompt.** Prompts can be bypassed; code cannot. Refund limits, allowlists, and audit logs live in Java.
2. **Verify, don't trust.** Model output is untrusted input: validate against schemas before acting.
3. **Idempotent everything.** Webhooks and queue messages are delivered at least once; handlers must tolerate duplicates.
4. **Resumable by design.** Long-running agent runs checkpoint state so crashes and approval pauses are routine.
5. **Observable end to end.** One trace ID follows a ticket across webhook, queue, agent, tools, and console.
6. **Measure before claiming.** Every behavior claim is backed by an eval number.
7. **Least privilege.** The agent gets only the tools and scopes the task needs.

## 8. Domain model (initial)

| Entity | Key fields |
|---|---|
| `customer` | id, name, email, tier, created_at |
| `order` | id, customer_id, status, total, placed_at, delivered_at |
| `order_item` | id, order_id, sku, qty, price |
| `ticket` | id, external_id (idempotency key), customer_id, subject, body, status, created_at |
| `refund` | id, order_id, amount, status (proposed / approved / executed / rejected), reason |
| `approval` | id, ticket_id, action, status, reviewer, decided_at |
| `audit_log` | id, actor, action, payload, ticket_id, created_at |
| `policy_chunk` | id, doc, text, embedding (vector), metadata |
| `agent_event` | id, ticket_id, run_id, type, payload, ts |

## 9. Event contracts (initial)

- **Inbound webhook** `ticket.created`: `{ "id", "customer_email", "subject", "body", "created_at" }` with headers `X-Signature` (HMAC-SHA256), `X-Timestamp`, `X-Idempotency-Key`.
- **Queue message** `ticket.process`: `{ "ticket_id", "trace_id", "attempt" }`.
- **Console events** (WebSocket): `run.started`, `step.tool_call`, `step.tool_result`, `approval.requested`, `run.completed`, `run.failed`.
- **Outbound webhook** `ticket.resolved` / `ticket.escalated`: signed payload with outcome and audit reference.

## 10. Concept index by module

| Module | Core concepts |
|---|---|
| 0 Setup | Monorepo, containers, local LLM runtime, config management |
| 1 Agent foundations | LLM API anatomy, tokens and context, function calling, structured outputs, ReAct, plan-and-execute, reflection, stop conditions |
| 2 Tools and MCP | Tool design, MCP architecture and transports, write-guards, audit logging, dry-run patterns |
| 3 Orchestration, RAG, memory | LangGraph state machines, checkpointing, human-in-the-loop, embeddings, vector search, agentic RAG, memory types |
| 4 Event-driven backend | Webhooks, HMAC, idempotency, delivery semantics, queues, retries, backoff, DLQ, outbox |
| 5 Real-time and console | WebSocket vs SSE, STOMP, pub/sub fan-out, reconnect and replay |
| 6 Evals and guardrails | Golden sets, LLM-as-judge, trajectory evals, non-determinism, prompt injection, red-teaming |
| 7 Observability, security, production | OpenTelemetry, SLOs, OAuth2/JWT, Kubernetes basics, CI/CD, rate limiting, caching |
| 8 Multi-agent, design, interviews | Supervisor/worker, handoffs, system design framework, ADRs, behavioral stories |

## 11. Glossary

- **Agent loop:** repeat (call model, run tool, append result) until a final answer or a stop condition.
- **Tool call:** the model's structured request to run a named function with arguments.
- **MCP:** Model Context Protocol, an open standard for exposing tools, resources, and prompts to AI clients.
- **Checkpoint:** a saved snapshot of graph state that allows pause and resume.
- **HITL (human-in-the-loop):** deliberately pausing for a human decision before a risky step.
- **RAG / agentic RAG:** retrieving relevant documents to ground answers; in the agentic form the model decides when and what to retrieve.
- **Idempotency:** repeating an operation has the same effect as doing it once.
- **At-least-once delivery:** a message may arrive more than once, never zero times, so consumers must dedupe.
- **DLQ:** dead-letter queue for messages that keep failing.
- **HMAC:** keyed hash used to prove a webhook came from a trusted sender and was not altered.
- **Outbox pattern:** write the event to the database in the same transaction as the state change, then publish it separately, so events are never lost.
- **Trajectory eval:** judging the sequence of steps an agent took, not just the final answer.
- **LLM-as-judge:** using a model to grade outputs against a rubric.
- **Prompt injection:** attacker-controlled text that tries to override the agent's instructions.
- **SSE vs WebSocket:** SSE is one-way server-to-browser over HTTP; WebSocket is two-way.

## 12. Interview mapping

| Interview topic | Where this project gives you a story |
|---|---|
| "Write an agent loop" | Module 1 raw loop |
| "How do you make agents safe?" | Module 2 write-guards, Module 6 injection suite |
| "How do you evaluate an agent?" | Module 6 harness and scorecard |
| "Design an LLM support system" | Modules 3 to 5 architecture |
| "Webhooks, queues, retries" | Module 4 |
| "Single vs multi-agent?" | Module 8 comparison report |
| "Production readiness" | Module 7 observability, auth, CI/CD |
