# Project Insight proposals

One directory per proposal. Each holds the proposal text and its rubric review side by side, so the
rejection patterns compound across submissions instead of resetting each time.

```
docs/proposals/
├── README.md                         ← this file
└── 2026-10-21-cahn-hilliard-mobility/
    ├── PROPOSAL.md                   ← the text submitted to the form (current revision)
    ├── PROPOSAL-v0.md                ← superseded draft, kept for history
    ├── REVIEW.md                     ← rubric evaluation + ranked fixes
    └── NOTES.md                      ← internal: pilot study plan, open design questions
```

## Conventions

**Directory name:** `YYYY-MM-DD-<short-slug>` — date the draft was started, kebab-case slug.
**File names:** `PROPOSAL.md` and `REVIEW.md` (uppercase) inside each directory.

**Front matter** on `PROPOSAL.md`:

```yaml
---
status: draft | submitted | approved | built | merged | withdrawn
review: ./REVIEW.md
review_verdict: Accept            # the rubric's Decision line
date: 2026-10-21
category: Science                  # as submitted
sub_category: Applied Mathematics
---
```

**Status meanings**

| Status | Meaning |
|---|---|
| `draft` | Being written. No form submitted. |
| `submitted` | On the proposal form; awaiting or in LLM-judge/human review. |
| `approved` | Human reviewers approved. **Green light to build the Harbor package.** |
| `built` | Harbor package exists locally; oracle passes, nop fails. |
| `merged` | PR merged into the upstream benchmark. |
| `withdrawn` | Abandoned. Record *why* in the review — that is the reusable lesson. |

## Writing flow

1. Copy `docs/PROPOSAL-TEMPLATE.md` into a new dated directory as `PROPOSAL.md`.
2. Fill **every** scaffolded paragraph. The template's bolded prompts are there because each one
   corresponds to a rubric criterion that has historically been the weak point.
3. Self-review against `docs/PRE-SUBMISSION-CHECKLIST.md` (sections A and B).
4. Get a second pair of eyes — ideally a domain expert who cannot see your notes. Hand them the
   proposal text alone; if they cannot solve it, the instruction/description is not well-specified.
5. Write `REVIEW.md` using the rubric template in `docs/PROPOSAL-TEMPLATE.md` §7.
6. Apply the ranked fixes, re-review, update `review_verdict`, then submit.

## Review files

`REVIEW.md` holds the rubric evaluation — re-stated problem, then each of the seven criteria with
pros, cons, and a judgement, then a final analysis and a `Decision:` line. It also holds the
**ranked fixes**: a numbered list of concrete, actionable changes, each saying *what to change and
why it matters*. A review that only judges is half a review; the fixes are the deliverable.

## Index

| Date | Proposal | Category / Sub-category | Verdict | Status |
|---|---|---|---|---|
| 2026-10-21 | Reconstruct a heterogeneous mobility field from sparse, noisy phase-separation imaging | Science / Applied Mathematics | Accept | draft (v1) |
