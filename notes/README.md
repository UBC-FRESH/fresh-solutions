# Notes

Notes are the persistent, agent-friendly context for this project. They hold what a future reader, human or agent, needs and cannot get from the code, the issues, or the changelog alone.

- `notes/adr/NNNN-slug.md`: decisions. One decision per file. Never rewrite an accepted ADR; supersede it with a new one. Start from `adr/0000-template.md`.
- `notes/reference/`: facts with provenance. Record where each fact came from, how it was read, and what is uncertain.
- `notes/`: focused plans that are too long for `ROADMAP.md`. Link each one from its roadmap task, and keep it current while the task is active.
- `notes/reports/`: the close-out report for each phase. Start from `reports/phase-closeout-template.md`. The report is the evidence for the maintainer's approval.

Keep private material out of this directory.

- `design/architecture.md`: adapter boundary, hybrid handoff, and contract tests.

- `reports/heuristic-progression.md`: staged design/evidence progression from generic moves to QAP tabu and Or-opt, including negative 3-opt result.
- `reports/shared-kernel-retrofit-closeout.md`: cross-repo closeout for the kernel extraction, 0.9.3 release, WS4/FHOPS adoption, and the papers pin.
