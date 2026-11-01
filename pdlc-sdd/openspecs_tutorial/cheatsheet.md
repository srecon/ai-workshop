# Openspecs Cheat sheet

##Commands

```
Command	Purpose
openspec list	List changes
openspec list --specs	List specifications
openspec status --change <name>	Inspect artifact completion
openspec validate <name>	Validate artifacts
git status	Check working-tree changes
git diff	Review changes
git diff --check	Check for whitespace errors
npm test	Example test command; use the one appropriate for your project
git log -5 --oneline	Inspect recent commits
```
## Skills for AI Agents.

```
Command or skill	Purpose
/opsx:explore	Explore an idea before committing to a design
/opsx:propose	Create a proposed change
/opsx:update	Update an existing change
/opsx:apply	Implement an approved change
/opsx:sync	Reconcile specification updates
/opsx:archive	Archive a completed change
Superpowers brainstorming	Challenge requirements and refine design
Superpowers writing-plans	Create a detailed implementation plan
Superpowers test-driven-development	Implement through failing and passing tests
Superpowers requesting-code-review	Review implementation quality
```
## The five golden rules to remember
1. Don't start with code. Start with a requirement that has a clear outcome.
2. Don't trust a generated specification automatically. Review it and challenge its assumptions.
3. Don't implement everything at once. Work on one coherent change at a time.
4. Don't accept “it works” without evidence. Run tests, review the code, and verify the acceptance criteria.
5. Don't archive prematurely. Finish verification and reconcile the specifications first.

You don't need to master every SDD concept before starting. Learn the workflow through your first small change, then repeat it.

## Step-by-step: Build your application using OpenSpec + Superpowers
I'll walk you through the process as if this is your first SDD project. We'll use your existing Wealth Management Dashboard repository, your existing OpenSpec changes, and your installed coding assistant.

The examples below use the current OpenSpec workflow (/opsx:...) and the Superpowers skills. OpenSpec commands such as openspec validate run in your terminal; slash commands such as /opsx:apply run in your coding assistant's chat.

### Understand the workflow first

```
1. Prepare
Git · repository · tools · existing changes


2. Grill the requirements
Superpowers brainstorming + OpenSpec review


3. Approve the design
Resolve questions · correct specifications · validate


4. Plan and implement
Superpowers plan · TDD · small coding tasks


5. Verify and finish
Tests · code review · OpenSpec sync/archive · Git commit
```

You repeat steps 2–5 for each capability. You do not need to design and build the entire application in one go.

- Step 1 — Prepare your repository
Open a terminal at the root of your project.
1.1 Check the current state
Run these commands in your terminal:

```
pwd
git status
git branch --show-current
openspec list
openspec list --specs
```

What you are checking:
- pwd — confirms you're in the correct project.
- git status — shows uncommitted changes.
- git branch --show-current — shows your current branch.
- openspec list — shows proposed and active changes.
- openspec list --specs — lists the current specifications.
If git status shows work you haven't committed, don't discard it. Preserve your changes before creating a new branch.

1.2 Check the OpenSpec status
For each existing change you intend to implement:
```
openspec status --change <change-name>
openspec validate <change-name>
```
Replace <change-name> with the actual change ID from openspec list.

For example, if the change is called financial-domain:
```
openspec status --change financial-domain
openspec validate financial-domain
```

Validation checks the artifacts' structure and consistency with the configured schema; it does not prove that the requirements are financially correct.


1.3 Confirm your tools are available

In your coding assistant's chat, ask:

```
Inspect this repository and tell me:
1. Which OpenSpec workflow and schema are configured?
2. Which OpenSpec commands and skills are available?
3. Is Superpowers installed and which skills can be invoked?
4. What test framework and commands does this project use?
5. What existing application code, if any, is present?
Do not install, update, overwrite, or modify anything yet. Report what you discover and the commands I should use in this environment.
```
This avoids a common beginner mistake: following a command example that isn't supported by your particular coding assistant.

Step 2 — Grill your existing OpenSpec changes
This is where you challenge what you plan to build before writing application code.
2.1 Start a review session
In your coding assistant's chat, invoke the installed Superpowers brainstorming skill if you can invoke skills directly. Otherwise, ask the assistant to use it.

Then paste this prompt:
```
I am new to Spec-Driven Development. I have already created the OpenSpec proposal and changes for my Wealth Management Dashboard.

Use the Superpowers brainstorming process to review the existing artifacts.

Important constraints:
- Do not create a new proposal.
- Do not write or modify application code.
- Do not modify existing OpenSpec files yet.
- Inspect the repository and existing changes first.
- Ask me one question at a time and explain technical terms in plain English.
- Challenge my assumptions rather than agreeing automatically.

Review these areas:
1. Financial domain model and calculation accuracy.
2. Currency conversion and valuation dates.
3. Import/export and data integrity.
4. Local persistence, backups, and privacy.
5. AI analysis and data grounding.
6. Requirements, dependencies, and acceptance tests.

For each issue, explain:
- What could go wrong.
- Which existing artifact or requirement is affected.
- Why it matters.
- Your recommended solution and its trade-offs.
- A test that would prove the solution works.

Start with the most important issue. Wait for my answer before moving to the next question. After the review, summarize the decisions and unresolved questions. Do not implement anything until I approve.
```
2.2 Answer questions before continuing
For example, your agent might ask:
```
Should the dashboard calculate net worth using the latest available exchange rate or the rate applicable on the valuation date?
```
A good response isn't just "use the latest rate." Think about the purpose:
- A current snapshot generally uses a current or explicitly selected recent rate.
- A historical snapshot generally needs a rate appropriate to its historical valuation date.
- Missing rates should be disclosed rather than silently replaced.
You can ask the agent to explain alternatives before deciding.

Repeat this question-and-answer process until the important business rules and architecture decisions are clear.

2.3 Record the decisions

Once you have answered the questions, ask:
Summarize the decisions we have agreed on, unresolved questions, and the OpenSpec artifacts affected.
```
Separate confirmed decisions from assumptions. Recommend which changes are essential before implementation and which can be deferred.

Do not edit any files yet. Show me the proposed corrections for approval.
```
Checkpoint: you should now understand what you're building, why, and what is still uncertain.

Step 3 — Update and validate the specifications
Now that you have reviewed the requirements, make the corrections in OpenSpec.
3.1 Ask the assistant to update the existing change
In chat, use the installed OpenSpec update workflow, typically:
```
/opsx:update
```

If the workflow requires a specific change name, supply it. Otherwise, ask the agent to update the existing change you identified. Use this prompt:
```
Update the existing OpenSpec change using only the decisions I approved during our review.

Requirements:
- Preserve the existing change ID.
- Update the relevant proposal, specs, design, and tasks.
- Keep requirements testable and unambiguous.
- Include concrete acceptance scenarios for financial calculations, missing data, invalid imports, and privacy boundaries where applicable.
- Do not add unapproved features.
- Do not write application code.
- Identify any decisions that remain unresolved.
After updating, show me a summary of each artifact changed and why.
```
3.2 Review the files yourself
OpenSpec artifacts are ordinary Markdown files. You can inspect them in your editor or terminal.

A typical structure looks like this:
```
openspec/
├── config.yaml
├── specs/
│   └── ...
└── changes/
    └── financial-domain/
        ├── proposal.md
        ├── design.md
        ├── tasks.md
        └── specs/
            └── .../spec.md

```
Your actual folder names and files may differ.

Read the artifacts in this order:
1. proposal.md — why this change is needed and what it covers.
2. specs/ — the required system behavior.
3. design.md — how the solution is intended to work.
4. tasks.md — the steps needed to implement it.
The important test is: could another developer implement the requirement without having to guess what it means?

3.3 Validate again

Back in the terminal:

```
openspec validate <change-name>
openspec status --change <change-name>
```

If validation fails, fix the reported problems before proceeding.

If validation passes, review the actual requirements and decisions as well. A structurally valid specification can still be incomplete or incorrect.

Step 4 — Prepare a safe development branch

Before implementation, protect your work.

In the terminal:

```git status
git log -5 --oneline

```
If your working tree is clean and you're on the intended base branch, create a feature branch:
```git switch -c feat/financial-domain```


If you already have a suitable feature branch, keep using it. If you have uncommitted work, commit it or otherwise preserve it before switching branches.

For a larger project, Superpowers' ```using-git-worktrees``` skill can create an isolated workspace. For your first change, a normal feature branch is enough.
Understand what you are implementing
Start with the smallest foundational capability. For example:

```define-financial-domain```

The goal is not to build the dashboard UI yet. It is to establish the model and calculation rules on which everything else depends.

If this capability already exists under another name, use the existing change rather than creating a duplicate.

Step 5 — Create an implementation plan with Superpowers

Open a fresh coding-assistant session after the requirements and design have been approved. This helps keep the implementation focused on the approved artifacts.

Invoke the Superpowers ```writing-plans``` skill, or ask your assistant to use it.

Then send:

```
Create an implementation plan for the approved OpenSpec change: define-financial-domain.

Read the existing OpenSpec artifacts and the repository first.

Use the Superpowers writing-plans process.

The plan must:
- Follow the approved specifications and design.
- Break work into small, independently verifiable tasks.
- Identify exact files to create or modify.
- Define the tests for each task.
- Identify dependencies between tasks.
- Avoid adding unrelated functionality.
- Include a verification command for every meaningful task.
- Identify any missing design decision instead of guessing.
Do not implement the plan yet.

Present the plan for review and wait for my approval.
```
Review the plan before allowing execution.

A reasonable task sequence for the financial domain might be:

1. Define core domain types and their invariants.
2. Implement money and currency value handling.
3. Define asset, liability, and valuation models.
4. Implement net-worth calculation rules.
5. Add tests for valid values, rounding, and missing exchange rates.
6. Run the complete test suite and review the implementation against the specifications.

These are examples, not a replacement for your actual approved design.

Step 6 — Implement using Test-Driven Development (TDD)

This is the main coding stage.

Superpowers ```test-driven-development``` process uses three steps:

```
1

RED — write a failing test

Define the expected behavior and verify that the test fails for the intended reason.

2

GREEN — implement the minimum solution

Write just enough code to pass the test. Run it and confirm the result.

3

REFACTOR — improve the code

Simplify the implementation while keeping the tests passing.
```

This cycle is central to the Superpowers development methodology.

Example: testing net worth
Suppose the approved requirement says:

```Net worth equals total assets minus total liabilities.```

A simple example:
```
Record	Amount
Cash	10,000
Investment	5,000
Loan	2,000
Net worth	13,000
```
Before implementing the calculation, the coding assistant should create a test that expresses the expected result.

Illustrative pseudocode:
```
it("calculates net worth as assets minus liabilities", () => {
  const result = calculateNetWorth({
    assets: [10000, 5000],
    liabilities: [2000],
  });

  expect(result).toBe(13000);
});
```

This is only an illustration; the actual code should follow your chosen language, domain model, and test framework.

Then ask Superpowers to implement the task:

```
Implement the next approved task from the plan using Superpowers test-driven-development.

Follow the RED-GREEN-REFACTOR cycle:
1. Write a focused failing test.
2. Run it and confirm that it fails for the expected reason.
3. Implement the minimum code needed to pass.
4. Run the test and relevant regression tests.
5. Refactor if necessary and rerun the tests.

Follow the approved OpenSpec design. Do not skip the test, weaken its assertion to make it pass, or add unrelated functionality.

Show me the commands executed, test results, files changed, and any remaining concerns. Stop if you encounter an unresolved requirement or design decision.
```

Repeat this for each task. Don't ask the agent to implement the entire application in a single step.

Step 6.1 — Track progress
After each meaningful task, check the state in your terminal:
```
git status
git diff --check
git diff
```
Review the actual changes, not just the agent's summary.

Check that completed tasks are marked in tasks.md, and that the code and tests really exist.

If the implementation reveals that a requirement is wrong or incomplete, stop and update the OpenSpec artifacts first. Do not quietly invent a different behavior in the code.

Step 7 — Review the code before declaring success
Passing tests is necessary, but it is not sufficient.

Invoke Superpowers ```requesting-code-review``` skill, or ask the coding assistant to use it.

```
Review the implementation of the current OpenSpec change against the approved requirements, design, and implementation plan.

Do not make changes yet.

Check:
1. Every completed task has corresponding code and tests.
2. The implementation satisfies the relevant acceptance scenarios.
3. Financial calculations handle rounding, currencies, and missing data correctly.
4. Errors are visible and do not corrupt saved financial data.
5. No unrelated files or features were changed.
6. The code is maintainable and does not introduce unnecessary complexity.
7. The test suite covers important success and failure cases.

Classify findings as Critical, High, Medium, or Low. For each finding, provide the affected file, evidence, potential failure, and recommended correction.

Do not claim that something was verified unless you actually ran the relevant check. Wait for my approval before making review-driven changes.
```
If the review finds a defect:

1. Understand the failure.
2. Update the specification if the required behavior is unclear or incorrect.
3. Add or correct a test.
4. Fix the implementation.
5. Run the tests again.
6. Request another review if the correction is significant.

Step 8 — Verify the completed OpenSpec change

Before closing the change, run the project's actual test commands. The agent should have identified these in Step 1.

Typical examples, depending on the project:

```
npm test
npm run lint
npm run build
```
Do not run these blindly if the project uses a different stack. Use the real commands from your package scripts, project documentation, or build configuration.

Then validate the OpenSpec artifacts:

```
openspec validate <change-name>
openspec status --change <change-name>
git diff --check
git status
```
Ask the coding assistant:

```
Verify the current OpenSpec change before it is considered complete.

Compare the implementation, tests, and completed tasks against every applicable requirement and acceptance scenario.

Run the available test, lint, and build commands. Report actual results, including failures.

Check for:
- Requirements with no implementation
- Implementations with no corresponding requirement
- Tasks marked complete without evidence
- Missing or inadequate acceptance tests
- Unresolved design decisions
- Changes to shared specifications that have not been reconciled

Do not archive the change yet. Produce a final verification report and list anything that blocks completion.
```
Completion gate: don't move forward while there are critical failures or unverified requirements that are essential to the change.

Step 9 — Synchronize and archive the change

Once the implementation and verification are complete, reconcile the change's specifications with the main specifications.

Depending on your OpenSpec workflow, this may be done through ```/opsx:sync``` followed by ```/opsx:archive```, or through the archive workflow itself. Check the instructions available in your installed profile. OpenSpec documents synchronization and archiving as part of the lifecycle of a completed change. 
OpenSpec+2

In your coding assistant's chat, you can ask:

```
The implementation and verification for this change are complete.

Inspect the current OpenSpec workflow and explain how to reconcile the change's specification updates with the main specifications.

Check for conflicts and confirm that the implementation satisfies the approved change before proceeding.

Then synchronize and archive the change using the supported workflow, but only if all completion criteria are met.

Report:
- Which specifications were updated
- Where the completed change was archived
- Any unresolved or deferred requirements
- The final validation result

Do not delete unrelated files or discard uncommitted user work.
```
If your installed workflow uses explicit slash commands, the sequence may be:

```
/opsx:sync
/opsx:archive
```
If your profile does not provide these commands, follow the instructions returned by the installed OpenSpec workflow rather than assuming the commands are available.

Step 10 — Commit the finished work

After synchronization and archiving, review the repository:

```
git status
git diff --check
git diff
```
If there are no unrelated changes and all required checks passed, commit the completed slice:

```
git add .
git commit -m "feat: implement financial domain"
```
Important: git add . stages all changes in the current directory. If your repository contains unrelated work, stage only the intended files instead.

Check the result:
```
git status
git log -1 --oneline
```

You now have a versioned, reviewed implementation and its corresponding specifications.

Step 11 — Start the next capability

Now repeat the workflow with the next capability. Your order might look like this:
```
1

Financial domain

Define assets, liabilities, money, valuations, and calculation rules.

2

Local persistence

Save and restore financial records reliably.

3

Import/export

Load data from CSV/Excel and validate it.

4

Net worth and cash flow

Implement and test deterministic financial calculations.

5

Dashboard UI

Display net worth, allocation, liabilities, and income.

6
Risk visualization

Add the configurable Wealth Pyramid and concentration indicators.

7
Financial goals

Implement goals and transparent projections.

8
AI analysis

Add privacy-controlled, evidence-grounded financial summaries.
```

This is a suggested order, not a requirement to create exactly eight changes. If your existing OpenSpec proposal already divides the work differently, use its structure and resolve dependencies before starting.

For each capability, repeat Steps 2–10 as appropriate. A small, unambiguous change may not need an extensive brainstorming session, but it should still have clear requirements, tests, and verification.

