# insight

Contributions to [Project Insight](https://project-insight-science.learn.joinhandshake.com/) — a
program for building hard, realistic, domain-specific terminal tasks that measure what AI agents
can actually do.

The upstream program is Terminal-Bench-Science (Stanford / Harbor / Laude Institute). Tasks are
authored in the [Harbor task format](https://harborframework.com/docs/task-format) and submitted as
pull requests to `harbor-framework/terminal-bench-science`.

## Layout

```
docs/
├── PROJECT-INSIGHT-BRIEF.md       what the program is, the rubric, the taxonomy, the CI pipeline
├── PROPOSAL-TEMPLATE.md           the fill-in template for a new proposal
├── PRE-SUBMISSION-CHECKLIST.md    39-criterion implementation rubric + 33 static checks, actionable
└── proposals/
    ├── README.md                  conventions, status values, index
    └── 2026-10-21-cahn-hilliard-mobility/
        ├── PROPOSAL.md            the submitted text (current revision)
        ├── PROPOSAL-v0.md         superseded draft, kept for history
        ├── REVIEW.md              rubric evaluation + ranked fixes
        └── NOTES.md               internal: pilot study plan, open design questions
```

## Workflow

1. **Ideate** — pick a domain/field, find a gap among the merged tasks, ground it in real work.
2. **Propose** — fill `docs/PROPOSAL-TEMPLATE.md`; self-review against §A–B of the checklist.
   Submit via the program's proposal form. An LLM judge reviews; human reviewers approve.
3. **Build** — only after approval. `harbor tasks init` scaffolds the package.
4. **Review** — local checks (§K of the checklist), then a PR; three rounds of human review.

## Local tooling

| Tool | Status |
|---|---|
| `harbor` | v0.24.0 — installed via `python -m uv tool install harbor` |
| `uv` | v0.13.4 — installed via `pip install uv` |
| Docker Desktop | CLI v27.5.1; engine running (Linux containers) |
| `ANTHROPIC_API_KEY` | needed for `harbor check` and agent trials |

```bash
export PATH="$PATH:$HOME/.local/bin"
harbor --version
```

## Current work

| Date | Proposal | Category / Sub-category | Verdict | Status |
|---|---|---|---|---|
| 2026-10-21 | Reconstruct a heterogeneous mobility field from sparse, noisy phase-separation imaging | Science / Applied Mathematics | Accept | draft (v1) |

## Reference

- Program brief and rubric breakdown: [docs/PROJECT-INSIGHT-BRIEF.md](docs/PROJECT-INSIGHT-BRIEF.md)
- Proposal rubric: `harbor-framework/terminal-bench-science` → `rubrics/task-proposal.md`
- Implementation rubric: `harbor-framework/terminal-bench-science` → `rubrics/task-implementation.toml`
- Contributing guide: `harbor-framework/terminal-bench-science` → `CONTRIBUTING.md`
- Task dashboard: `stevendillmann.github.io/tb-science-task-dashboard/`
- Questions: `stevendi@stanford.edu`
