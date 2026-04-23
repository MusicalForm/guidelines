# LCMA Modelling Architecture v0.2 — DRAFT

> **Status:** Working draft.  Sections marked *[CONCEPTUAL DRAFT]* are subject
> to substantial change depending on decisions identified in the text.

---

## Table of Contents

1. [Current State Inventory](#1-current-state-inventory)
2. [Terminology](#2-terminology)
3. [Goals — Dependency Graph](#3-goals--dependency-graph)
4. [The Project Root Question](#4-the-project-root-question)
5. [Tooling — Module-by-Module Exploration](#5-tooling--module-by-module-exploration)
6. [Derivation Hierarchy and Change Propagation](#6-derivation-hierarchy-and-change-propagation)
7. [Collaborative Workflow](#7-collaborative-workflow)
8. [Documentation Architecture](#8-documentation-architecture)
9. [Phased Migration Path](#9-phased-migration-path)
10. [Open Questions](#10-open-questions)
11. [Appendices](#11-appendices)

---

## 1. Current State Inventory

### 1.1 The Guidelines Repository

The guidelines repo (`MusicalForm/guidelines`) is a Quarto website
(`_quarto.yml`, output to `docs/`) following the Diataxis documentation
philosophy.  It renders to https://musicalform.github.io/guidelines/.
The navbar exposes four Diataxis categories:

| Category    | Content                                                   |
|-------------|-----------------------------------------------------------|
| Tutorial    | `wiki/tutorials/quickstart.md`, `wiki/Intro.md`, `wiki/Principles.md` |
| How-To      | `wiki/Workflow.md`                                        |
| Explanations| `wiki/Examples.md`                                        |
| Reference   | `wiki/Syntax.md`, `Vocabulary.ipynb`                      |

Content is curated via the GitHub wiki (`wiki/` submodule, URL:
`MusicalForm/guidelines.wiki.git`).  Updating the rendered site requires
updating the submodule ref and rebuilding — this step is not integrated into
any automated workflow.

**Vocabulary.ipynb** generates a reference table from the CSV export of a
collaborative Nextcloud spreadsheet (`data/Form vocabulary.csv`).  The table
links to external Open Music Theory pages and to two vignettes in
`wiki/vignettes/`:

- `vignette-thematic-intro.md` — Curtain & Thematic Introduction
- `vignette‐sequence.md` — (title from filename; note the Unicode hyphen)

Of approximately 60+ needed vignettes, only these 2 exist.

### 1.2 The Vocab Spreadsheet and CSV

The spreadsheet (`data/Form vocabulary.csv`) contains 103 rows spanning:

- **Active terms** (rows 1–61): labels used in annotation, with columns for
  formal label, short label, function/type, hierarchical level, containment
  relations, short explanation, Open Music Theory link, theoretical provenance.
- **Cadence-related terms** (rows 62–68): PAC, IAC, HC, EC, DC, PC — typed as
  "Type" but not integrated into the EBNF grammar or Python enums.
- **Deprecated/proposed terms** (rows 72–103): terms like `anhang`, `answer`,
  `bridge`, `chorus`, `verse`, `track` — many without hierarchical level,
  function/type designation, or abbreviation.  These represent potential future
  vocabulary or domain-specific extensions (pop/rock, Baroque concerto, Koch
  terminology).

**Known issues:**

- The CSV contains terms not in the EBNF grammar (cadences, deprecated rows).
- The EBNF grammar contains terms not in the CSV (`after-the-end`/`ate` is in
  both, but `codetta`/`cdta` appears in the CSV as section-level while the EBNF
  does not distinguish hierarchical levels).
- The Python enums contain terms not in the CSV (e.g., `cadential_subphrase`
  vs. CSV's `cadential idea`/`cad`).
- The CSV contains terms not in the Python enums (cadence types, deprecated
  terms).
- No single component is authoritative.

### 1.3 The EBNF Grammar

`grammar/lcma_standard.ebnf` defines the LCMA Form Annotation Standard v0.1.
It specifies:

- **Label structure:** optional `Name:` prefix, one or more `FormLabel`s
  (separated by `-`), or a `PlaceholderLabel`.
- **FormLabel:** `FunctionLabel` optionally followed by `|TypeExp` and `?`.
- **FunctionLabel:** one or two `FunctionExpr`s connected by `/` (crossing) or
  `>` (transformation).
- **FunctionExpr:** a `Function` optionally followed by `Shorthand`
  (material operators).
- **Function:** `GenericFunction` (cardinality + unit) or `SpecificFunction`
  (enumerated terms).
- **SpecificFunction:** 32 specific function names with abbreviation aliases.
- **FormalType:** 18 type names with aliases, including compound forms
  (`simple_binary.balanced`, `ternary.da_capo`, etc.).
- **MaterialBrackets:** reference system for material relationships.

The grammar is processed by DHParser (v1.9.4, actively maintained) to
auto-generate `grammar/lcma_standardParser.py`.  A copy of this parser lives
in `musicalform/src/musicalform/cli/lcma_standardParser.py`.

### 1.4 The `musicalform` Python Library

`musicalform/` (submodule, `MusicalForm/musicalform`, v0.1.0) contains:

**`enums.py`** — `FancyStrEnum`-based vocabulary:

| Enum Class            | Members (canonical) | Purpose                          |
|-----------------------|---------------------|----------------------------------|
| `SpecificFunctionName`| 32                  | Named formal functions           |
| `UnitName`            | 15                  | Generic hierarchical units       |
| `FunctionSpecificity` | 2                   | specific / generic               |
| `MainType`            | 18                  | Primary formal types             |
| `SubType`             | 3                   | Qualifiers for binary/ternary    |
| `MaterialOperator`    | 15                  | Material relationship operators  |
| `PlaceholderName`     | 1                   | `%` placeholder                  |
| `CertaintyName`       | 2                   | default / uncertain              |
| `ReferenceSentinel`   | 1                   | implicit previous reference      |

`FancyStrEnum` supports instantiation from abbreviation aliases and provides
`get_abbreviations()`.

**`core.py`** — Domain model as dataclasses:

- `FormalFunction` (ABC) → `SingleFunction` → `SpecificFunction`,
  `GenericFunction`; `FunctionalTransformation`
- `FormalType` (main_type, sub_type, notional)
- `SingleReference`, `MaterialReferences`, `TransformationalReferences`
- `PlaceholderLabel`, `FormLabel`, `AnnotationLabel`

Each dataclass has a `from_parse(dict)` class method that translates DHParser's
JSON-dict output into domain objects.  This coupling means the domain model
currently serves double duty: it is both the canonical representation of
concepts AND a parser output consumer.

**`cli/`** — Command-line interface:

- `musicalform validate -e EXPR` — validate a single label expression
- `musicalform validate -c FILE.csv` — batch-validate a CSV
- `musicalform validate -j FILE.json` — extract and validate TiLiA `.tla` files
- `musicalform validate -d DIR` — recursively validate a directory of `.tla`
  files

**`utils.py`** — `compact_repr` decorator, parse-tree helpers.

**Build & CI:**

- Build system: `uv_build` (pyproject.toml)
- Dependencies: `DHParser>=1.8.3`, `pandas>=2.0`
- Dev tools: pytest, tox, pre-commit, autoflake, black, isort, flake8, mypy
- CI: GitHub Actions on push/PR to `development` branch; matrix: Python 3.11,
  3.12
- Release: `release-please` (v3; current is v4) targeting `development` branch

### 1.5 The OWL Ontology (Deprecated)

`ontology/protege/form_ontology.owl` is a draft from September 2024, created
in WebProtégé.  It is **deprecated** and retained only for informational
content.

The ontology captures the **meta-level architecture** — what Formal Function,
Feature, and Formal Type *are* — but not the vocabulary itself (no individual
functions or types are instantiated).

**Classes defined** (12):

| OWL Class                  | Subclass Of         | Key Relations                         |
|----------------------------|---------------------|---------------------------------------|
| Formal Function            | (root)              | is characterised by → Form-functional Aspect; is realised as → Formal Type; qualifies → Timespan |
| Form-functional Aspect     | (root)              | characterises → Formal Function       |
| Formal Type                | (root)              | realises → Formal Function            |
| Feature                    | (root)              | operationalises → Musical Domain      |
| Intrinsic Function         | Formal Function     | is informed by → Context-Independent Feature |
| Contextual Function        | Formal Function     | is informed by → Context-Dependent Feature |
| Positional Function        | Contextual Function | (inherits)                            |
| Context-Independent Feature| Feature             | informs → Intrinsic Function          |
| Context-Dependent Feature  | Feature             | informs → Contextual Function         |
| Timespan                   | (root)              | is qualified by → Formal Function; is embedded in → Timeline |
| Musical Context            | Timespan            | (subclass)                            |
| Timeline                   | owl:Thing           | embeds → Timespan                     |
| Musical Expression         | (root)              | elapses over → Timeline               |
| Musical Domain             | Musical Expression  | is operationalised by → Feature       |
| Weightedness               | Form-functional Aspect | (subclass)                         |
| Directionality             | Form-functional Aspect | (subclass)                         |
| Temporality                | Form-functional Aspect | (subclass)                         |

**Object properties** (12): `is characterised by` / `characterises`,
`is realised as` / `realises`, `qualifies` / `is qualified by`,
`is informed by` / `informs`, `operationalises` / `is operationalised by`,
`is embedded in` / `embeds`, `elapses over`, `is context of`.

**Critical notes:**

- URIs are WebProtégé-generated opaque identifiers
  (`http://webprotege.stanford.edu/R7IpFvmDUSeck6CfF59w0GI`), not
  project-owned namespaces.
- `rdfs:isDefinedBy` is used for definitions (only 2 classes have them).
- No `owl:versionInfo`, no version IRI, no contributor metadata.
- The Intrinsic/Contextual Function distinction, the Feature/Domain hierarchy,
  and the Form-functional Aspect subclasses (Weightedness, Directionality,
  Temporality) represent domain modelling decisions that may or may not carry
  forward.

### 1.6 The Brahms Paper

`ontology/model_of_music_analysis/Brahms_Form_New_text.html` contains a paper
modelling music analysis as **Claim Production by Agents**, drawing on IFLA LRM
(Library Reference Model) and CIDOC CRM (Conceptual Reference Model).  This
paper provides the theoretical foundation for the ontology and informs the
metaconcept/concept/metafeature/feature hierarchy described in Spec 3.

### 1.7 Consolidated Gap Analysis

| Gap | Severity | Affects |
|-----|----------|---------|
| No single source of truth (spreadsheet ≠ EBNF ≠ Python enums) | Critical | All downstream components |
| No concept definitions (which features define a concept) | Critical | Annotation quality, validation |
| No hierarchical relations between concepts in Python | High | Model expressiveness |
| No version alignment across components | High | Reproducibility |
| No automated change propagation | High | Developer/annotator friction |
| Only 2 of ~60+ vignettes | Medium | Documentation completeness |
| Minimal test coverage | Medium | Reliability |
| Domain model doubles as parser output consumer | Medium | Separation of concerns |
| Wiki submodule update is manual | Low | Documentation freshness |
| OWL ontology is deprecated with opaque URIs | Informational | Future ontology work |
| release-please action is at v3 (current: v4) | Low | CI reliability |

---

## 2. Terminology

The following terms are used precisely throughout this document.  The word
"metaclass" is avoided to prevent confusion with Python's `metaclass`.

**Metaconcept** (e.g., "Caesura"):
An abstract class stipulating the overarching meaning/use of a class of
concepts, potentially across musical styles.  Defines the upper, more
style-independent layers of the ontology.  Includes the set of
metaconcepts/concepts/metafeatures needed to obtain a concrete, parametrized
concept.  There is a continuum where child metaconcepts become more concrete
by swapping abstract components with concrete ones ("conditioning" /
"predicating").  The child that replaces the very last unconditioned component
constitutes the "quantum leap" from metaconcept to concept.  In Python, could
be implemented as runtime-checkable Protocols.

**Concept** (e.g., "Half Cadence in the Viennese classic"):
A fully conditioned, parametrized subclass of a metaconcept.  When resolved
against a musical object, yields a congruence score.  An atomic concept can
become a small class hierarchy of metafeatures (probability distribution,
score-based ranking, single imperative value, logic-based values, etc.).
A non-atomic concept defines acceptable congruence score ranges (for the
resolved metafeatures).  A concept defines which types of musical objects it
can be applied to (i.e., it may serve as a type guard in the Python sense).

**Metafeature** (e.g., "dominant harmony"):
The combination of a concept with some value range.  A component within a
concept definition that specifies not a single value but a range, distribution,
or ranked set of acceptable values for a given feature.

**Feature** (e.g., "dominant harmony with Roman numeral V, indicating a root
position triad"):
The outcome of resolving a metafeature against a musical object.  The
combination of a concept with a specific value.  Exposes nested structure
corresponding to the resolved definition components (because concepts are
recursively defined, resolving a feature may yield sub-features).

---

## 3. Goals — Dependency Graph

Goals are structured as a directed acyclic graph.  An arrow `G_x → G_y` means
G_x must be achieved before G_y can begin.  Goals in the same phase can be
pursued concurrently if their specific dependencies are met.

```
Phase 0 — Foundation (no root dependency)
──────────────────────────────────────────
  G0  Terminology consolidation
  G1  Current state audit and gap analysis ← (this document)
  G2  Existing analysis baseline
        (validate current TiLiA analyses with current tools;
         establish quantitative pass/fail baseline)

Phase 1 — Architectural Decision
─────────────────────────────────
  G3  Root paradigm decision ← G0, G1
        (evaluate options (a)–(e) per Section 4;
         requires human decision informed by this analysis)

Phase 2 — Infrastructure
─────────────────────────
  G4  Source of truth setup ← G3
        (create/configure the chosen root representation)
  G5  Derivation pipeline ← G4
        (scripts/tooling to generate downstream artifacts from root)
  G6  CI consistency checks ← G5
        (fail build when any derived artifact is out of sync)
  G7  Collaborative editing setup ← G4
        (configure the editing environment for the chosen root)

Phase 3 — Integration
─────────────────────
  G8   EBNF ↔ model synchronization ← G5
         (either generate EBNF from root, or generate enum lists
          from EBNF, or bidirectional check — depends on G3)
  G9   musicalform library restructuring ← G5
         (separate domain model from parser output; populate from root)
  G10  Annotation validation pipeline expansion ← G8, G9
         (validate .tla files against the next candidate model version)
  G11  Validation shapes (SHACL or Python tests) ← G4
         (if OWL is part of the architecture: SHACL shapes;
          if Python-only: property-based tests and type constraints)

Phase 4 — Workflow
──────────────────
  G12  Full collaborative workflow operational ← G6, G7, G10
         (change definition → PR → auto-propagation → CI → merge → release)
  G13  Documentation pipeline ← G9, G12
         (auto-generated reference + manual curation in Quarto)
  G14  Version alignment ← G6, G12
         (SemVer across all components; release-please integration)

Phase 5 — Content
─────────────────
  G15  Concept definitions at scale ← G12
         (the daily work; thousands of iterations)
  G16  Vignette workflow ← G13
         (auto-generated stub + manually curated narrative)
  G17  Existing analysis migration/validation ← G10, G15
         (iterative dialectic between model and annotation_pilot analyses)
```

**ASCII DAG (simplified):**

```
G0 ──┐
G1 ──┤
     ├→ G3 ──→ G4 ──→ G5 ──→ G6 ──→ G12 ──→ G15
G2   │         │      │      │       ↑       G16
     │         │      ├→ G8 ─┤       │       G17
     │         ├→ G7  ├→ G9 ─┼→ G10 ─┘
     │         │      │      │
     │         └→ G11 ┘      ├→ G13 → G16
     │                       ├→ G14
     │                       └→ G17
     └────────────────────────→ G2 (feeds back into G17)
```

**Key observation:** G3 (root paradigm decision) is the critical-path
bottleneck.  Nearly all downstream work depends on it.  The analysis in
Section 4 is designed to enable this decision.

---

## 4. The Project Root Question

The "project root" is the canonical, authoritative representation from which
all other representations are derived or against which they are validated.
The importance of the `musicalform` Python library does not preclude operating
with upstream **control files** that generate parts of the library
programmatically.

### 4.1 Evaluation Criteria

| # | Criterion | Weight | Rationale |
|---|-----------|--------|-----------|
| C1 | Daily workflow optimality | Critical | The change→PR→propagation→CI→merge→release cycle will be performed thousands of times.  Friction here is multiplied. |
| C2 | Accessibility for non-developers | Critical | Musicologists who are not Python developers must be able to participate directly in concept definitions. |
| C3 | Expressiveness | Critical | The model requires metaconcept hierarchies, concept conditioning, metafeature value ranges, congruence scoring, type guards, recursive definitions. |
| C4 | Dependency risk | High | 3rd-party tool dependencies produce technological debt.  Abandonware risk must be visible. |
| C5 | Code generation complexity | High | If the root is not Python, a robust generator must be built and maintained. |
| C6 | Version control friendliness | Medium | Git diffs should be human-readable for review. |
| C7 | Incremental adoptability | Medium | The migration from current state should be gradual, not big-bang. |

### 4.2 Option (a): Python Object Hierarchy as Root

**What it means:** `musicalform/src/musicalform/enums.py`, `core.py`, and
future modules ARE the model.  All vocabulary terms, concept definitions,
metaconcept hierarchies, and metafeature specifications are expressed as Python
code (enums, dataclasses, Protocols, type annotations).  OWL, EBNF, and
documentation are derived from Python.

**Who edits:** Developers in an IDE.  Non-developers describe desired changes
to a developer, or learn enough Python to edit enum members.

**Expressiveness:**

Python can express:

- Class hierarchies (inheritance, ABCs, Protocols)
- Type constraints (type annotations, runtime-checkable Protocols, TypeGuard)
- Validation logic (property methods, `__post_init__`, custom validators)
- Enumerated vocabularies with aliases (`FancyStrEnum`)
- Dataclass-based parametric definitions

Python cannot natively express:

- OWL-style description logic axioms (e.g., "every FormalFunction that is
  characterised by exactly 2 Aspects and is realised as some FormalType")
- Property characteristics (transitivity, symmetry, reflexivity)
- Open-world reasoning (checking whether inferred facts follow from axioms)
- Domain/range constraints as first-class metadata (possible via decorators
  but bespoke)

These gaps can be bridged by custom abstractions, but the result is a
project-specific modelling framework rather than a standards-based one.

**Daily workflow:**

1. Developer opens IDE, edits enum member or dataclass.
2. Runs `pytest` locally.
3. Creates PR; CI runs: tests, lint, type-check, sync-check (EBNF ↔ enums).
4. Colleagues review Python diff.
5. Merge triggers release-please → version bump → generated artifacts rebuild.

For a musicologist to add a concept: they must either learn to write
`class HalfCadenceVienneseClassic(Concept): ...` or describe the concept to a
developer who translates it.

**Downstream generation (what must be built):**

- Python → EBNF: Extract enum members, generate EBNF production rules.
  Moderate complexity.  The current EBNF's `SpecificFunction` and `FormalType`
  productions are essentially enum listings; generation is straightforward.
- Python → OWL: Traverse class hierarchy, emit OWL axioms.  Owlready2 makes
  this feasible but the mapping from Python idioms (FancyStrEnum aliases,
  dataclass defaults, Protocol constraints) to OWL constructs requires custom
  logic.  Medium-high complexity.
- Python → Documentation: Sphinx/mkdocs autodoc or Quarto with pre-render
  script.  Well-established tooling.

**Git friendliness:** Excellent.  Python source diffs are clear and reviewable.

**Dependency risk:** Very low.  Python stdlib + standard tooling.  No 3rd-party
dependency for the model itself.

**Incremental adoptability:** High.  The current `musicalform` library already
exists; expanding it is natural.

**What this option rules out:**

- Using ontology editors (Protégé, VocBench) as primary editing tools.  They
  become consumers of generated OWL, not producers.
- Non-developers editing the model directly.
- OWL reasoning at the source level (only on generated output).
- Collaborative web-based editing (unless a bespoke web UI is built).

**What this option enables:**

- Full Python toolchain: mypy, pytest, IDE autocompletion, refactoring.
- Tight coupling between model and validation/parsing code.
- No impedance mismatch between model and the software that uses it.

**Score on evaluation criteria:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| C1 Daily workflow | Good | Fast for developers; slow for non-developers |
| C2 Accessibility | Poor | Requires Python knowledge |
| C3 Expressiveness | Good | Sufficient with custom abstractions; not OWL-grade |
| C4 Dependency risk | Excellent | Near-zero |
| C5 Codegen complexity | Medium | EBNF generation straightforward; OWL generation moderate |
| C6 VCS friendliness | Excellent | Clear diffs |
| C7 Incremental adoption | Excellent | Extends existing codebase |

### 4.3 Option (b): OWL File as Root

**What it means:** An OWL file (preferably serialized as Turtle for
Git-friendly diffs) is THE model.  It is edited via an ontology editor (Protégé
desktop, WebProtégé, or another editor).  Python enums, dataclasses, and EBNF
are generated from OWL.

**Who edits:** Anyone with access to the ontology editor.  Desktop Protégé
requires installation; WebProtégé or VocBench (see Section 5.1) require a
server.

**Expressiveness:**

OWL 2 DL can express:

- Class hierarchies with multiple inheritance
- Object properties with domain/range, cardinality restrictions
- Property characteristics (transitivity, symmetry, reflexivity, etc.)
- Class restrictions (existential, universal, hasValue, cardinality)
- Equivalence and disjointness axioms
- Annotation properties for definitions, labels, abbreviations
- Named individuals for concrete instances

This is substantially more expressive than Python for ontological modelling.
The metaconcept → concept conditioning continuum maps naturally to OWL class
hierarchies with progressive restriction.  Metafeature value ranges can be
modelled as datatype restrictions or custom annotation properties.

**Daily workflow (with desktop Protégé + Git):**

1. Open Protégé, load OWL file from Git working copy.
2. Add/edit class, property, or annotation.
3. Save (Turtle format).  Commit to Git.  Push, create PR.
4. CI: parse OWL → validate consistency (reasoner) → generate Python →
   run tests → generate EBNF → generate docs.
5. Colleagues review Turtle diff (readable but less familiar than Python).
6. Merge triggers release pipeline.

**Daily workflow (with web-based editor like VocBench):**

1. Open browser, navigate to VocBench instance.
2. Add/edit class, property, or annotation.
3. VocBench records change in its internal history.
4. Export OWL (Turtle) → commit to Git → PR.
   (This export step is a friction point; automation required.)
5. CI pipeline as above.
6. Colleagues review on GitHub.

**Downstream generation (what must be built):**

- OWL → Python enums: Traverse OWL classes annotated as vocabulary terms,
  extract `rdfs:label` and abbreviation annotations, emit `FancyStrEnum`
  members.  Medium complexity.  The generator must handle: multiple alias
  annotations per class, the mapping between OWL class hierarchy and Python
  enum/dataclass hierarchy, and the FancyStrEnum alias pattern.
- OWL → Python dataclasses: Traverse OWL class restrictions, translate to
  dataclass fields with type annotations.  High complexity.  OWL restrictions
  (existential quantification, cardinality) do not map 1:1 to Python dataclass
  fields.  A mapping convention must be designed and documented.
- OWL → EBNF: Extract vocabulary terms from designated OWL classes, emit
  EBNF productions.  Medium complexity (similar to Python → EBNF).
- Owlready2 provides partial automation: it exposes OWL classes as Python
  classes with properties.  However, the generated classes would NOT match the
  current `FancyStrEnum` + `@dataclass` pattern.  Either the Python library
  adapts to Owlready2's idioms, or a custom generator is written.

**Git friendliness:** Good if Turtle serialization is used (one triple per line,
readable diffs).  Poor if OWL/XML or RDF/XML is used (verbose, noisy diffs).
**Turtle must be enforced as the serialization format.**  Protégé can save as
Turtle; it must be configured to do so consistently (sorted output, stable
blank node identifiers).

**Dependency risk:** Moderate.

- The OWL format itself is a W3C standard — zero format risk.
- The editing tool is a dependency:
  - Protégé desktop: free, open source, Stanford-backed, actively maintained
    (v5.6.9, March 2025).  Plugin ecosystem is stale.  Single-user.
  - WebProtégé: free, open source, being re-architected to microservices.
    Hosted instance at Stanford.  Your existing OWL was created here.
  - VocBench: free, open source, EU-funded.  Self-hosted.  See Section 5.1.
- The code generator (OWL → Python) is custom and must be maintained.
- OWL reasoning requires Java (HermiT, Pellet) unless using OWL-RL (Python,
  limited profile).

**Incremental adoptability:** Medium.  Requires:

1. Designing the OWL ontology from scratch (the existing one is deprecated
   and uses opaque WebProtégé URIs).
2. Minting a proper namespace.
3. Building the OWL → Python generator.
4. Rewriting or adapting the `musicalform` library to consume generated code.

These are significant upfront investments before daily vocabulary work can begin.

**What this option rules out:**

- Direct hand-editing of model Python code (model code is generated).
- Using Python-native type checking on the model definition itself (generated
  code can be type-checked, but the source is OWL, not Python).

**What this option enables:**

- Full OWL 2 reasoning for consistency checking.
- SHACL shapes for data quality validation.
- Ontology editors as primary tools (Protégé, VocBench, etc.).
- Linked data / semantic web interoperability.
- Potential publication of the ontology as a formal standard.
- Formal foundation for the IFLA LRM / CIDOC CRM integration described in
  the Brahms paper.

**Score on evaluation criteria:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| C1 Daily workflow | Medium | Depends on editor; export→commit friction |
| C2 Accessibility | Good | Web editors are accessible; Protégé desktop less so |
| C3 Expressiveness | Excellent | Full OWL 2 DL |
| C4 Dependency risk | Medium | Editor + generator + optional Java |
| C5 Codegen complexity | High | OWL→Python mapping is non-trivial |
| C6 VCS friendliness | Good | With Turtle serialization |
| C7 Incremental adoption | Low-Medium | Significant upfront work |

### 4.4 Option (c): Spreadsheet / Tabular Tool as Root

**What it means:** A spreadsheet (Google Sheets, Nextcloud Spreadsheet, or
Excel) defines the vocabulary.  Columns encode: term, abbreviation,
function/type, hierarchical level, definition, relations, metafeature
parameters, etc.  Both Python and OWL (if desired) are generated from the
spreadsheet via scripts.

This is essentially a formalized version of the current state (the Nextcloud
spreadsheet), elevated from "informational resource" to "authoritative root."

**Who edits:** Anyone with browser access.  Spreadsheets are universally
familiar.

**Expressiveness:**

A spreadsheet can express:

- Flat vocabulary lists (term, abbreviation, type, level)
- Simple properties (one value per cell)
- Simple parent-child hierarchies (via a "parent" column)
- Tabular definitions (columns for each property)

A spreadsheet cannot practically express:

- Complex class hierarchies with multiple inheritance
- Recursive concept definitions (a concept whose metafeatures are themselves
  concepts)
- The metaconcept → concept conditioning continuum (requires structured data
  within cells or multiple linked sheets, becoming unwieldy)
- Property characteristics (transitivity, etc.)
- Cardinality constraints, restriction axioms
- Multi-valued structured relations (e.g., a concept with 3 metafeatures,
  each with different value range types)
- Congruence score ranges as a function of resolved metafeatures

**The existing spreadsheet already demonstrates this limitation:** it has
deprecated columns, inconsistent use of the "Relation: contains" column (some
cells have comma-separated lists, others are empty), and no way to express the
rich concept definitions described in Section 2 (Terminology).

**Daily workflow:**

1. Open spreadsheet in browser, add/edit row.
2. Manual or automated export to CSV, commit to Git, PR.
3. CI: parse CSV → generate Python enums + OWL → run tests → generate docs.
4. Colleagues review generated diffs (not the spreadsheet diff, unless using
   a CSV diff tool).
5. Merge triggers release.

**Problem:** The review step is awkward.  Reviewing a CSV diff is less
informative than reviewing a Python or Turtle diff.  The spreadsheet itself
(if cloud-hosted) has its own version history that is disconnected from Git.

**Downstream generation:**

- CSV → Python enums: Straightforward for flat vocabulary; a script reads rows
  and emits `FancyStrEnum` members.  Low complexity for the current vocabulary
  scope.  But: as concept definitions become richer (metafeatures, value
  ranges, conditioning), the CSV → Python mapping becomes fragile and
  convention-heavy (special column names, cell formats, cross-sheet references).
- CSV → OWL: VocBench's Sheet2RDF tool or custom scripts.  Similar complexity
  profile.
- CSV → EBNF: Extract term names and aliases, emit productions.  Low
  complexity.

**Git friendliness:** CSV diffs are readable line-by-line but lack context
(column headers are not repeated on each line).  Tab-separated formats are
marginally better.  Spreadsheet-native formats (XLSX) produce binary diffs.

**Dependency risk:** Very low for the spreadsheet tool itself.  Moderate for
the generation scripts (custom, must handle increasingly complex CSV schemas).

**Incremental adoptability:** High.  The CSV already exists.  Promoting it to
root requires only formalizing the schema and writing generation scripts.

**What this option rules out:**

- Rich ontological modelling at the source level.
- OWL reasoning at source level.
- Complex structured definitions without elaborate multi-sheet conventions
  that defeat the purpose of spreadsheet accessibility.

**What this option enables:**

- Maximum accessibility: any browser, no installation, universal familiarity.
- Easy bulk editing (sort, filter, find-replace across rows).
- Cloud collaboration (simultaneous editing with Google Sheets/Nextcloud).
- Simple generation pipeline.

**The fundamental tension:** This option is optimal for the current vocabulary
(~60 active terms with simple properties) but will become a bottleneck as the
model grows toward the complex concept definitions described in Section 2.
The question is: will the daily work remain at the "add a term with an
abbreviation" level, or will it evolve to "define a concept with 5 metafeatures
each having parametrized value ranges"?  If the latter, option (c) will require
either abandonment or augmentation with structured data files that erode the
accessibility advantage.

**Score on evaluation criteria:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| C1 Daily workflow | Excellent | For simple vocabulary; degrades with complexity |
| C2 Accessibility | Excellent | Universal familiarity |
| C3 Expressiveness | Poor | Fundamentally tabular; cannot capture rich definitions |
| C4 Dependency risk | Excellent | Spreadsheet tools are commodity |
| C5 Codegen complexity | Low→High | Low for flat vocab; high as definitions grow complex |
| C6 VCS friendliness | Medium | CSV diffs readable but context-poor |
| C7 Incremental adoption | Excellent | CSV already exists |

### 4.5 Option (d): Dedicated Vocabulary Management Platform as Root

**What it means:** A platform (VocBench, Metaphactory, or similar) is THE
primary editing environment.  The platform's internal data store is the
authoritative source.  OWL exports and Python code are derived from the
platform's state.

**Key difference from option (b):** In (b), the OWL *file* is the root and
can be edited by any tool.  In (d), the *platform* is the root; the OWL file
is an export artifact.  This means:

- The platform's internal representation (which may include workflow states,
  user annotations, change proposals) is authoritative.
- Git receives periodic OWL exports, not real-time edits.
- The platform manages its own versioning; Git versioning is secondary.

**Who edits:** Anyone with browser access to the platform.

**Expressiveness:** Depends on the platform.

- VocBench: Full OWL 2, SKOS, Ontolex-lemon.  Equivalent to option (b) in
  expressiveness.
- Metaphactory: Full OWL 2 + SHACL.  Equivalent or better.
- PoolParty: Primarily SKOS/taxonomy.  Insufficient for full OWL modelling.
- Others: See Section 5.1 for detailed evaluation.

**Daily workflow (with VocBench):**

1. Open browser, navigate to VocBench.
2. Add/edit class, property, annotation.
3. Submit change for review (VocBench's built-in workflow: propose → validate
   → approve).
4. On approval, automated export: OWL (Turtle) → commit to Git → PR.
5. CI: parse OWL → generate Python → run tests → generate docs.
6. PR merge triggers release.

**The double-review problem:** VocBench has its own review workflow, and GitHub
has PRs.  Running both creates friction.  Options:

- Use VocBench review only; Git/GitHub is a passive archive.  Loses GitHub's
  code review features (inline comments, CI integration).
- Use GitHub review only; VocBench is a dumb editor (no internal workflow).
  Loses VocBench's domain-specific validation.
- Use VocBench for domain review + GitHub for technical review.  Most complete
  but highest ceremony.

**Downstream generation:** Same as option (b) — the exported OWL file feeds
the same generators.

**Git friendliness:** Depends on export automation.  If exports are frequent
and automated, Git history is useful.  If exports are infrequent, Git history
has large, unreviewed jumps.

**Dependency risk:** High.

- The platform is a critical runtime dependency for editing (not just a tool
  that produces files).
- Self-hosted platforms (VocBench) require server maintenance: Java 17+,
  application server, potentially a triple store backend.
- If the platform goes down, editing stops.
- If the platform is abandoned, migration requires exporting all data and
  finding a new editor (data is in OWL/RDF, so format portability is
  maintained, but workflow/history is lost).
- Commercial platforms (Metaphactory, PoolParty) add recurring cost risk.

**Incremental adoptability:** Low.  Requires:

1. Deploying and configuring the platform.
2. Designing the OWL ontology in the platform.
3. Setting up the export → Git → CI pipeline.
4. Training team members on the platform.
5. Building the OWL → Python generator.

All of this must happen before daily vocabulary work can use the platform.

**What this option rules out:**

- Editing model files directly in a text editor or IDE.
- Using Git as the primary version control (platform history is primary).
- Offline editing (requires platform server to be running).

**What this option enables:**

- Best collaborative editing experience (built-in workflows, roles, validation).
- Domain-specific editing interfaces (class hierarchies, property matrices).
- Potentially the smoothest non-developer experience.
- Built-in SPARQL/reasoning if the platform supports it.

**Score on evaluation criteria:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| C1 Daily workflow | Good | Smooth in-platform; export→Git friction |
| C2 Accessibility | Good-Excellent | Web-based, no installation needed |
| C3 Expressiveness | Excellent | Full OWL 2 (with VocBench/Metaphactory) |
| C4 Dependency risk | High | Platform is a critical runtime dependency |
| C5 Codegen complexity | High | Same as (b): OWL→Python generator needed |
| C6 VCS friendliness | Medium | Depends on export frequency and automation |
| C7 Incremental adoption | Low | Significant deployment and setup required |

### 4.6 Option (e): Hybrid

**What it means:** Two layers with different management paradigms:

- **Top layer (metaconcept architecture):** The abstract class hierarchy,
  structural rules, property definitions, and Python ABCs/Protocols.  Managed
  in Python (option (a) for this layer).  Expected to stabilize within weeks.
- **Vocabulary layer (concept definitions):** Individual terms, abbreviations,
  concept definitions, metafeature specifications, hierarchical relations.
  Managed via an accessible tool — spreadsheet (c), OWL editor (b), or
  platform (d).  This is the bulk of daily work.

**Who edits:** Developers edit the top layer in Python.  Musicologists edit
the vocabulary layer in the accessible tool.

**The boundary question:** The viability of this option depends entirely on
whether a clean, stable boundary can be drawn between the two layers.  If the
boundary shifts frequently, synchronization becomes a constant source of bugs.

Candidate boundaries:

1. **ABCs/Protocols in Python, instances/subclasses in vocabulary tool.**
   Python defines `FormalFunction(Protocol)`, `Concept(Protocol)`, etc.
   The vocabulary tool defines `HalfCadence`, `Sentence`, etc. as subclasses
   or instances.  *Risk:* Adding a new metaconcept (e.g., a new kind of formal
   function aspect) requires Python changes that the vocabulary tool must then
   reference.

2. **Structural rules in Python, term lists in vocabulary tool.**
   Python defines how labels are structured (the grammar, the combination
   rules).  The vocabulary tool provides the list of valid terms.  *Risk:*
   Some terms carry structural implications (e.g., `FunctionalTransformation`
   has a source and target, which is structural).  The boundary is leaky.

3. **Everything above the leaf level in Python, leaves in vocabulary tool.**
   Python defines the class hierarchy down to the level where individual
   concepts are added.  The vocabulary tool populates the leaf classes.
   *Risk:* The leaf level is not uniform — some "leaves" are simple (an enum
   member) while others are complex (a concept with multiple metafeatures).

**Expressiveness:** Depends on the vocabulary tool chosen for the lower layer.
The top layer has full Python expressiveness.  The combination is potentially
the most expressive, but the interface between layers must be carefully
designed.

**Daily workflow:**

For vocabulary work (frequent):
1. Open accessible tool, add/edit concept.
2. Export → commit → PR.
3. CI: validate vocabulary against top-layer constraints → generate derived
   artifacts → tests.
4. Review, merge, release.

For structural work (infrequent):
1. Developer edits Python, commits, PR.
2. CI: re-validate vocabulary against updated structure → regenerate.
3. Review, merge, release.

**Downstream generation:**

- Two sources must be reconciled: Python top layer + vocabulary tool output.
- The generation pipeline is more complex: it must merge the two sources into
  a consistent whole.
- Sync checks must verify that the vocabulary conforms to the top-layer
  constraints.

**Git friendliness:** Good for the Python layer.  Depends on the vocabulary
tool for the other layer.

**Dependency risk:** Moderate — same as whichever tool is chosen for the
vocabulary layer.

**Incremental adoptability:** Medium-High.  The Python top layer exists
(expanding `musicalform`).  The vocabulary layer can start with the existing
CSV and migrate to a richer tool later.

**What this option rules out:** Nothing categorically, but the complexity of
maintaining two paradigms is the cost.

**What this option enables:** Combining Python's strengths (tooling, type
safety, IDE support) with an accessible interface for vocabulary work.

**Score on evaluation criteria:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| C1 Daily workflow | Good | Smooth for vocabulary if tool is well-chosen |
| C2 Accessibility | Good | Lower layer is accessible; top layer is not |
| C3 Expressiveness | Excellent | Full Python + full vocabulary tool |
| C4 Dependency risk | Medium | Depends on vocabulary tool choice |
| C5 Codegen complexity | High | Two-source reconciliation |
| C6 VCS friendliness | Good | Python layer excellent; vocabulary layer varies |
| C7 Incremental adoption | Medium-High | Can start with CSV, migrate later |

### 4.7 Comparative Summary

| Criterion | (a) Python | (b) OWL | (c) Spreadsheet | (d) Platform | (e) Hybrid |
|-----------|-----------|---------|-----------------|-------------|-----------|
| C1 Daily workflow | Good | Medium | Excellent→Poor* | Good | Good |
| C2 Accessibility | **Poor** | Good | **Excellent** | Good-Excellent | Good |
| C3 Expressiveness | Good | **Excellent** | **Poor** | Excellent | Excellent |
| C4 Dependency risk | **Excellent** | Medium | **Excellent** | **High** | Medium |
| C5 Codegen complexity | Medium | **High** | Low→High* | **High** | High |
| C6 VCS friendliness | **Excellent** | Good | Medium | Medium | Good |
| C7 Incremental adoption | **Excellent** | Low-Medium | **Excellent** | **Low** | Medium-High |

*Asterisk: rating degrades as concept definitions grow more complex.

### 4.8 Decision-Consequence Map

Each root choice constrains or enables specific tooling and paradigm choices
downstream.  The following table shows which doors each option opens and
closes:

| Decision | (a) Python root | (b) OWL root | (c) Spreadsheet root | (d) Platform root | (e) Hybrid |
|----------|----------------|-------------|---------------------|------------------|-----------|
| Primary editor | IDE (VS Code, PyCharm) | Ontology editor | Spreadsheet app | Platform UI | IDE + vocabulary tool |
| OWL reasoning | On generated OWL only | At source level | On generated OWL only | Depends on platform | On generated/exported OWL |
| SHACL validation | On generated OWL only | At source level | On generated OWL only | If platform supports it | On vocabulary layer exports |
| Non-developer editing | Not possible | With web-based editor | Directly | Directly | For vocabulary layer only |
| Graph visualization | On generated OWL | On source OWL | On generated OWL | Built into some platforms | On OWL layer |
| Linked data publication | From generated OWL | Natively | From generated OWL | From platform exports | From OWL layer |
| CIDOC CRM/IFLA LRM integration | Requires OWL mapping layer | Native OWL alignment | Requires OWL mapping layer | If OWL-based platform | Via OWL vocabulary layer |
| Ontology editor tooling (Protégé, VocBench) | Import-only (consume generated OWL) | Primary tool | Import-only | IS the tool | For vocabulary layer |
| Python type-checking of model | Direct (mypy) | On generated code | On generated code | On generated code | Direct for top layer; generated for vocabulary |
| Custom Python model patterns (FancyStrEnum, @dataclass) | Direct control | Must be generated (high complexity) | Must be generated (medium) | Must be generated (high) | Direct for top; generated for vocabulary |

### 4.9 Analysis and Recommendation

**Option (c) is insufficient as a long-term root.** The existing spreadsheet
already fails to capture the model's complexity, and the concept definitions
described in Section 2 far exceed what tabular representation can handle.
Option (c) may serve as a short-term stepping stone (Phase 0–1 vocabulary
capture) but not as the architectural root.

**Option (d) introduces unnecessary dependency risk** without proportional
benefit over option (b).  The platform adds a critical runtime dependency
(server uptime, maintenance, training) for an editing convenience that (b)
already provides via web-based editors like VocBench — but in (b), VocBench is
an interchangeable editor, not the root itself.  If VocBench is abandoned in
(b), you switch to Protégé desktop and continue editing the same Turtle file.
In (d), if the platform is abandoned, you must migrate the entire editing
workflow.

**The real choice is between (a), (b), and (e).**  The decision hinges on one
empirical question that only the project team can answer:

> **How complex will the daily concept definition work actually be?**

**If concept definitions are primarily vocabulary entries** (name, abbreviation,
hierarchical level, parent concept, short definition, a few typed relations) —
i.e., the majority of daily edits look like "add term X as a child of Y with
abbreviation Z" — then:

- **Option (a)** is viable: each addition is 1–5 lines of Python.  The
  accessibility barrier is real but manageable if the team includes at least
  one developer who can translate musicologist requests quickly.
- **Option (e) with CSV vocabulary** is also viable: the spreadsheet handles
  the simple additions; Python handles the structural backbone.

**If concept definitions are rich parametric structures** (multiple metafeatures
with value ranges, congruence score thresholds, type guards, recursive
sub-concept references) — i.e., the daily edits look like "define concept X
with metafeatures M1(range=[0.3, 0.7], type=probability), M2(values={V, V7},
ranking=score-based), applicable to Timespan objects of level ≥ Phrase" — then:

- **Option (b)** becomes attractive: OWL's expressiveness handles this
  natively, and web-based editors give musicologists a structured form
  interface for these complex entries.
- **Option (e)** becomes attractive: Python defines the structural framework
  for these parametric definitions, and the vocabulary tool provides the
  accessible interface for populating them.
- **Option (a)** is still viable but the accessibility cost is higher, because
  each concept definition is a substantial Python class.

**Recommendation:** The project team should decide between **(a)** and **(b)**
(or **(e)** which combines elements of both, at the cost of additional
complexity).

To make this decision concrete, I recommend the following test:

1. **Write 5 representative concept definitions** by hand — 2 simple ones
   (like "basic idea") and 3 complex ones (like "Half Cadence in the Viennese
   classic" with full metafeature specifications).
2. **Express each in Python** (as a dataclass/Protocol/enum combination).
3. **Express each in OWL** (as a class with restrictions and annotations).
4. **Show both versions to 2–3 musicologists** who will do the daily work.
5. **Ask:** Which representation would you rather create and edit for 500 more
   concepts?  Which can you read and review?

This test produces the empirical evidence needed for the decision.  The rest
of this architecture document is parameterized by the root choice: each section
notes what changes depending on which option is selected.

---

## 5. Tooling — Module-by-Module Exploration

For each module, the analysis explores (1) applicable paradigms, (2) leading
software solutions per paradigm, and (3) dependency paths — how each choice
impacts other modules.

### 5.1 Module: Vocabulary / Ontology Management (Primary)

This module is directly coupled to the project root decision (Section 4).

#### Paradigm 1: Python-native

No additional tool needed; the model lives in `.py` files.

| Aspect | Assessment |
|--------|-----------|
| Solutions | IDE (VS Code, PyCharm, vim) |
| Dependency | None beyond Python |
| Impact on other modules | OWL/RDF module becomes export-only; visualization requires generated OWL |

#### Paradigm 2: File-based OWL + Desktop Editor

The OWL file (Turtle serialization) lives in Git.  An ontology editor opens
and saves it.

| Solution | Status | OWL Support | Collaboration | Git Integration | Visualization | License | Risk |
|----------|--------|-------------|---------------|-----------------|---------------|---------|------|
| **Protégé 5.6.x** | Active (v5.6.9, Mar 2025) | Full OWL 2 | None (single-user desktop) | None built-in; file-on-disk → Git | Class tree + OntoGraf plugin (limited) | Free, BSD-like, Stanford-backed | Low (decades of funding) |
| **Eddy 3.8** | Active (v3.8, Jan 2026) | OWL 2 QL/RL/EL | None (desktop) | None built-in | Graphol visual notation (graph editing as primary interface) | GPL v3 | Medium (small team, Python/Qt) |
| **OWLGrEd 1.6** | Active | Full OWL 2 | None (desktop) | None built-in | UML-style diagrams with in-diagram editing | Free | Medium (University of Latvia team) |

**Dependency path:** Choosing file-based OWL + desktop editor means no
collaborative web-based editing.  Multiple musicologists cannot work
simultaneously.  PRs contain Turtle diffs.

#### Paradigm 3: Web-based Collaborative OWL Editor

A server-hosted editor manages the OWL model; multiple users edit
simultaneously.

| Solution | Status | OWL Support | Collaboration | Git Integration | Visualization | License | Risk |
|----------|--------|-------------|---------------|-----------------|---------------|---------|------|
| **VocBench 3** | Active, EU-funded (Digital Europe Programme) | Full OWL 2, SKOS, Ontolex | Yes: roles, proposal→validation→approval workflow | None native; export + commit required | Class hierarchy browsing, property views; basic graph | Free, open source | Low-Medium (EU-funded, open source; but single research group at U. Rome Tor Vergata) |
| **WebProtégé** | Being re-architected (microservices); hosted at Stanford | Full OWL 2 | Yes: multi-user, in-browser, comments, per-entity history | None native; export required | Added in 4.0; limited graph | Free, open source, BSD-2 | Medium (re-architecture in progress; hosted instance could change) |
| **Metaphactory** | Active commercial product | Full OWL 2 + SHACL | Yes: multi-user, workflow states | **Native Git integration** (distinguishing feature) | Interactive graph, tables, charts, timelines | **Commercial** (enterprise pricing) | Moderate (commercial; data portable as OWL/RDF) |

**Dependency path:** Choosing a web-based editor means:

- Server infrastructure needed (Docker, Java 17+ for VocBench; Stanford-hosted
  for WebProtégé).
- Export automation needed (OWL export → Git commit → CI trigger).
- If the editor is the root (option d), it becomes a critical dependency.
  If the OWL file is the root (option b), the editor is interchangeable.

**VocBench evaluation detail:**

- Backend: Semantic Turkey (Java).  Requires a triple store (built-in
  in-memory for small ontologies; Jena Fuseki or GraphDB for production).
- Deployment: Docker available.  ~10 min setup for standalone mode.
- Workflow: Propose→validate→approve.  Role-based access.  Change history.
- Export: OWL (all serializations), SKOS, CSV (via Sheet2RDF).
- API: REST, SPARQL via backend triple store.
- Limitation: No Python API.  Automation requires REST calls.
- Limitation: Visualization is functional but not publication-quality.
- Sustainability: Maintained since 2013.  EU Digital Europe funding is
  multi-year but not permanent.  Open source mitigates abandonment risk
  (community can fork).

#### Paradigm 4: Spreadsheet-based

The vocabulary lives in a tabular tool.  See Section 4.4 for the full analysis.
Key additional tooling:

- **Nextcloud Spreadsheet** (current): collaborative, self-hosted.
- **Google Sheets**: collaborative, cloud-hosted, API for automation.
- **VocBench Sheet2RDF**: imports CSV/spreadsheet data as RDF.  Could serve as
  a bridge between a spreadsheet "source" and an OWL "derived" representation.

**Dependency path:** Spreadsheet root limits expressiveness (Section 4.4) but
minimizes tooling dependencies.  If combined with an OWL generation step, adds
the same codegen needs as options (b/d) without the expressiveness benefit at
source level.

#### Paradigm comparison

| Paradigm | Expressiveness | Accessibility | Dependency Weight | Collaboration |
|----------|---------------|---------------|-------------------|---------------|
| Python-native | Good (custom abstractions) | Poor (requires Python) | Minimal | Git + PR only |
| File OWL + desktop editor | Excellent (OWL 2) | Medium (requires installation) | Low (editor is optional) | None (single-user) |
| Web OWL editor | Excellent (OWL 2) | Good (browser) | Medium-High (server infra) | Built-in |
| Spreadsheet | Poor (flat) | Excellent (browser, universal) | Minimal | Built-in |

### 5.2 Module: OWL/RDF Storage and Manipulation

**This module is needed regardless of root choice** — even if Python is the
root, OWL export for documentation, visualization, and potential linked data
publication requires RDF tooling.

#### Paradigm 1: File-based (no server)

The OWL file on disk is read directly by Python libraries.

| Solution | Version | What It Does | Python Integration | License |
|----------|---------|-------------|-------------------|---------|
| **rdflib** | 7.6.0 (Feb 2026) | Core Python RDF library: parse/serialize (Turtle, RDF/XML, JSON-LD, N-Triples), SPARQL query, in-memory graph | **Native** | BSD-3 |
| **Owlready2** | 0.50 (Feb 2026) | "Ontology-oriented programming": OWL classes as Python classes, automatic reasoning via HermiT/Pellet, optimized quadstore | **Native** | LGPL v3 |

**rdflib** is the essential baseline — every Python RDF workflow uses it.
**Owlready2** provides a higher-level API where `my_ontology.FormalFunction`
is a Python class.  However:

- Owlready2 is maintained by a single academic (Jean-Baptiste Lamy, Sorbonne
  Paris Nord).  Bus-factor risk.
- Owlready2's quadstore is SQLite-based and handles up to 1B triples, but
  for your ontology (~hundreds of triples), in-memory is sufficient.
- Owlready2's generated Python classes do NOT match the current `FancyStrEnum`
  pattern.  Using Owlready2 would mean either (a) adapting the library's
  idioms to Owlready2's style or (b) using Owlready2 only for OWL
  manipulation, not as the model itself.

**Dependency path:** If root = Python (a), rdflib suffices for OWL export.  If
root = OWL (b/d/e), Owlready2 is attractive for reading OWL and making it
accessible as Python objects, but its idioms differ from the existing codebase.

#### Paradigm 2: Triple Store (server-based SPARQL endpoint)

Needed if deploying VocBench in production mode or requiring SPARQL access from
multiple clients.

| Solution | Version | Reasoning | Python Integration | License | Risk |
|----------|---------|-----------|-------------------|---------|------|
| **Apache Jena Fuseki** | Active (ASF) | RDFS + basic OWL | SPARQLWrapper / rdflib SPARQLStore | Apache 2.0 | Very low (ASF-backed) |
| **GraphDB Free** | Active (Graphwise) | RDFS, OWL 2 RL, custom rules | rdflib 7.6 native integration | Free (limited); Enterprise paid | Medium (corporate ownership change: Ontotext → Graphwise) |
| **Oxigraph** | 0.5.6 (Mar 2026) | None (pure storage + SPARQL) | **pyoxigraph** (native Rust bindings) | MIT + Apache 2.0 | Low (Rust, modern codebase, permissive license) |
| ~~Blazegraph~~ | Archived (Mar 2026) | — | — | — | **Do not use (abandonware)** |
| ~~Stardog~~ | Active | Full OWL 2 DL (proprietary Pellet 3.0) | REST | **Commercial** | High (cost, proprietary reasoning) |

**Recommendation for this module:**

- If no triple store is needed: **rdflib** (file-based OWL).
- If VocBench is deployed: **Jena Fuseki** (mature, free, well-documented
  VocBench integration) or **GraphDB Free** (built-in reasoning, new rdflib
  integration).
- If lightweight SPARQL from Python is needed: **Oxigraph/pyoxigraph** (modern,
  fast, no Java).

#### Paradigm 3: Graph Database

| Solution | Notes |
|----------|-------|
| **Neo4j + neosemantics (n10s)** | Bridges property graph and RDF.  v5.26.0 (Sep 2025).  The RDF→property graph mapping is lossy for some OWL constructs.  Introduces Neo4j as a dependency without clear benefit over RDF-native tools for this project.  **Not recommended** unless the project has other Neo4j needs. |

### 5.3 Module: Ontology Reasoning

Reasoning checks whether the ontology is logically consistent and computes
inferred class memberships.  Relevant only if OWL is part of the architecture
(root options b/d/e, or as a derived artifact from a/c with reasoning run on
the output).

| Solution | OWL Profile | Language | Invocation from Python | License | Notes |
|----------|-------------|----------|----------------------|---------|-------|
| **HermiT** | Full OWL 2 DL | Java | Via Owlready2 `sync_reasoner()` | LGPL | Most complete open-source reasoner.  Bundled with Protégé.  Website TLS cert expired — project health concern, but reasoner itself is stable and mature. |
| **Pellet / Openllet** | Full OWL 2 DL | Java | Via Owlready2 | Pellet 2.x: AGPL.  Pellet 3.0: proprietary (Stardog only).  Openllet: AGPL. | Openllet last release 2019.  Use HermiT instead. |
| **ELK** | OWL 2 EL only | Java | Protégé plugin | Apache 2.0 | Very fast but only EL profile.  Your ontology likely needs constructs outside EL (universal restrictions, negation).  **Insufficient.** |
| **OWL-RL** | OWL 2 RL | Python | `import owlrl; owlrl.DeductiveClosure(g)` | W3C license | Pure Python, no Java.  Forward-chaining on rdflib graph.  Sufficient for RDFS + basic OWL inference.  Not full DL. |

**Recommendation:** Use **OWL-RL** for lightweight, Java-free reasoning in CI.
Use **HermiT via Owlready2** for full DL consistency checking when needed
(requires Java in CI image).

**Dependency path:** If root = Python (a), reasoning is optional — Python tests
can check model invariants directly.  If root = OWL (b/d/e), reasoning is a
valuable CI step but adds Java to the CI image.

### 5.4 Module: Validation (SHACL vs. Python Tests)

Two paradigms for enforcing constraints on the model's data:

#### SHACL (Shapes Constraint Language)

SHACL defines **shapes** (constraints) that RDF data must conform to.  Unlike
OWL (which uses the Open World Assumption and does not flag missing data),
SHACL uses a Closed World Assumption: if a required property is missing, it is
a validation error.

| Tool | Version | Notes |
|------|---------|-------|
| **pySHACL** | 0.30.1 (Jan 2026) | Pure Python.  Validates RDF against SHACL shapes.  CLI + library.  Active (RDFLib umbrella). |
| **GitHub Action** | `KonradHoeffner/shacl@v1` | Ready-made CI step for SHACL validation. |

**Example SHACL shape for your domain:**

```turtle
ex:FormalFunctionShape a sh:NodeShape ;
    sh:targetClass ex:FormalFunction ;
    sh:property [
        sh:path ex:isCharacterisedBy ;
        sh:minCount 1 ;
        sh:class ex:FormFunctionalAspect ;
    ] ;
    sh:property [
        sh:path rdfs:label ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
    ] .
```

**When SHACL is relevant:** If OWL is part of the architecture (root b/d/e),
SHACL is the standard tool for data quality validation.  If root = Python (a),
Python-native validation (type hints, `__post_init__`, pytest) serves the same
purpose without the RDF overhead.

#### Python-native Validation

| Tool | Version | Notes |
|------|---------|-------|
| **Pydantic** | v2.x (active) | Data validation + JSON Schema generation.  Would work for `.tla` file structure validation. |
| **mypy** | Active | Static type checking.  Already in dev dependencies. |
| **pytest** | Active | Already in dev dependencies.  Property-based testing with hypothesis is possible. |
| **dataclass `__post_init__`** | stdlib | Already used in `core.py`. |

**Recommendation:** Use **OWL + SHACL** for ontology-level constraints if OWL
is in the architecture.  Use **Pydantic** for `.tla` file structure validation
regardless of root choice (JSON validation is always needed).  Use **Python-
native validation** (mypy, pytest, `__post_init__`) for the Python model
regardless of root choice.

### 5.5 Module: Visualization and Graph Interaction

| Tool | Type | Editing? | Web/Desktop | Status | Notes |
|------|------|----------|-------------|--------|-------|
| **WebVOWL** | Read-only visualization | No | Web | Hosted at TIB (v1.1.6, 2019) | Beautiful VOWL notation.  Embeddable in docs.  Effectively unmaintained but usable. |
| **OWLGrEd** | Visualization + editing | **Yes** (UML-style) | Desktop + online demo | Active (v1.6.11) | Closest to "graph editing as primary interface" outside of Eddy.  Free. |
| **Eddy** | Visual graph editor | **Yes** (Graphol notation) | Desktop (Python/Qt) | Active (v3.8, Jan 2026) | True graph-editing primary interface.  OWL 2 export.  GPL v3.  Learning curve for Graphol notation. |
| **Chowlk + draw.io** | Diagram → OWL converter | **Yes** (via draw.io) | Web (draw.io) | Active | Draw ontology in diagrams.net using Chowlk library, convert to Turtle.  Most accessible visual tool.  Manual conversion step. |
| **D3.js / Cytoscape.js** | Custom visualization | Potentially | Web | Active | For custom interactive views in documentation.  Requires development effort. |
| Protégé OntoGraf | Read-only visualization | No | Desktop | Active (Protégé plugin) | Limited quality. |

**Dependency path:** If root = OWL, visualization tools work directly on the
source.  If root = Python, visualization requires first generating OWL.  For
documentation, WebVOWL is embeddable regardless.

**Recommendation:** **WebVOWL** for documentation embedding.  **OWLGrEd** or
**Eddy** if graph-based editing is desired.  **Chowlk + draw.io** as the most
accessible option for non-developers to visualize and sketch ontology changes.

### 5.6 Module: Documentation Generation

| Tool | Version | Input | Output | Quarto Integration | Notes |
|------|---------|-------|--------|-------------------|-------|
| **Ontospy** | 2.1.1 | OWL/RDF | HTML, **Markdown**, D3 charts | Best: Markdown output → `{{< include >}}` | Python-based.  SHACL support.  Jinja2 templates. |
| **pyLODE** | 3.4.2 (Apr 2023) | OWL/RDF | **HTML only** (3.x) | Embed HTML or use 2.x fork for Markdown | OntPub, VocPub, Supermodel profiles.  Maintenance concern (3 years since release). |
| **pyLODE.md** (fork) | Based on 2.13.3 | OWL/RDF | Markdown | Direct include in Quarto | Minimally maintained fork preserving Markdown output. |
| **Widoco** | Active | OWL | Full HTML site with WebVOWL, OOPS! | Standalone site; iframe or link from Quarto | Java-based.  Integrates visualization + pitfall scanning + changelog. |
| **Sphinx** (+ autodoc) | Active | Python | HTML, PDF | Separate build or Quarto import | Standard for Python docs.  Irrelevant if docs are Quarto-based. |

**Quarto integration strategy:**

Quarto supports combining auto-generated and manually curated content:

- **Pre-render scripts** (`_quarto.yml` → `pre-render: script.py`): run before
  Quarto render.  Generate `.qmd`/`.md` files that Quarto picks up.
- **`{{< include >}}`**: paste included file content inline.
- **Raw HTML includes**: for HTML fragments from pyLODE/WebVOWL.

**Recommended pipeline:**

1. Pre-render script runs Ontospy (or pyLODE.md) on the OWL representation
   (whether source or generated), producing Markdown reference fragments.
2. Manually curated `.qmd` pages include these fragments via `{{< include >}}`.
3. Vignettes have a standard template: auto-generated concept reference
   (from Ontospy) + manually written narrative sections.

**Dependency path:** Documentation generation requires OWL regardless of root.
If root = Python, OWL must be generated first.

### 5.7 Module: Grammar and Parser Infrastructure

| Tool | Version | EBNF Support | CI Generation | Notes |
|------|---------|-------------|---------------|-------|
| **DHParser** | 1.9.4 (Jan 2026) | Native (multiple EBNF dialects) | `python -m DHParser grammar.ebnf` → `.py` | Current choice.  Active (Bavarian Academy of Sciences).  Releases every 2–3 months. |
| **Lark** | 1.3.1 (Oct 2025) | Native (augmented EBNF: `.lark`) | Optional: `python -m lark.tools.standalone` | Largest community.  Earley + LALR(1).  Stronger alternative if migration needed. |
| **TatSu** | 5.13.0 (Jan 2025) | Native (Wirth, ISO EBNF) | `tatsu grammar.ebnf -o parser.py` | **Requires Python ≥ 3.14** (v5.13).  TatSu-LTS fork for broader compat.  Significant concern. |
| **ANTLR4** | 4.13.1 | Own `.g4` format (not EBNF) | Requires Java at build time | Grammar rewrite needed.  Python runtime is slow.  Massive grammar ecosystem. |

**Recommendation:** **Retain DHParser.**  It is actively maintained, already
integrated, and works.  Lark is the strongest fallback if DHParser is ever
abandoned.

**EBNF ↔ model synchronization:**

The EBNF's `SpecificFunction` and `FormalType` productions are essentially
enum listings that must match the vocabulary.  Three synchronization strategies:

1. **Generate EBNF from root:** If root = Python (a), extract enum members
   from `SpecificFunctionName`, `MainType`, etc. and generate the EBNF
   productions.  If root = OWL (b/d), extract from OWL annotations.
2. **Generate enums from EBNF:** Parse the EBNF, extract terminal lists,
   generate Python enums.  This makes EBNF the root for vocabulary terms (a
   sub-case of option (a)).
3. **Bidirectional check:** Both EBNF and enums exist independently; CI
   compares them and fails if they diverge.

Strategy 1 (generate EBNF from root) is cleanest — it establishes a single
source of truth.  Strategy 3 is viable as a transitional measure.

### 5.8 Module: Annotation Validation

The current `musicalform validate` CLI provides:

- Expression-level validation (parse a label string against the EBNF).
- CSV batch validation.
- TiLiA `.tla` file validation (extract labels from HIERARCHY_TIMELINEs,
  validate each).
- Directory-level recursive validation.

**Expansion needed:**

| Layer | What | Current State | Needed |
|-------|------|--------------|--------|
| Syntax | Parse label against EBNF | Implemented | Maintained via EBNF sync |
| Structure | Validate `.tla` JSON structure | Implicit (json.load + key access) | Formal schema (Pydantic models or JSON Schema) |
| Semantics | Validate label against model constraints | Not implemented | E.g., "a `presentation` can only appear inside a `sentence` or `hybrid`" |
| Cross-reference | Validate material references | Not implemented | E.g., "reference `[a]` must resolve to a named segment" |

**Note on TiLiA `.tla` format:** `.tla` files are JSON containing `timelines`
as the top-level key.  Timeline types include HIERARCHY_TIMELINE (the relevant
one), Beat, Harmony, Marker, etc.  No published JSON Schema exists.  A schema
should be reverse-engineered from TiLiA source (`TimeLineAnnotator/desktop`
on GitHub) and formalized as Pydantic models.

### 5.9 Module: CI/CD and Version Management

**Current CI:**

- GitHub Actions on push/PR to `development` (musicalform submodule only).
- Matrix: Python 3.11, 3.12.
- Runs tox (which runs pytest).
- release-please v3 (current: v4) for versioning.

**Needed CI enhancements (regardless of root choice):**

| Check | Purpose | Tooling |
|-------|---------|---------|
| EBNF ↔ model sync | Fail if EBNF and vocabulary diverge | Custom script (compare enum members vs. EBNF terminals) |
| Derived artifact sync | Fail if any generated file is stale | Custom script (regenerate, diff, fail if different) |
| Grammar auto-generation | Ensure parser matches EBNF source | `python -m DHParser grammar.ebnf`, compare output |

**Additional CI if OWL is in architecture:**

| Check | Purpose | Tooling |
|-------|---------|---------|
| OWL syntax validation | Ensure OWL file is parseable | `rdflib`: `Graph().parse('ontology.ttl')` |
| OWL consistency | Ensure no logical contradictions | OWL-RL or HermiT via Owlready2 |
| SHACL validation | Ensure data quality constraints met | pySHACL or `KonradHoeffner/shacl@v1` GitHub Action |
| OWL ↔ Python sync | Fail if generated Python doesn't match OWL | Custom script |

**OOPS! (OntOlogy Pitfall Scanner):** Web service at `oops.linkeddata.es`
detecting 41 common ontology modelling pitfalls.  REST API available.  Depends
on external server — useful for periodic audits but not reliable for CI
(network dependency).

**Version numbering (SemVer with domain-specific meaning):**

| Component | MAJOR | MINOR | PATCH |
|-----------|-------|-------|-------|
| Model version | Breaking change: removed/renamed concept, changed structural rules | New concept, new relation, expanded metafeature | Annotation/documentation fix, abbreviation alias addition |
| EBNF version | New syntactic constructs | New terminals (functions, types) | Whitespace/comment changes |
| Library version | Breaking API change | New feature | Bug fix |

All components should share a version number, enforced by CI.  The
release-please configuration should be updated to v4 and potentially extended
to cover the guidelines repo, not just the musicalform submodule.

---

## 6. Derivation Hierarchy and Change Propagation

The derivation hierarchy depends on the root choice (Section 4).  The following
table shows the derivation flow for each option:

### 6.1 Derivation Flows by Root Choice

**Option (a): Python as root**

```
Python source (enums.py, core.py, concept definitions)
  ├── → EBNF grammar (generated: enum members → production rules)
  │     └── → Parser script (DHParser auto-generation)
  ├── → OWL ontology (generated: class hierarchy → OWL axioms)
  │     ├── → Documentation reference (Ontospy/pyLODE)
  │     └── → Visualization (WebVOWL)
  └── → Documentation reference (Sphinx autodoc / Quarto pre-render)
```

**Option (b): OWL as root**

```
OWL file (Turtle, Git-versioned)
  ├── → Python enums (generated: annotated classes → FancyStrEnum members)
  ├── → Python dataclasses (generated: class restrictions → dataclass fields)
  │     └── → (Python model used by validation, CLI, etc.)
  ├── → EBNF grammar (generated: vocabulary classes → production rules)
  │     └── → Parser script (DHParser auto-generation)
  ├── → Documentation reference (Ontospy/pyLODE directly on source)
  └── → Visualization (WebVOWL directly on source)
```

**Option (c): Spreadsheet as root**

```
Spreadsheet / CSV
  ├── → Python enums (generated: rows → FancyStrEnum members)
  ├── → OWL ontology (generated: rows → OWL individuals/classes)
  │     ├── → Documentation reference
  │     └── → Visualization
  ├── → EBNF grammar (generated: term columns → production rules)
  │     └── → Parser script
  └── → Documentation reference (table rendering, existing Vocabulary.ipynb)
```

**Option (e): Hybrid**

```
Python top layer (ABCs, Protocols, structural rules)
  └── defines constraints for ↓

Vocabulary source (tool-dependent: CSV, OWL subset, or platform export)
  ├── → Python vocabulary code (generated, must satisfy top-layer constraints)
  ├── → EBNF grammar (generated)
  ├── → OWL ontology (generated or is the vocabulary source)
  └── → Documentation reference
```

### 6.2 Change Propagation Rules

Regardless of root choice, the following rules apply:

1. **Single source of truth:** Every piece of model information has exactly one
   authoritative location.  All other representations are derived.

2. **Derivation direction:** Changes flow from root to derived artifacts, never
   the reverse.  A change to a derived artifact that is not reflected in the
   root is either:
   - (a) A **manual curation** in a designated overlay location (e.g.,
     hand-written narrative in a vignette, which augments but does not override
     auto-generated content).
   - (b) A **bug** (the artifact is out of sync and must be regenerated).

3. **CI enforcement:** CI checks must **fail** when any derived component is
   out of sync with its source.  Implementation: the CI step regenerates all
   derived artifacts from the root source and diffs them against the committed
   versions.  Any diff is a failure.

4. **Overlay convention:** Files that contain both generated and manual content
   must clearly demarcate the two.  Options:
   - Separate files: `concept_ref_generated.md` (generated, never hand-edited)
     + `concept_ref.qmd` (manual, includes the generated file).
   - Markers: `<!-- BEGIN GENERATED -->` / `<!-- END GENERATED -->` blocks
     within a single file.
   The first option (separate files) is recommended for clarity.

---

## 7. Collaborative Workflow

The iterative modelling cycle, optimized for the daily work of changing
definitions and adding terms:

### 7.1 The Change Cycle

```
1. EDIT
   └─ Open the root source in its editor (IDE, ontology editor, spreadsheet)
   └─ Make the change (add term, edit definition, modify relation)

2. COMMIT
   └─ Save / export
   └─ Stage and commit to a feature branch
   └─ Push to GitHub

3. PROPAGATE (automated, triggered by push)
   └─ CI regenerates all derived artifacts from root
   └─ CI commits regenerated artifacts to the same branch (if changed)

4. VALIDATE (automated, part of CI)
   └─ Syntax: EBNF grammar consistency
   └─ Structure: derived artifacts match root
   └─ Semantics: model invariants (tests, SHACL if applicable)
   └─ Annotation: existing analyses re-validated against new model

5. REVIEW (human)
   └─ PR opened (automatically or manually)
   └─ Colleagues review the root change + propagated diffs
   └─ Discussion, revision if needed

6. MERGE → RELEASE (automated)
   └─ PR merged to main/development branch
   └─ release-please creates a version bump PR (or auto-releases)
   └─ Documentation site rebuilt and deployed
   └─ New version tagged
```

### 7.2 Human Review Stage

The review must cover:

- **Domain correctness:** Is the concept definition accurate?  Is the
  hierarchical placement correct?  Are relations meaningful?
- **Standard compliance:** Does the term follow naming conventions?  Are
  abbreviations unique and mnemonic?
- **Propagation correctness:** Do the generated artifacts look right?
  (Reviewers should not need to understand the generator, but should sanity-
  check the output.)
- **Test results:** CI must pass before merge.

For concept definitions specifically, the review should ideally be performed
by at least one musicologist and at least one person who understands the
model's formal structure.

### 7.3 Annotation Pilot Dialectic

The existing TiLiA analyses in the `annotation_pilot` repository play a
special role: they serve as a test corpus for the model.  The workflow is:

1. A model change is proposed (PR).
2. CI re-validates all `annotation_pilot` analyses against the proposed model.
3. If analyses break:
   - Either the model change is wrong (revert or revise the model).
   - Or the analyses need updating (file issues in `annotation_pilot`).
4. This dialectic between fitting the model to the analyses and updating the
   analyses to comply is the primary mechanism for model validation.

---

## 8. Documentation Architecture

### 8.1 Diataxis Structure

The existing Diataxis structure is maintained:

| Category | Content Type | Source |
|----------|-------------|--------|
| **Tutorial** | Learning-oriented guides | Manually curated wiki pages |
| **How-To** | Task-oriented recipes | Manually curated wiki pages |
| **Explanation** | Understanding-oriented discussions | Manually curated wiki pages + Brahms paper content |
| **Reference** | Information-oriented lookup | **Auto-generated** from model + manually curated vignettes |

### 8.2 Reference Material Pipeline

Reference material has two components:

1. **Auto-generated reference tables and concept descriptions:** Produced by
   running a documentation generator (Ontospy for Markdown output, or a custom
   pre-render script) on the model representation (OWL if available, or Python
   introspection).  This replaces the current `Vocabulary.ipynb` which reads
   from the (deprecated) CSV.

2. **Vignettes:** Full-fledged concept reference pages combining auto-generated
   and manually curated content.

### 8.3 Vignette Workflow

Each vignette follows a template:

```markdown
---
title: [Concept Name]
---

<!-- BEGIN GENERATED: do not edit below this line -->
## Reference

[Auto-generated: definition, abbreviations, hierarchical level,
 parent/child concepts, metafeatures, formal type associations,
 cross-references to related concepts]
<!-- END GENERATED -->

## Explanation

[Manually curated: theoretical context, historical provenance,
 relationship to scholarly sources]

## Examples

[Manually curated: annotated musical examples with TiLiA screenshots
 or score excerpts, demonstrating the concept in practice]

## Common Misidentifications

[Manually curated: how this concept is confused with related concepts,
 diagnostic criteria for disambiguation]
```

**Vignette creation workflow:**

1. A new concept is added to the model and merged.
2. The documentation pipeline generates a vignette stub with the auto-generated
   reference section filled in.
3. A musicologist claims the vignette (via GitHub issue) and writes the manual
   sections.
4. The vignette is reviewed and merged.
5. On subsequent model changes, the auto-generated section updates
   automatically; the manual sections are preserved.

### 8.4 Wiki Submodule

The wiki submodule (`wiki/`) enables browser-based editing via GitHub's wiki
interface.  Whether to keep it depends on the documentation pipeline:

- **If Quarto pre-render generates content from the model:** The wiki remains
  useful for manually curated pages (tutorials, how-tos, explanations).
  The submodule update step should be automated (a CI job or pre-commit hook
  that updates the submodule ref).
- **If all content moves into the main repo:** The wiki submodule can be
  removed.  Pages would be `.qmd` files in the main repo, editable via
  GitHub's web editor.

The recommended approach: **keep the wiki for manually curated content** (it
enables non-developer editing in the browser) and **generate reference content
in the main repo** (where CI can manage it).  Automate the submodule update.

---

## 9. Phased Migration Path

### Phase 0: Foundation (no root decision needed)

**Duration:** Can begin immediately.

- [ ] **G0: Terminology consolidation.** Circulate Section 2 to all team
  members.  Reach agreement on metaconcept/concept/metafeature/feature
  definitions.
- [ ] **G1: Current state audit.** ← This document.
- [ ] **G2: Existing analysis baseline.** Run `musicalform validate -d` on
  all `annotation_pilot` analyses.  Record pass/fail rates.  This is the
  baseline against which model changes will be measured.
- [ ] **Root decision test (Section 4.9):** Write 5 representative concept
  definitions in Python and OWL.  Show to musicologists.  Decide.

### Phase 1: Root Decision

**Duration:** 1 meeting after the test in Phase 0.

- [ ] **G3: Root paradigm decision.** Choose (a), (b), or (e).
  Document the decision and rationale.

### Phase 2: Infrastructure

**Duration:** Depends on root choice.

**If root = (a) Python:**
- [ ] **G4:** Design the concept definition framework in Python (Protocols for
  metaconcepts, dataclasses for concepts, metafeature specifications).
- [ ] **G5:** Write EBNF generation script (Python enums → EBNF productions).
- [ ] **G5:** Write OWL generation script (Python classes → OWL axioms), if
  OWL export is desired.
- [ ] **G6:** Add CI steps: EBNF sync check, derived artifact sync check.
- [ ] **G7:** Establish contribution guide for non-developers (template files,
  review process).

**If root = (b) OWL:**
- [ ] **G4:** Design the OWL ontology with proper namespace (e.g.,
  `https://musicalform.github.io/ontology/`).  Migrate informational content
  from the deprecated OWL.  Choose Turtle serialization with stable output
  ordering.
- [ ] **G5:** Build OWL → Python generator (OWL classes → FancyStrEnum members
  + dataclass fields).  Build OWL → EBNF generator.
- [ ] **G6:** Add CI steps: OWL syntax, OWL consistency (reasoner), SHACL,
  generated artifact sync.
- [ ] **G7:** Deploy VocBench (Docker) or configure WebProtégé for
  collaborative editing.  Set up export → Git automation.

**If root = (e) Hybrid:**
- [ ] **G4:** Define the boundary between Python top layer and vocabulary
  layer.  Design the Python structural framework.  Choose the vocabulary tool.
- [ ] **G5:** Write vocabulary → Python generation script.  Write vocabulary →
  EBNF generation script.  Write sync-check between top layer and vocabulary.
- [ ] **G6:** Add CI steps for both layers.
- [ ] **G7:** Set up vocabulary tool (spreadsheet, VocBench, or other).

### Phase 3: Integration

- [ ] **G8:** EBNF ↔ model synchronization (using the strategy from
  Section 5.7).
- [ ] **G9:** Restructure `musicalform` library: separate domain model from
  parser output consumption.  The `from_parse()` methods should be adapters,
  not part of the core model.
- [ ] **G10:** Expand annotation validation (semantic validation, cross-
  reference checking).
- [ ] **G11:** Define validation shapes (SHACL if OWL is present; Python tests
  otherwise).

### Phase 4: Workflow

- [ ] **G12:** Full change cycle operational (Section 7.1) for at least 10
  test concepts.
- [ ] **G13:** Documentation pipeline: Quarto pre-render + auto-generated
  reference + manual vignette template.
- [ ] **G14:** Version alignment: shared SemVer across all components,
  release-please v4 configuration.

### Phase 5: Content

- [ ] **G15:** Begin concept definition work at scale.
- [ ] **G16:** Begin vignette writing (prioritized by annotator need).
- [ ] **G17:** Re-validate `annotation_pilot` analyses against the evolving
  model.  Track convergence.

---

## 10. Open Questions

These questions genuinely require further human input about the domain model
and cannot be resolved by architectural analysis alone.

**Q1. Complexity of concept definitions.**
How complex will the daily concept definition work be?  (See Section 4.9.)
This determines the root choice.

**Q2. Relations between concepts.**
What types of relations exist between concepts beyond parent-child hierarchy?
Examples: "is prerequisite for," "is variant of," "is transformation of,"
"is incompatible with."  These must be enumerated to design the model schema.

**Q3. CIDOC CRM / IFLA LRM integration.**
To what extent should the formal model integrate with CIDOC CRM (for cultural
heritage objects) and IFLA LRM (for bibliographic entities)?  The Brahms paper
lays groundwork for this.  Integration would favor OWL as root or as a
first-class derived artifact.

**Q4. Congruence scoring mechanism.**
How are congruence scores computed when a concept is resolved against a musical
object?  Is this a weighted sum of metafeature scores?  A probabilistic model?
A rule-based system?  The answer affects whether the model needs numeric
parameters (suggesting Python/code) or declarative constraints (suggesting
OWL/SHACL).

**Q5. Style-specific concept conditioning.**
The metaconcept→concept conditioning continuum implies that the same metaconcept
(e.g., "Cadence") may be conditioned differently for different styles
(Viennese Classic, Romantic, Pop/Rock).  How should style-specific conditioning
be organized?  As separate class hierarchies?  As parametric variations?

**Q6. Cadence vocabulary integration.**
The CSV contains cadence-related terms (PAC, IAC, HC, EC, DC, PC) that are
not in the EBNF grammar or Python enums.  Should these be integrated into the
annotation standard?  If so, at what level?  (Currently, cadences are implicit
in the harmonic analysis layer, not the form annotation layer.)

**Q7. Pop/rock and non-classical vocabulary.**
The CSV contains terms from pop/rock analysis (`chorus`, `verse`, `bridge`,
`pre-chorus`, `post-chorus`) and historical German terminology (`Hauptperiode`,
`Satz`, `Schlusssatz`).  What is the integration plan?  Separate namespace?
Extended grammar?

**Q8. Multi-annotator agreement.**
When multiple annotators analyse the same piece, how are disagreements
represented and resolved?  This affects the annotation validation pipeline
design (e.g., whether to track annotator IDs, confidence levels, inter-rater
metrics).

---

## 11. Appendices

### Appendix A: Interface Contracts *[CONCEPTUAL DRAFT]*

These contracts define the interfaces between components.  They are subject
to change based on the root decision.

**VocabularyRegistry (concept carried forward from v0.1 draft):**

A central registry that provides:

- Lookup: term name or abbreviation → canonical concept.
- Enumeration: all concepts at a given hierarchical level.
- Validation: is a given label component valid?
- Metadata: definition, abbreviations, relations, metafeatures.

The registry's implementation depends on the root:

- If root = Python: the registry IS the Python module (enums + class
  hierarchy, queryable via introspection).
- If root = OWL: the registry wraps an rdflib/Owlready2 graph with a
  Python-friendly API.
- If root = Spreadsheet: the registry wraps a DataFrame or dict loaded from
  CSV.

**EBNF ↔ Vocabulary interface:**

The EBNF grammar must contain production rules listing exactly the vocabulary
terms recognized by the parser.  The interface is a generated section of the
EBNF file:

```ebnf
/* AUTO-GENERATED from [root source]. Do not edit manually. */
SpecificFunction ::= 'antecedent' | 'ant'
                   | 'basic idea' | 'bi'
                   | ...
```

The generation script reads the root source and emits these productions.

**OWL export interface (if applicable):**

The OWL file must use:

- A project-owned namespace (e.g., `https://musicalform.github.io/ontology/`).
- `rdfs:label` for human-readable names.
- A custom annotation property (e.g., `mf:abbreviation`) for abbreviation
  aliases.
- `rdfs:comment` for short definitions.
- `rdfs:seeAlso` for vignette links.
- `owl:versionInfo` for version string.
- `owl:versionIRI` for version-specific namespace.

### Appendix B: File Mapping *[CONCEPTUAL DRAFT]*

This mapping shows the current and proposed locations of each component.
Proposed locations are subject to change based on the root decision.

| Component | Current Location | Status | Proposed Location |
|-----------|-----------------|--------|-------------------|
| Quarto site config | `_quarto.yml` | Active | Unchanged |
| Wiki content (tutorials, how-tos) | `wiki/` (submodule) | Active | Unchanged (automate submodule update) |
| Vignettes | `wiki/vignettes/` | 2 of ~60+ | Unchanged; add auto-generated stubs |
| Syntax reference | `wiki/Syntax.md` | Active | Unchanged |
| Vocabulary table | `Vocabulary.ipynb` | Active (reads CSV) | Replace with Quarto pre-render from model |
| Vocab spreadsheet CSV | `data/Form vocabulary.csv` | Deprecated as root; informational | Archive; replace with model-generated reference |
| EBNF grammar | `grammar/lcma_standard.ebnf` | Active (v0.1) | Unchanged (or generated from root) |
| EBNF parser (generated) | `grammar/lcma_standardParser.py` | Generated | Unchanged |
| EBNF parser (CLI copy) | `musicalform/src/musicalform/cli/lcma_standardParser.py` | Copy of above | Eliminate duplication; single source |
| Python enums | `musicalform/src/musicalform/enums.py` | Active (v0.1.0) | Root source (a) or generated (b/d/e) |
| Python domain model | `musicalform/src/musicalform/core.py` | Active (v0.1.0) | Restructure: separate model from parser adapters |
| Python CLI | `musicalform/src/musicalform/cli/` | Active | Expand validation capabilities |
| OWL ontology (deprecated) | `ontology/protege/form_ontology.owl` | Deprecated | Archive; new ontology in `ontology/` if root=(b) |
| Brahms paper | `ontology/model_of_music_analysis/` | Reference | Unchanged |
| CI: tests | `musicalform/.github/workflows/ci.yml` | Active | Add sync checks, expand to guidelines repo |
| CI: release | `musicalform/.github/workflows/release-please.yml` | Active (v3) | Update to v4; extend to cover guidelines repo |
| Git submodules | `.gitmodules` | Active | Unchanged |

### Appendix C: Tooling Dependency Ledger

Every 3rd-party tool adopted produces technological debt.  This ledger makes
that debt visible.

| Tool | Role | Maintainer | License | Last Release | Risk Level | Mitigation |
|------|------|-----------|---------|-------------|-----------|-----------|
| DHParser | EBNF parsing | Bavarian Academy of Sciences | Apache 2.0 | Jan 2026 | Low | Lark as fallback |
| rdflib | RDF manipulation | RDFLib community | BSD-3 | Feb 2026 | Very Low | De facto standard |
| Owlready2 | OWL-as-Python | J-B Lamy (Sorbonne) | LGPL v3 | Feb 2026 | Medium | Single maintainer; rdflib as fallback (lower-level) |
| pySHACL | SHACL validation | RDFLib community | BSD-3 | Jan 2026 | Low | Community-maintained |
| OWL-RL | Python reasoning | RDFLib community | W3C | Jul 2025 | Low | Community-maintained |
| Ontospy | Doc generation | lambdamusic | MIT | Active | Medium | Small project; pyLODE as alternative |
| Quarto | Documentation | Posit (RStudio) | GPL v2 | Active | Very Low | Major corporate backing |
| VocBench | Ontology editing | U. Rome Tor Vergata + EU | Open source | Active | Medium | EU-funded but single research group; OWL files portable |
| Jena Fuseki | Triple store | Apache SF | Apache 2.0 | Active | Very Low | ASF-backed |
| release-please | Versioning | Google | Apache 2.0 | Active | Low | Google-maintained |
| pandas | Data manipulation | NumFOCUS | BSD-3 | Active | Very Low | Ubiquitous |
