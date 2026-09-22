# AGENTS.md — shared working rules

This repository may be worked on by ChatGPT/Codex agents.

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
