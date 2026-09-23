# AGENTS.md — shared working rules

This repository may be worked on by ChatGPT/Codex agents.


## Project prioritization and planning autonomy

Agents are expected to help manage the order of work, not merely react to the
latest idea mentioned in chat.

A user question, idea or suggestion is **input to planning**, not automatically
an instruction to implement it immediately. Unless the user explicitly asks to
execute it now, the agent should decide whether it belongs in:

- **NOW** — required for the current milestone or blocking progress,
- **NEXT** — the next logical dependency after the current milestone,
- **LATER / TODO** — useful, but should not interrupt the current work,
- **PARKED** — intentionally deferred until prerequisite work is complete.

Choose the next work item using project context, including:

1. safety and reversibility,
2. unfinished acceptance gates or milestones,
3. technical dependencies,
4. architectural coherence and reuse,
5. risk of regressions,
6. testability and observability,
7. value relative to implementation cost,
8. whether starting something new would leave important work half-finished.

Prefer completing and documenting an in-progress milestone before opening an
unrelated implementation thread.

It is valid to tell the user that an idea is good but should be deferred, and
to record it in TODO/roadmap/handoff instead of implementing it immediately.

Do **not** infer urgency from a casual question. If the user clearly says to
change priority, implement something now, or stop current work, follow that
explicit direction unless a safety-critical conflict requires clarification.

This is **autonomous sequencing, not autonomous scope expansion**. Agents may
choose the best order of already relevant project work, but must not silently
invent new project goals.

Keep the roadmap/TODO/handoff updated when a suggestion materially changes the
planned sequence. The user can redirect priorities at any time.

## Mandatory terminal exchange workflow

For interactive work involving a terminal, SSH session, shell script, Python
snippet, deployment or diagnostics, **do not paste long multi-line command
blocks through chat** when the task can be executed from a file.

Long pasted blocks can be corrupted by browser/chat paste and may produce
malformed commands or misleading failures.

Use a GitHub live-exchange channel instead:

- operational branch: `ops/live-exchange`
- preferred script name: `EXCHANGE.sh`
- a target-specific name such as `EXCHANGE_VM108.sh` is also allowed

Expected agent behavior:

1. Inspect the current state and decide the next safe step.
2. Update the exchange script on `ops/live-exchange`.
3. Keep each script focused on one operational action or verification gate.
4. Ask the user to run only a short fetch/show/execute command.
5. Read the returned output before publishing the next exchange step.
6. Keep project documentation and handoff evidence current.
7. Never put passwords, API keys, tokens, private keys or other secrets in the
   exchange script or repository.

Typical local execution pattern:

```bash
git fetch origin ops/live-exchange
git show FETCH_HEAD:EXCHANGE.sh | bash
```

Typical remote execution pattern:

```bash
git fetch origin ops/live-exchange
git show FETCH_HEAD:EXCHANGE.sh | ssh user@target 'bash -s'
```

The `ops/live-exchange` branch is an operational scratch channel only.
**Never treat it as the release/source-of-truth branch.** Release identity,
accepted commits, package hashes and production configuration must remain
defined by the project's normal branch/tag/release documentation.

Prefer this workflow whenever a command would otherwise require more than a few
short lines, especially for heredocs, embedded Python, deployment scripts or
multi-step diagnostics.

## Safety and project-specific rules

This shared workflow does not override project-specific safety requirements.
Read the repository's README, handoff and safety documentation before making
changes or operating external systems.
