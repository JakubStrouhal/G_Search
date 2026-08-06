# Skills

One folder per skill, each containing a `SKILL.md`:
`.claude/skills/<skill-name>/SKILL.md`.

```markdown
---
name: skill-name
description: What it does AND when to use it — this is the only text Claude
  sees when deciding whether to load the skill, so make the triggers explicit.
---

The instructions, loaded into context only when the skill fires.
```

Supporting files (scripts, templates, reference docs) live alongside `SKILL.md`
in the same folder and are read on demand, so a skill can be much larger than
what it costs to keep listed.

Skills are model-invoked (Claude decides) as well as user-invocable via
`/<skill-name>`; commands are always user-invoked. Use a skill when the
knowledge should apply automatically, a command when the user drives it.

Candidates for this repo: the VERIFIED / INFERRED / CANNOT VERIFY tagging
discipline that `FINDINGS.md` uses; the F1–F6 failure taxonomy from
`docs/analysis/PLAN.md` §5 that the Part B prototype must cover.
