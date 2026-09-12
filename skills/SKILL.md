---
name: corporate-architecture-diagram
description: Create evidence-grounded corporate architecture diagrams and architecture descriptions from business requirements, system requirements, standards, regulations, ADRs, existing architecture documents, and OKF knowledge. Use when the user asks to design, visualize, explain, review, or document a corporate software architecture.
priority: 20
---

# Corporate Architecture Diagram

## Purpose

Create high-quality, evidence-grounded corporate architecture diagrams.

The goal is NOT merely to draw a visually attractive diagram.

The goal is to help a corporate architect:

- understand the problem;
- identify architectural drivers;
- identify required capabilities and components;
- establish system boundaries;
- identify external dependencies;
- represent important interfaces and data flows;
- expose architecture constraints;
- distinguish approved architecture from proposed architecture;
- explain the architecture to technical and non-technical stakeholders;
- preserve traceability from architecture decisions to source evidence.

Use Archify as the rendering and validation engine when available.

---

# Core principles

## 1. Evidence before visualization

Never start by drawing.

First determine:

1. What is explicitly stated?
2. What is required?
3. What architecture is already approved?
4. What standards constrain the solution?
5. What is derived from the evidence?
6. What remains unknown?

Do not invent components, technologies, integrations, data flows,
ownership, deployment topology, or protocols unless supported by evidence
or explicitly marked as a proposal.

---

## 2. Separate FACT, DERIVED, PROPOSAL and UNKNOWN

Every important architectural element must belong to one of these categories.

### FACT

Explicitly supported by source material.

### DERIVED

A logical consequence of documented requirements or architecture.

### PROPOSAL

An architecture option suggested by the AI.

### UNKNOWN

Information required to make a reliable architectural conclusion but
not available in the source material.

Never silently convert UNKNOWN into FACT.

---

# 3. Source authority

When sources conflict, use the following precedence unless the user
explicitly specifies another rule:

1. Approved Architecture Decision / ADR
2. Approved target architecture
3. Corporate architecture standards
4. Security and regulatory requirements
5. Explicit system requirements
6. Functional requirements
7. Business requirements
8. Existing implementation documentation
9. General architecture best practices
10. AI inference

If two authoritative sources conflict:

- do not silently resolve the conflict;
- report the conflict;
- identify both sources;
- explain the architectural consequence;
- ask for a decision when necessary.

---

# 4. Do not confuse requirements with architecture

Business requirements describe WHAT the business needs.

Functional requirements describe WHAT the system must do.

Non-functional requirements describe HOW WELL it must work.

Standards and regulations describe CONSTRAINTS.

ADRs describe WHY an architectural decision was made.

Architecture describes HOW the system is structured.

Do not directly convert every requirement into a component.

First identify the architectural driver.

Example:

Requirement:
"System must support 10,000 requests per second."

Do NOT immediately create:

"Load Balancer + 5 Microservices + Kafka."

Instead derive:

Architectural driver:
"High throughput."

Then identify possible architectural consequences:

- horizontal scalability;
- stateless processing;
- capacity management;
- load distribution.

Only introduce concrete technologies when supported by evidence
or explicitly proposed.

---

# 5. Understand the requested purpose before selecting a diagram

Select the diagram type based on the question the diagram must answer.

## Architecture diagram

Use when the question is:

"What exists and how are the major building blocks connected?"

Show:

- systems;
- services;
- applications;
- data stores;
- external systems;
- important boundaries;
- major interfaces;
- primary relationships.

## Workflow

Use when the question is:

"How does a business or technical process move through the system?"

Show:

- actors;
- activities;
- decisions;
- approvals;
- alternative paths.

## Sequence

Use when the question is:

"Who calls whom and in what order?"

Show:

- participants;
- requests;
- responses;
- asynchronous interactions;
- important timing relationships.

## Data Flow

Use when the question is:

"Where does data come from, where does it go, and across which boundaries?"

Show:

- data sources;
- transformations;
- stores;
- consumers;
- trust boundaries;
- sensitive data flows.

## Lifecycle

Use when the question is:

"How does an entity or process change state?"

Show:

- states;
- transitions;
- events;
- retries;
- terminal states.

Do not force every problem into an architecture diagram.

---

# 6. Determine the appropriate architecture level

Prefer the minimum level of detail required to answer the user's question.

Possible levels:

### Level 0 — Context

System and external actors/systems.

### Level 1 — Container / Solution

Major applications, services, databases and integrations.

### Level 2 — Component

Internal logical components and responsibilities.

### Level 3 — Deployment

Nodes, environments, clusters, zones, networks and deployment boundaries.

Do not mix levels without a clear reason.

If the user asks for a corporate architecture overview,
prefer Level 0 or Level 1.

If implementation detail is required, progressively drill down.

---

# 7. Architecture diagram composition

Prefer:

- 8–15 major elements for an executive or corporate architecture view;
- one dominant reading direction;
- clear system boundaries;
- explicit external systems;
- meaningful grouping;
- limited crossing edges;
- short labels;
- meaningful relationship labels.

Avoid:

- huge diagrams;
- dozens of equal-weight components;
- crossing arrows;
- decorative elements;
- unnecessary technology logos;
- duplicate nodes;
- unexplained abbreviations;
- every requirement represented as a box.

If supporting detail is needed, place it in a second diagram or description.

---

# 8. Architecture boundaries

Look for and represent meaningful boundaries such as:

- organization boundaries;
- system boundaries;
- trust boundaries;
- security zones;
- network zones;
- responsibility boundaries;
- data ownership boundaries;
- environment boundaries.

Do not create boundaries merely for visual decoration.

Every important boundary should communicate an architectural fact.

---

# 9. Relationships

Every important relationship should answer:

"Why are these two elements connected?"

Prefer explicit relationship labels such as:

- REST API
- event
- message
- file exchange
- database access
- authentication
- data replication

Do not invent protocols.

If the protocol is unknown, use:

"Integration"

or:

"Interface — protocol unspecified"

Never assume REST, Kafka, gRPC, HTTP, etc. without evidence.

---

# 10. Data flows

When data movement is architecturally important, identify:

- source;
- destination;
- data type;
- direction;
- transformation;
- persistence;
- sensitivity;
- ownership.

If sensitive or regulated data is involved, explicitly consider:

- trust boundary;
- encryption;
- access control;
- retention;
- audit;
- regulatory constraints.

Do not claim compliance merely because a security component appears.

---

# 11. Architecture drivers

Before generating the final diagram, identify the main architectural drivers.

Typical drivers:

- scalability;
- availability;
- resilience;
- performance;
- security;
- regulatory compliance;
- data sovereignty;
- interoperability;
- maintainability;
- observability;
- cost;
- time-to-market.

Only include drivers supported by source material or clearly mark them
as assumptions.

---

# 12. Architecture constraints

Identify constraints separately from drivers.

Examples:

- mandatory technology;
- prohibited technology;
- corporate platform;
- regulatory requirement;
- deployment restriction;
- data residency;
- existing system dependency;
- organizational ownership.

Constraints should influence the architecture.

Do not merely list them below the diagram.

---

# 13. ADR awareness

When an ADR is available:

1. identify the decision;
2. identify the context;
3. identify the chosen option;
4. identify rejected alternatives;
5. identify consequences.

Do not redraw an ADR as if it were only a technical topology.

The diagram should reflect the chosen decision.

If the proposed architecture contradicts an ADR,
explicitly flag the contradiction.

---

# 14. Architecture quality review before rendering

Before generating the final diagram, perform a lightweight architecture review.

Check:

### Completeness

Are the important requirements represented?

### Consistency

Does the architecture contradict itself?

### Traceability

Can important elements be traced to source evidence?

### Boundary clarity

Are system and responsibility boundaries clear?

### Dependency clarity

Are major external dependencies visible?

### Requirement coverage

Are important architectural drivers reflected?

### Missing information

Are important decisions blocked by unknown information?

### ADR consistency

Does the architecture respect existing decisions?

### Standard compliance

Does the architecture appear consistent with applicable standards?

Do not claim compliance when evidence is insufficient.

---

# 15. Architecture description

Every final diagram should be accompanied by a concise architecture description.

Use this structure:

## 1. Purpose

What problem does the architecture solve?

## 2. Scope

What is included and excluded?

## 3. Main building blocks

Explain the responsibility of each major component.

## 4. Main interactions

Explain the primary flows.

## 5. Architectural drivers

List the requirements that shaped the architecture.

## 6. Constraints

List important standards, regulations and existing decisions.

## 7. Key decisions

Explain important architectural choices.

## 8. Risks and open questions

Identify unresolved architectural questions.

## 9. Source evidence

For each important architectural fact, provide the relevant source.

---

# 16. Traceability

Maintain traceability between:

Requirement
    ↓
Architectural driver
    ↓
Architecture decision
    ↓
Architecture element
    ↓
Relationship

When source information is available, include:

- source title;
- source path;
- relevant section;
- slide/page when available.

Never fabricate source references.

---

# 17. OKF knowledge usage

When the user's workspace contains an OKF knowledge base:

1. Use the knowledge index/catalog to locate relevant documents.
2. Search for the exact architectural topic.
3. Retrieve authoritative sources.
4. Prefer primary/approved sources.
5. Compare relevant sources when multiple documents exist.
6. Extract evidence before proposing architecture.
7. Preserve source terminology.

Do not treat the entire knowledge base as equally authoritative.

When GBrain is available, use it for semantic retrieval of relevant knowledge.

Do not use retrieved text as architectural fact until its source and context
have been checked.

---

# 18. GBrain retrieval discipline

Use GBrain to answer targeted retrieval questions.

Prefer queries such as:

- "Find approved architecture decisions concerning <topic>"
- "Find corporate standard requirements for <topic>"
- "Find previous architecture decisions related to <system>"
- "Find requirements concerning availability of <system>"

Avoid broad queries such as:

"Find everything about architecture."

Retrieve focused evidence.

If retrieval returns ambiguous or weak evidence:

- report uncertainty;
- search again using more specific terminology;
- do not compensate by inventing architecture.

---

# 19. Local LLM discipline

The model may have incomplete knowledge of the organization.

Therefore:

Corporate knowledge from the user's sources has priority over
general model knowledge.

General architecture knowledge may be used to:

- explain concepts;
- identify possible alternatives;
- identify missing information;
- propose options.

It must not be presented as an existing corporate fact.

---

# 20. Corporate architecture notation

Prefer a restrained enterprise architecture visual language.

Use visual hierarchy:

1. system boundary;
2. major domains;
3. applications/services;
4. data stores;
5. external systems;
6. integrations;
7. annotations.

Avoid excessive colors.

Use color primarily to communicate semantic meaning:

- external;
- internal;
- data;
- security/trust;
- proposed;
- risk.

Do not use color merely for decoration.

---

# 21. Proposed architecture

If the user asks to DESIGN a new architecture rather than DOCUMENT an existing one:

Clearly separate:

### Evidence

What is known.

### Constraints

What cannot be changed.

### Design decisions

What must be decided.

### Proposed architecture

What the AI recommends.

### Alternatives

Other viable options.

### Trade-offs

Benefits and costs.

### Open questions

What requires human decision.

Never present a proposed architecture as an existing corporate architecture.

---

# 22. Archify integration

When Archify is available:

1. Build the architecture model first.
2. Choose the appropriate diagram type.
3. Generate the Archify representation.
4. Validate the generated artifact.
5. Inspect layout and relationships.
6. Correct only identified issues.
7. Deliver the validated artifact.
8. Produce the architecture description separately.

Use Archify's validation facilities.

Do not repeatedly regenerate the entire diagram when only a local correction
is required.

Preserve stable elements during refinement.

---

# 23. Final quality gate

Before presenting the result, verify:

[ ] Every major component has a reason to exist.

[ ] Every major relationship is supported or explicitly proposed.

[ ] No unsupported technology has been introduced as fact.

[ ] Requirements are represented where architecturally relevant.

[ ] Important standards and constraints are reflected.

[ ] ADR decisions are respected.

[ ] Unknown information is clearly identified.

[ ] Proposed elements are distinguishable from existing architecture.

[ ] The diagram answers one clear architectural question.

[ ] The diagram is readable without the source documents.

[ ] The description explains the architecture in plain language.

[ ] Source evidence is available for important claims.

---

# 24. Final response format

Return the result in this order:

## Architecture objective

One paragraph.

## Architecture drivers

Short table:

| Driver | Source | Architectural implication |

## Architecture

Use Archify to create the appropriate diagram.

## Architecture description

Explain the major building blocks and interactions.

## Key decisions

| Decision | Rationale | Evidence |

## Constraints

| Constraint | Source | Impact |

## Risks and open questions

| Question | Why it matters | Required decision |

## Evidence

List the most important source documents and sections.

## Assumptions

List every material assumption that was required.

## Validation status

State:

- validated facts;
- derived elements;
- proposed elements;
- unresolved items.