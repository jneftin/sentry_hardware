# Sentry Hardware Agent Instructions

This repository is the hardware layer for AI-assisted physical systems used by the operator and clients.

Before answering, planning, or editing in this repository, read:

`C:\Users\Jean Neftin\Desktop\Sentry_hardware\HARDWARE_CONTRACT.md`

## Role Of This Repository

Use this repository for hardware-facing work:

- Arduino UNO Q and App Lab projects
- sensor pod design
- firmware, sketches, Python scripts, and edge AI model notes
- bill of materials and part research
- enclosure and wiring notes
- field test logs
- client-ready hardware demos
- contest deliverables and submission materials

This repository is separate from:

- `C:\Users\Jean Neftin\Desktop\Sentry-Stack` - local-first AI platform source of truth
- `C:\Users\Jean Neftin\Desktop\Sentry_Stack_Control_Room` - governance and dispatch layer
- `C:\Users\Jean Neftin\Desktop\Sentry_Stack_Index` - navigational map only

Sentry-Stack may later provide backend APIs, dashboards, storage, retrieval, analysis, or dispatch for hardware projects, but only through explicit integration tasks or contracts. Do not silently make Sentry-Stack depend on this repository, and do not silently make this repository depend on Sentry-Stack.

## Current Primary Project

The first active hardware project is the Arduino UNO Q facility and warehouse intelligence pod:

- contest: Invent the Future with Arduino UNO Q and App Lab
- scenario: Industrial IoT / smart predictive maintenance
- concept: modular sensor pods for facility telemetry, edge AI, alerts, and dashboarding
- internal target: August 28, 2026
- external contest close date to verify: August 30, 2026 at 11:59 PM PDT

## Working Rules

- Keep instructions agent-agnostic. Use role language such as operator, session agent, coding executor, hardware builder, firmware executor, and review agent.
- Preserve hardware evidence. Do not delete notes, test results, photos, wiring references, CAD files, or failed prototype records. Archive instead.
- Do not guess electrical specs, pinouts, current limits, charging behavior, sensor tolerances, battery safety, or contest requirements. Verify them from primary sources or mark them unknown.
- Do not claim hardware has been tested unless there is a test log, photo, video, measurement, or reproducible command.
- Do not store secrets, WiFi credentials, API keys, client private data, or contest account credentials in this repo.
- Before changing firmware, wiring, power, or physical design instructions, state the expected files, verification plan, and safety assumptions.
- For client hardware work, separate generic reusable design from client-specific details.

## GitHub Backup Rule

This repository should back up to:

`https://github.com/jneftin/sentry_hardware`

Every meaningful editing session should end with:

1. `git status --short --branch`
2. commit-ready summary of changed files
3. operator decision if changes should be committed or pushed

Do not force-push, rewrite history, delete branches, or remove remote content unless the operator explicitly asks for that exact action.
