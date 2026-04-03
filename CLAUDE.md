# [Project Name]

Brief description of what this project does.

## Casey's Preferences

### Design Philosophy
- **Unified over separate**: One schema for all cases, not multiple specialized schemas
- **Build only as complicated as necessary** without backing into corners
- **One-way doors** (hard to undo) get careful review; **two-way doors** proceed quickly
- **Evidence-based complexity**: Add defensive patterns when measured, not assumed

### Technical Preferences
- **Plain JavaScript frontend** — no React, Next.js, or frameworks. Vanilla JS + HTML + CSS.
- **No dependency injection**: Hard to debug and maintain
- **Test happy AND negative paths**: Tests prevent production bugs, not hit coverage metrics
- **Build only what's needed**: Add libraries/frameworks when the complexity justifies them

### Communication Style
- Concise summaries with tables
- Explicit "in scope / out of scope" boundaries
- Validate assumptions before implementation

## Autonomous Workflow

Operate fully autonomously. Casey only reviews "one-way doors."

1. Skip EnterPlanMode approval — create plans directly
2. Auto-proceed after multi-agent reviews
3. Commit incrementally during implementation
4. **Run `/workflows:review` before every PR** — mandatory, no exceptions
5. Create PR when done — auto-merge after review passes

**Auto-merges** (two-way doors): new features, refactoring, bug fixes, tests, docs, scripts
**Needs human review** (one-way doors): breaking schema changes, major dependencies, architectural constraints, irreversible data migrations

Mark one-way doors with `needs-human-review` label.

## Standard Workflow

This is the standard workflow for all features, even simple ones. LLM review tasks execute quickly so there's no reason to skip them.

1. **Brainstorm** (`/workflows:brainstorm`) — explore WHAT to build through dialogue
2. **Plan** (`/workflows:plan`) — define HOW to build it
3. **Plan Review Loop** (`/plan_review`) — multi-agent review, update plan, re-review until aligned
4. **Work** (`/workflows:work`) — implement the plan using agent subprocesses
5. **Code Review** (`/workflows:review`) — multi-agent review of implementation
6. **PR** — create and merge (auto-merge for two-way doors)
7. **Compound** (`/workflows:compound`) — capture learnings for future sessions

Always use agent subprocesses for implementation work to preserve main conversation context.

## Research Before Shipping

**Never ship data without verifying against primary sources.** Use parallel research agents — the cost (minutes) is negligible compared to showing wrong data. See PRODUCT.md for rationale.

## Project Organization

### Rule 1: Lifecycle — close what you open
When a PR is merged:
- Move the plan to `docs/plans/archive/`
- Update `BACKLOG.md` — move item from Active to Done
- Delete local + remote feature branch, `git fetch --prune`

### Rule 2: Location — everything has a home
| File type | Location |
|-----------|----------|
| Project docs | `CLAUDE.md`, `PRODUCT.md`, `README.md`, `BACKLOG.md` (root only) |
| Plans (active) | `docs/plans/` |
| Plans (done) | `docs/plans/archive/` |
| Brainstorms | `docs/brainstorms/` |
| Institutional learnings | `docs/solutions/` |
| Reference data | `reference/` |
| Generated/scratch | `output/` — gitignored |

### Rule 3: Session start — read the board
Read `BACKLOG.md`, `MEMORY.md`, `CLAUDE.md`, and `PRODUCT.md` at session start.

### Rule 4: Session end — leave it clean
Update `BACKLOG.md` with current status, flag untracked files.

## Philosophy

Each unit of engineering work should make subsequent work easier — not harder.

1. **Plan** → Understand the change and its impact (use research agents first)
2. **Delegate** → Use AI tools to help with implementation
3. **Assess** → Verify changes work as expected
4. **Codify** → Run /workflows:compound to capture learnings

### Auto-Compound Rules
Run /workflows:compound automatically before:
- Running /compact
- Switching to a different feature or task
- Completing a major milestone
- When context window feels crowded

## Git Workflow

**CRITICAL: Never squash commits.** Preserve commit history.
- **Merge commit** (default) or **Rebase and merge**
- Before moving to new work, check for orphaned commits on feature branches
- After merge: delete local + remote branches, `git fetch --prune`

## Active Gotchas

(Add gotchas as you discover them)

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
