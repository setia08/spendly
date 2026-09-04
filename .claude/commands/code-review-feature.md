---
description: Runs quality and security review for a specific Spendly feature. Pass the spec name as argument e.g. /code-review-feature 05-backend-connection
allowed-tools: Bash(git diff)
---

Run the code review pipeline for the feature specified 
in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /code-review-feature 
<spec-name> e.g. /code-review-feature 05-backend-connection"

If `.claude/specs/$ARGUMENTS.md` does not exist, stop 
immediately and say:
"Spec file not found at .claude/specs/$ARGUMENTS.md. 
Please check the spec name and try again."

---

## Step 1: Run Both Reviews in Parallel

Invoke the **spendly-quality-reviewer** and 
**spendly-security-reviewer** subagents simultaneously 
(same message, parallel Agent calls) with the following 
context for each:

- Spec file for context: 
  `.claude/specs/$ARGUMENTS.md`
- Diff to review: output of `git diff` against the base 
  branch (or the working tree diff if uncommitted), 
  scoped to the changes made for this feature
- Instruction: Review only the recently changed or newly 
  added code for this feature. Skip stub routes — they 
  are expected placeholders. Stay in your own lane 
  (quality vs. security) and do not duplicate the other 
  reviewer's findings.

Wait for both subagents to fully complete before 
producing the combined report.

---

## Handoff Rules

- Do NOT start writing the combined report until both 
  reviewers have finished
- Do NOT attempt to fix any code based on the findings — 
  this command only reports
- Do NOT run tests — that's `/test-feature`'s job

---

## Final Output

After both subagents complete, produce a combined 
summary:

### Code Review Report — $ARGUMENTS

**Quality Review**
- Mirror the spendly-quality-reviewer's structured report

**Security Review**
- Mirror the spendly-security-reviewer's structured report

**Verdict**
One of:
- ✅ Looks solid — no blocking issues found
- 💡 A few things worth addressing — see findings above
