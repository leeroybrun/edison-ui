# Data Model — Edison UI Speckit Audit & Consolidation

## Entities

### Project
- **Identity**: projectId (hash of absolute path)
- **Attributes**: path (absolute), name, pinned (bool), health counts (tasks, sessions, QA), lastActivity, hasGit, gitBranch?, isHealthy, errors[]
- **Relationships**: has many Sessions, Tasks, QARounds, Agents, Validators
- **Constraints**: path must resolve and be within configured scan roots; unique projectId per path.

### Session
- **Identity**: sessionId
- **Attributes**: state (draft/active/blocked/done/closing/validated/recovery/archived), owner, createdAt, updatedAt, closedAt?, history[], gitInfo?, taskIds[]
- **Relationships**: belongs to Project; references Tasks
- **State transitions**: Edison guards control allowed moves; blocked transitions must include guard reason.

### Task
- **Identity**: taskId
- **Attributes**: title, description, state (todo/wip/blocked/done/validated), tags[], createdAt, updatedAt, claimedAt?, completedAt?, validatedAt?, timeEstimate?, timeSpent?
- **Relationships**: belongs to Project; may link to Session and QARounds
- **Constraints**: titles sanitized; transitions follow Edison rules; tags are user-defined strings.

### QARound
- **Identity**: qaRoundId (per task, round-based)
- **Attributes**: status/verdict, evidence links, validator names, timestamps, notes
- **Relationships**: belongs to Task (and Project)
- **Constraints**: evidence paths must resolve within project; missing evidence surfaces warnings.

### Agent / Validator
- **Identity**: name/id from Edison-generated metadata
- **Attributes**: description, capabilities, type (agent/validator), availability
- **Relationships**: belongs to Project context
- **Constraints**: read-only visibility in current scope.

### Audit Entry
- **Identity**: timestamp + actionId
- **Attributes**: actor (local OS user + display name), action, target entity, outcome, context, timestamp
- **Relationships**: linked to Project and affected entity
- **Constraints**: recorded for every state-changing action; must not expose secrets or paths outside project roots.
