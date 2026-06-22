# AGENTS
This repository defines an artifact-based AI workflow.

## Main rule

- Treat files in `work/` as the durable source of truth.
- Treat `.pi/` as the pi workflow implementation.
- Treat `.opencode/` as the OpenCode workflow implementation.
- Start new delivery work with `brainstorm`.
- Prefer repo artifacts over chat memory.

## Important locations

- `.pi/prompts/` - pi prompt templates for agent roles and command entry points
- `.pi/skills/` - pi reusable skills
- `.pi/custom/init/` - pi bootstrap assets and README source
- `.opencode/agent/` - OpenCode agent definitions
- `.opencode/commands/` - OpenCode command entry points
- `.opencode/skills/` - OpenCode reusable skills
- `.opencode/custom/init/` - OpenCode bootstrap assets and README source
- `work/project-config.md` - repo operating context
- `work/backlog/` - story state
- `work/ideas/` - idea capture

## Agent behavior

- Read `work/project-config.md` first.
- Load only guidance relevant to the current task.
- Do not invent repo policy when the repository does not define it.
- Keep workflow decisions and delivery state in repo artifacts.