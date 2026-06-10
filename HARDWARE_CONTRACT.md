# Sentry Hardware Contract

Status: active
Owner: Jean Neftin
Layer: hardware
Created: 2026-06-10

## Purpose

Sentry Hardware is the repository for AI-assisted physical systems: devices, sensors, firmware, edge AI experiments, hardware demos, and client-applicable prototypes.

Its job is to turn practical hardware ideas into reproducible builds that can assist the operator and clients in the physical world.

## Layer Boundary

Sentry Hardware owns:

- hardware project briefs
- prototype architecture
- firmware and board-level code
- sensor selection and validation notes
- bill of materials
- wiring, enclosure, and assembly notes
- edge AI model experiments tied to hardware behavior
- test logs, measurements, photos, and demo evidence
- contest and client demo artifacts

Sentry Hardware does not own:

- Sentry-Stack platform architecture
- Control Room governance
- Index navigation rules
- production task orchestration
- Sentry-Stack source-of-truth docs
- client private records unless explicitly approved and scoped

Sentry-Stack can support hardware projects through APIs, dashboards, retrieval, storage, observability, or orchestration only after an explicit integration plan is written.

## Active Project: Facility Intelligence Pods

The first active project is a modular Arduino UNO Q sensor pod for facility and warehouse intelligence.

Working concept:

- modular battery-powered or wired pods
- Arduino UNO Q and App Lab as the core development target
- sensors for temperature, humidity, sound, vibration, and possibly camera/video
- edge AI for anomaly detection and classification
- WiFi and possibly LoRa or mesh connectivity
- central dashboard for real-time monitoring and alerts
- facility, warehouse, cold storage, manufacturing, hospital, data center, construction, and property management use cases

Primary near-term goal:

Produce a credible final hardware design and contest submission package for the Arduino UNO Q / App Lab Hackster contest.

Dates:

- internal target: 2026-08-28
- contest close date to verify against Hackster: 2026-08-30 23:59 PDT

## Authority Order

When working in this repository, use this order:

1. `HARDWARE_CONTRACT.md` - active contract for this repository
2. `AGENTS.md` - bootstrap instructions for agents and executors
3. active project files under this repository
4. verified vendor documentation and contest rules
5. notes, drafts, and scratch files

Sentry-Stack documents can inform integration choices, but they do not override this hardware contract inside this repository.

## Safety Rules

- Treat electrical, battery, charging, wireless, enclosure, and installation details as safety-sensitive.
- Verify voltage, current, pinout, connector, thermal, and battery assumptions from primary documentation before implementation.
- Mark unverified hardware assumptions as unknown.
- Do not recommend deployment in a client site until a bench test and field-test checklist exist.
- Do not use hidden network credentials or secret-bearing files in examples.
- Do not make irreversible changes to hardware artifacts. Archive superseded versions with a reason.

## Done Criteria

A hardware task is done only when the session reports:

- artifact produced or changed
- files changed
- verification performed or clear reason verification was skipped
- remaining unknowns
- next smallest useful hardware step
- git status and backup state

## Backup Contract

The canonical backup remote is:

`https://github.com/jneftin/sentry_hardware`

The local folder is:

`C:\Users\Jean Neftin\Desktop\Sentry_hardware`

Meaningful work should be committed and pushed after operator approval, unless the operator asks for a direct backup action in the same turn.
