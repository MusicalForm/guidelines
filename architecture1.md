# LCMA Architecture Document

> **Status**: Working draft, v0.2.0-dev
> **Date**: 2026-03-31
> **Scope**: Architecture for the form model, its representations,
> tooling, and collaborative workflow.

---

## Table of Contents

1. [Current State Inventory](#1-current-state-inventory)
2. [Terminology](#2-terminology)
3. [Goal Dependency Graph](#3-goal-dependency-graph)
4. [Project Root: Analysis and Recommendation](#4-project-root-analysis-and-recommendation)
5. [Vocabulary Management Platform](#5-vocabulary-management-platform)
6. [Tooling: Module-by-Module Analysis](#6-tooling-module-by-module-analysis)
7. [Derivation Hierarchy and Change Propagation](#7-derivation-hierarchy-and-change-propagation)
8. [Collaborative Workflow](#8-collaborative-workflow)
9. [Documentation Architecture](#9-documentation-architecture)
10. [Phased Migration Path](#10-phased-migration-path)
11. [Open Questions](#11-open-questions)
12. [Appendices](#appendices)

---

## 1. Current State Inventory

### 1.1 The Guidelines Repository

The guidelines repo (`MusicalForm/guidelines`) is the central workspace for the
LCMA model. It renders a Quarto website (`_quarto.yml`, output to `docs/`)
hosted at `https://musicalform.github.io/guidelines/`. The site follows the
[Diataxis](https://diataxis.fr/) documentation philosophy with four quadrants:

| Quadrant     | Content                       | Source location                      |
|--------------|-------------------------------|--------------------------------------|
| Tutorial     | Quickstart, Intro, Principles | `wiki/tutorials/`, `wiki/`           |
| How-To       | Workflow                      | `wiki/Workflow.md`                   |
| Explanations | Examples                      | `wiki/Examples.md`                   |
| Reference    | Syntax, Vocabulary table      | `wiki/Syntax.md`, `Vocabulary.ipynb` |

The wiki is included as a git submodule (`wiki/` -> `MusicalForm/guidelines.wiki`).
Browser-based editing of the wiki is possible; updating the rendered homepage
requires updating the submodule pointer and rebuilding Quarto.

### 1.2 The Annotation Standard and EBNF Grammar

The annotation standard defines a label syntax for form analysis in TiLiA (a
timeline annotator). The syntax is documented in `wiki/Syntax.md` and encoded
formally in `grammar/lcma_standard.ebnf` (115 lines). DHParser auto-generates
a parser script (`grammar/lcma_standardParser.py`) from this EBNF, and a copy
lives in the Python library at `musicalform/src/musicalform/cli/lcma_standardParser.py`.

The EBNF defines:

- **Labels**: optional name, one or more `FormLabel` or `PlaceholderLabel` segments
- **FormLabel**: function expression + optional type expression + optional certainty + optional material brackets
- **Function vocabulary**: 30 `SpecificFunction` entries and 15 `Unit` entries
- **Type vocabulary**: 14 `FormalType` entries (some with subtypes)
- **Material operations**: operators for repetition, transposition, ornamentation, etc.

### 1.3 The Vocabulary Spreadsheet

A Nextcloud-hosted spreadsheet (CSV export at `data/Form vocabulary.csv`, 103
rows) contains term definitions including labels, abbreviations, hierarchical
level, function/type classification, relations, short explanations, and
theoretical provenance. Rows 62-103 contain terms that are either
cadence-related or not yet integrated into the formal vocabulary (many with
empty fields). Large parts are deprecated.

`Vocabulary.ipynb` reads this CSV and renders a filtered reference table for
the Quarto site, linking terms to Open Music Theory pages and vignettes.

### 1.4 The `musicalform` Python Library

Included as a git submodule (`musicalform/` -> `MusicalForm/musicalform`),
version 0.1.0. Key components:

| File                         | Contents                                                                                                                                                                                                                                                                         |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enums.py`                   | `FancyStrEnum` base class; `SpecificFunctionName` (30 members + aliases), `UnitName` (15), `MainType` (18 + aliases), `SubType` (2), `MaterialOperator` (15 + symbol aliases), `PlaceholderName`, `CertaintyName`                                                                |
| `core.py`                    | Domain model: `AnnotationLabel`, `FormLabel`, `PlaceholderLabel`, `FormalFunction` (ABC), `SingleFunction`, `SpecificFunction`, `GenericFunction`, `FunctionalTransformation`, `FormalType`, `References`, `SingleReference`, `MaterialReferences`, `TransformationalReferences` |
| `utils.py`                   | `compact_repr` decorator, parse-tree helpers                                                                                                                                                                                                                                     |
| `cli/validate.py`            | Validation CLI: expression, file, CSV, and TiLiA JSON modes                                                                                                                                                                                                                      |
| `cli/main.py`                | CLI entry point with `validate` subcommand                                                                                                                                                                                                                                       |
| `cli/lcma_standardParser.py` | DHParser-generated parser (copy from `grammar/`)                                                                                                                                                                                                                                 |

Build system: `uv_build`, `pyproject.toml`. Dependencies: DHParser >= 1.8.3,
pandas >= 2.0. Dev tools: pytest, tox, pre-commit, black, isort, flake8, mypy.

CI: GitHub Actions (`ci.yml`) runs tox on Python 3.11 and 3.12. Release
management via `release-please.yml` on the `development` branch.

### 1.5 The OWL Ontology (deprecated)

`ontology/protege/form_ontology.owl` (428 lines, September 2024) was created
in WebProtege. It defines the meta-level structure:

| OWL Class                 | Label                  |
|---------------------------|------------------------|
| `Rlqidt0dt2pEZVIfEhmBeR`  | Formal Function        |
| `R53kZLGWA8NQB483qUSyaQ`  | Form-functional Aspect |
| `RNZUc4Eis88akAPwITfLx6`  | Formal Type            |
| `RoBc2KO68r05ZBPZyf9zPI`  | Feature                |
| `R88OoE1s5MJif7rlX2tTyaF` | Timespan               |
| `RDyg4CmamyII9JlsnOf7IJC` | Timeline               |
| `RDV5Uxq0I7jjzcfUr9T0EkP` | Musical Expression     |
| `RQvENM7B4TkChxhO6Dw6I6`  | Musical Domain         |

Properties include: `characterises`/`is characterised by`, `qualifies`/
`is qualified by`, `operationalises`/`is operationalised by`, `informs`/
`is informed by`, `realises`/`is realised as`, `embeds`/`is embedded in`,
`elapses over`, `is context of`.

**Status**: This OWL file is fully deprecated. It will be used only as
informational input for the meta-level design. A new OWL ontology will be
generated from scratch with human-readable URIs (see
[Section 4](#4-project-root-analysis-and-recommendation)).

### 1.6 The Analysis Model Paper

`ontology/model_of_music_analysis/Brahms_Form_New_text.html` is a paper
modelling music analysis as "Claim Production by Agents," drawing on IFLA LRM
and CIDOC CRM. It provides the conceptual foundation for the meta-level
ontology. IFLA LRM terms (Work, Expression, Manifestation, Item) and their
most relevant subclasses will be included in the generated OWL ontology.

### 1.7 Vignettes

Two vignettes exist in `wiki/vignettes/`:

- `vignette-thematic-intro.md` -- Curtain & Thematic Introduction
- `vignette-sequence.md` -- Sequence (note: filename uses a Unicode hyphen)

Approximately 60+ vignettes are needed to cover the full vocabulary.

### 1.8 Gaps and Inconsistencies

| # | Gap                                                                                                            | Impact                                                                                       |
|---|----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| 1 | No single source of truth: spreadsheet, EBNF, and Python enums contain overlapping but non-identical term sets | Any change requires manual synchronization across three locations                            |
| 2 | No concept definitions: neither Python classes nor OWL encode which features define a concept                  | Concepts are labels without semantics beyond their name                                      |
| 3 | No hierarchical relations between concepts in Python                                                           | The `contains` column in the CSV is not programmatically accessible                          |
| 4 | No version alignment across components                                                                         | EBNF, Python, CSV, and OWL may diverge silently                                              |
| 5 | No automated change propagation                                                                                | Adding a term requires editing EBNF + Python enums + CSV manually                            |
| 6 | Only 2 of ~60+ vignettes exist                                                                                 | Reference documentation is skeletal                                                          |
| 7 | Minimal test coverage                                                                                          | No property-based tests, no cross-source consistency tests                                   |
| 8 | Parser script exists as a copy in two locations                                                                | `grammar/lcma_standardParser.py` vs `musicalform/src/musicalform/cli/lcma_standardParser.py` |

---

## 2. Terminology

The following terms are used precisely throughout this document. The word
"metaclass" is avoided to prevent confusion with Python's `metaclass`.

**Metaconcept** (e.g., "Caesura"):
An abstract class stipulating the overarching meaning and use of a class of
concepts, potentially across musical styles. Defines the upper,
style-independent layers of the ontology. Includes the set of
metaconcepts/concepts/metafeatures needed to obtain a concrete, parametrized
concept. There is a continuum where child metaconcepts become more concrete by
swapping abstract components with concrete ones ("conditioning" /
"predicating"). The child that replaces the very last unconditioned component
constitutes the "quantum leap" from metaconcept to concept. In Python,
metaconcepts may be implemented as runtime-checkable `Protocol`s. Fundamental
modelling decisions at this level require extreme care and may require testing
multiple solutions.

**Concept** (e.g., "Half Cadence in the Viennese classic"):
A fully conditioned, parametrized subclass of a metaconcept. When resolved
against a musical object, yields a congruence score. An atomic concept can
become a small class hierarchy of metafeatures (probability distribution,
score-based ranking, single imperative value, logic-based values, etc.). A
non-atomic concept defines acceptable congruence score ranges for its resolved
metafeatures. A concept defines which types of musical objects it can be
applied to (it may serve as a type guard in the Python sense).

**Metafeature** (e.g., "dominant harmony"):
The combination of a concept with some value range. A component within a
concept definition that specifies not a single value but a range, distribution,
or ranked set of acceptable values for a given feature.

**Feature** (e.g., "dominant harmony with Roman numeral V, indicating a root
position triad"):
The outcome of resolving a metafeature against a musical object. The
combination of a concept with a specific value. Exposes nested structure
corresponding to the resolved definition components (because concepts are
recursively defined, resolving a feature may yield sub-features).

---

## 3. Goal Dependency Graph

Goals are structured as a directed acyclic graph (DAG). An arrow `A -> B`
means "A must be completed before B can begin."

```
G1: Consolidate term inventory
 |
 v
G2: Design canonical YAML schema
 |
 +---> G3a: YAML -> Python enum/class generator
 |      |
 |      +---> G5: VocabularyRegistry in Python
 |      |
 |      +---> G8: Property-based tests & cross-source consistency tests
 |
 +---> G3b: YAML -> EBNF generator (or EBNF -> YAML back-import)
 |      |
 |      +---> G8
 |
 +---> G3c: YAML -> OWL generator (with IFLA LRM terms)
 |      |
 |      +---> G9: OWL export/import bridge
 |      |
 |      +---> G8
 |
 +---> G4: CI sync checks (all derived artifacts must match YAML)
 |      |
 |      +---> G8
 |
 v
G5: VocabularyRegistry (runtime concept lookup, abbreviation resolution)
 |
 v
G6: Annotation validation pipeline expansion
 |   (validate TiLiA JSON files against the model; batch annotation_pilot)
 |
 v
G7: Vignette pipeline (auto-generated stub from YAML + manual curation)
 |
 v
G10: Documentation rebuild (Quarto + generated reference + curated content)
 |
 v
G11: Iterative consolidation cycle
     (validate annotation_pilot analyses <-> model; update both)

--- Parallel track (independent of G3-G6) ---

G12: Vocabulary management GUI evaluation and deployment
     (depends on G2: schema must be stable before tooling is chosen)

G13: Human review workflow integration
     (depends on G4: CI checks must exist before review is meaningful)
```

### Goal Descriptions

| Goal    | Description                                                                                                                                                                                                                                                                                                                                                           |
|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **G1**  | Audit the spreadsheet, EBNF, and Python enums.  Produce a reconciled term list with canonical names, abbreviations, hierarchical levels, function/type classification, and containment relations.  Identify terms that exist in one source but not others.                                                                                                            |
| **G2**  | Define the YAML schema for concept definitions.  Each concept file (or entry in a multi-concept file) specifies: canonical name, abbreviations, metaconcept membership, metafeature definitions with value ranges, hierarchical level, containment relations, theoretical provenance, and vignette link.  The schema itself is defined in JSON Schema for validation. |
| **G3a** | Write a generator that reads YAML and produces Python `FancyStrEnum` members and (later) domain dataclass definitions.  Must produce identical output to the current hand-written enums as a migration constraint.                                                                                                                                                    |
| **G3b** | Write a generator that reads YAML and produces the EBNF grammar (or: define a back-importer that seeds YAML from the existing EBNF).  The EBNF remains the input to DHParser for parser generation.                                                                                                                                                                   |
| **G3c** | Write a generator that reads YAML and produces OWL/RDF with human-readable URIs under a project namespace.  Include IFLA LRM classes (Work, Expression, Manifestation, Item) and their relevant subclasses as upper-ontology imports.                                                                                                                                 |
| **G4**  | CI checks that fail when any derived artifact (Python enums, EBNF, OWL) is out of sync with the YAML source.  Implemented as a `make check-sync` target or equivalent.                                                                                                                                                                                                |
| **G5**  | A `VocabularyRegistry` class that loads the generated vocabulary at runtime, supports lookup by canonical name or abbreviation, and provides iteration/filtering by hierarchical level, function/type, etc.  Population mechanism depends on the YAML -> Python generator output.                                                                                     |
| **G6**  | Expand the annotation validation pipeline to validate TiLiA JSON files against the full model (not just grammar parsing).  Batch-validate the annotation_pilot repository.                                                                                                                                                                                            |
| **G7**  | For each concept in the YAML, auto-generate a vignette stub (with fields for definition, musical examples, related concepts, etc.).  Manually curated content is written into a designated section that is preserved across regeneration.                                                                                                                             |
| **G8**  | Property-based tests (Hypothesis) for grammar parsing, cross-source consistency tests (YAML == Python enums == EBNF terms == OWL individuals), and roundtrip tests for the generators.                                                                                                                                                                                |
| **G9**  | An OWL export/import bridge: export the current model state as OWL for use in external tools (VocBench, Protege); import OWL modifications back into YAML (with conflict detection).                                                                                                                                                                                  |
| **G10** | Rebuild the Quarto documentation pipeline.  Reference material is auto-generated from YAML/Python.  Curated content (tutorials, how-tos, explanations, vignette narratives) coexists via designated directories.                                                                                                                                                      |
| **G11** | The ongoing dialectic: validate annotation_pilot analyses against the model, update analyses to comply, update the model where analyses reveal gaps.                                                                                                                                                                                                                  |
| **G12** | Evaluate and deploy a vocabulary management GUI for musicologists (see [Section 5](#5-vocabulary-management-platform)).                                                                                                                                                                                                                                               |
| **G13** | Integrate the human review stage: PR-based review with CI checks, preview of generated documentation, diff of OWL changes.                                                                                                                                                                                                                                            |

---

## 4. Project Root: Analysis and Recommendation

### 4.1 Options Evaluated

| Option                                             | Root paradigm                                  | Daily workflow                         | Accessibility                                     | Robustness                                         | Expressiveness |
|----------------------------------------------------|------------------------------------------------|----------------------------------------|---------------------------------------------------|----------------------------------------------------|----------------|
| **(a)** Python hierarchy                           | Edit Python IDE                                | Low for non-devs                       | High (no external deps)                           | High (full Python expressiveness)                  |
| **(b)** OWL file via ontology editor               | Edit OWL, generate Python                      | Medium (GUI-based)                     | Low (OWL editor dependency, generation fragility) | High (OWL DL)                                      |
| **(c)** Spreadsheet/tabular tool                   | Edit spreadsheet, generate Python+OWL          | High (familiar to musicologists)       | Low (cloud dependency, merge conflicts)           | Low (flat structure, no recursion)                 |
| **(d)** Dedicated vocabulary platform              | Edit via platform GUI, generate all            | Medium-High (purpose-built)            | Low (vendor lock-in, cost)                        | Medium (platform-constrained)                      |
| **(e)** Hybrid: Python top-level + YAML vocabulary | Edit YAML for vocabulary, Python for structure | High (YAML is readable, PR-reviewable) | High (plain text, git-native)                     | High (YAML supports nesting; Python handles logic) |

### 4.2 Evaluation

**Option (a): Python as sole root.**
Editing Python enums and dataclasses requires IDE familiarity. Adding a term
means editing `enums.py` (enum member + alias), potentially `core.py`
(dataclass fields), and `lcma_standard.ebnf` (grammar rule). This is
error-prone and inaccessible to musicologists. However, the Python code is
the most expressive representation and the one that must ultimately be correct.

**Option (b): OWL as sole root.**
Requires maintaining the ontology in an OWL editor and generating Python from
it. The generation step is fragile: OWL's open-world semantics do not map
cleanly to Python's closed-world type system. OWL editors (Protege,
VocBench) have steep learning curves. OWL does not natively express the
procedural aspects of the model (parsing rules, congruence scoring).

**Option (c): Spreadsheet as sole root.**
The current spreadsheet already demonstrates the problems: flat structure
cannot represent recursive concept definitions, merge conflicts in CSV are
unreadable, no validation, no type checking. Cloud dependency (Nextcloud)
adds a failure point.

**Option (d): Dedicated platform as sole root.**
TopBraid EDG and PoolParty are enterprise products (5-6 figure annual
licensing). VocBench is free but requires server deployment and does not
support the full expressiveness needed (YAML-level nesting, custom
metafeature schemas). All platforms risk vendor lock-in and produce heavy
technological debt.

**Option (e): Hybrid with YAML control files.**
The abstract metaconcept hierarchy (structural rules, class architecture) is
maintained in Python, which is expected to stabilize within weeks. The
vocabulary -- individual concept definitions and relations, which constitute
the bulk of daily work -- is maintained in YAML files within the git repo.
Code generators produce Python enums/classes, EBNF grammar rules, and OWL
from the YAML.

### 4.3 Recommendation: Option (e) -- Hybrid with YAML Control Files

**Rationale**:

1. **Optimal for the daily workflow.**  Adding a term means editing a YAML file
   (human-readable, diff-friendly), creating a PR (standard GitHub workflow),
   which triggers CI to regenerate all derived artifacts and run consistency
   tests. Merge = new release. This will happen thousands of times; the
   overhead per change is minimal.

2. **Accessible to musicologists.**  YAML is readable without programming
   knowledge. A concept definition in YAML looks like:

   ```yaml
   # Example concept definition (illustrative; schema is a conceptual draft)
   antecedent:
     abbreviations: [ant]
     type: function
     hierarchical_level: phrase
     contains: [basic_idea, contrasting_idea]
     provenance: Caplin1998
     vignette: wiki/vignettes/vignette-antecedent.md
     explanation: >
       2-bar bi, 2-bar ci, ending with HC or IAC.
   ```

3. **Robust against dependency risks.**  The source of truth is plain text in
   git. No external platform is required for the core workflow. External
   tools (VocBench, visualization tools) consume generated OWL as read-only
   views.

4. **Expressive.**  YAML supports the nested structures needed for recursive
   concept definitions. The YAML schema is validated by JSON Schema, catching
   errors before generation. Python handles the procedural logic (parsing,
   validation, congruence scoring) that YAML cannot express.

5. **Version-controlled.**  Every change to the vocabulary is a git commit with
   full history, blame, and diff support. PR-based review is native.

**Trade-off acknowledged**: YAML is not a GUI. Musicologists who find YAML
intimidating can use a vocabulary management GUI (see
[Section 5](#5-vocabulary-management-platform)) that reads/writes the YAML files.
The GUI is an optional convenience layer, not the source of truth.

---

## 5. Vocabulary Management Platform

### 5.1 Requirements

The vocabulary management platform serves as an optional GUI layer over the
YAML control files. It must support:

- Browsing and searching the vocabulary (terms, hierarchies, relations)
- Editing concept definitions (with validation)
- Visualizing the ontology as an interactive graph
- Exporting to OWL/RDF for interoperability
- Collaborative use by multiple musicologists
- Integration with the git-based workflow (reading from / writing to YAML)

### 5.2 Candidates Evaluated

#### 5.2.1 Dedicated Ontology Management Software

| Tool                     | OWL/RDF Support                          | Collaboration                            | Version Control                       | Visualization                        | License                       | Risk Assessment                                                                                                                                                                       |
|--------------------------|------------------------------------------|------------------------------------------|---------------------------------------|--------------------------------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Protege Desktop**      | Full OWL 2                               | None (single-user)                       | None native                           | Minimal (OntoGraf plugin, stale)     | Free, open-source             | Low cost, high learning curve, no collaboration, stale plugins. Adequate for individual expert use; inadequate as a team platform.                                                    |
| **WebProtege**           | OWL 2 subset                             | Web-based, multi-user                    | Change history (not git)              | Limited                              | Free, open-source             | The existing OWL was created here.  Limited expressiveness (no SWRL, limited annotation properties).  Stanford-hosted instance is unreliable.  Self-hosting requires Java stack.      |
| **VocBench 3**           | Full OWL, SKOS, SKOS-XL, OntoLex, RDF    | Web-based, multi-user, role-based access | Change tracking, validation workflows | Tree views, SPARQL-based exploration | Free, open-source (EU-funded) | **Best-in-class for free OWL management.**  Backed by Semantic Turkey.  Supports import/export in all standard formats.  Active development.  Requires Java/Tomcat server deployment. |
| **TopBraid EDG**         | Full OWL, SHACL, SKOS                    | Enterprise multi-user                    | Full audit trail, workflows           | Graph views, forms, dashboards       | Commercial (5-6 figure/year)  | Powerful but prohibitively expensive for an academic project.  Vendor lock-in risk.                                                                                                   |
| **PoolParty**            | SKOS-focused, OWL support via extensions | Enterprise multi-user                    | Change tracking, workflows            | Graph views, thesaurus views         | Commercial (5-6 figure/year)  | Merged with Ontotext (now Graphwise).  SKOS-first design limits OWL expressiveness.  Enterprise pricing.                                                                              |
| **Semaphore** (Progress) | SKOS, limited OWL                        | Enterprise multi-user                    | Audit trail                           | Limited                              | Commercial                    | Taxonomy-focused; insufficient for OWL-level expressiveness.                                                                                                                          |
| **OntoPortal**           | OWL, SKOS                                | Web-based, multi-user                    | Version tracking                      | Ontology visualization               | Free, open-source             | Designed for ontology repositories (BioPortal model), not editing environments.  Overkill for vocabulary management.                                                                  |

#### 5.2.2 Graph-Based Ontology Editors

| Tool                       | Graph Editing                          | OWL Support   | Integration                               | License                | Risk Assessment                                                                                                           |
|----------------------------|----------------------------------------|---------------|-------------------------------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Grafo**                  | Visual graph editing                   | OWL 2         | Export OWL/RDF                            | Free tier + commercial | Promising but early-stage; unclear long-term viability.  No Python API.                                                   |
| **Metaphactory**           | Visual graph exploration, SPARQL-based | Full RDF/OWL  | REST API, SPARQL endpoint                 | Commercial             | Enterprise-grade knowledge graph platform.  Expensive.  More suited to large knowledge graphs than vocabulary management. |
| **yEd / yEd Live**         | Visual graph editing                   | No native OWL | Export GraphML, import/export via scripts | Free                   | General-purpose graph editor.  Would require custom conversion scripts.  No semantic awareness.                           |
| **draw.io / diagrams.net** | Visual diagramming                     | None          | Export SVG/PNG                            | Free                   | Visualization only; no semantic layer.  Useful for documentation diagrams, not for editing the ontology.                  |

#### 5.2.3 Lightweight / Developer-Oriented Tools

| Tool                   | Approach                                   | OWL Support                               | Integration                    | License           |
|------------------------|--------------------------------------------|-------------------------------------------|--------------------------------|-------------------|
| **LinkML**             | YAML-based schema language for linked data | Generates OWL, JSON Schema, SHACL, Python | CLI generators, Python library | Free, open-source |
| **Cogs** (YAML -> OWL) | YAML vocabulary definitions -> OWL         | Generation only                           | Python scripts                 | Free, open-source |
| **OWLReady2**          | Python library for OWL manipulation        | Full OWL 2                                | Direct Python integration      | Free, open-source |
| **RDFLib**             | Python library for RDF                     | RDF/OWL parsing/serialization             | Direct Python integration      | Free, open-source |

### 5.3 Recommendation

**Primary workflow**: YAML control files in git, edited directly or via IDE.
No external platform dependency.

**Visualization and exploration**: **VocBench 3** deployed as a read-mostly
tool. The generated OWL is imported into VocBench for browsing, graph
exploration, and SPARQL queries. VocBench can also be used for experimental
edits that are then back-ported to YAML.

**YAML-to-OWL generation**: Evaluate **LinkML** as the schema language for
the YAML control files. LinkML is purpose-built for defining linked-data
schemas in YAML and can generate OWL, JSON Schema, Python dataclasses, and
SHACL shapes from a single source. If LinkML's expressiveness proves
sufficient for the LCMA model, it would replace custom generation scripts
for G3a/G3c and provide a maintained, community-backed toolchain.

**Fallback if LinkML is insufficient**: Custom Python generators using
**RDFLib** (for OWL generation) and **Jinja2** (for Python code generation)
operating on a custom YAML schema validated by JSON Schema.

**Decision point**: LinkML suitability must be evaluated during G2 (YAML
schema design). The evaluation criteria are:

1. Can LinkML express metaconcept hierarchies with metafeature definitions?
2. Can LinkML generate the `FancyStrEnum` pattern used in `musicalform`?
3. Can LinkML incorporate IFLA LRM terms as external imports?

---

## 6. Tooling: Module-by-Module Analysis

### 6.1 Vocabulary and Ontology Management (Primary)

**Functional need**: Create, modify, browse, and validate concept definitions
and their relations.

**Paradigms**:

| Paradigm                            | Description                                      | Suitability                                                              |
|-------------------------------------|--------------------------------------------------|--------------------------------------------------------------------------|
| Plain-text files in git (YAML/TOML) | Version-controlled, diff-friendly, CI-integrated | **Best fit for source of truth**.  Requires schema validation tooling.   |
| Spreadsheet (cloud or local)        | Familiar UI, multi-user                          | Poor for nested data, merge conflicts in CSV, no validation              |
| Ontology editor (Protege/VocBench)  | Purpose-built for OWL/SKOS                       | Good as secondary view; too heavyweight and opaque as primary source     |
| Custom web GUI                      | Tailored to domain                               | High development cost; consider only if YAML editing proves insufficient |

**Recommended solution**: YAML files in git + JSON Schema validation.
Evaluate LinkML as the schema framework (see [Section 5.3](#53-recommendation)).

**Dependency path**: This decision constrains G2 (schema design), G3a-c
(generators), and G4 (CI checks). All downstream tooling must consume YAML
as input.

### 6.2 OWL/RDF Storage and Manipulation

**Functional need**: Generate, parse, serialize, and query OWL/RDF
representations of the model.

**Paradigms**:

| Paradigm                                   | Description                                             | Suitability                                                                                                            |
|--------------------------------------------|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| File-based OWL (Turtle, RDF/XML)           | Generated files committed to git or produced on-the-fly | **Best fit**.  Simple, version-controlled, no server dependency.                                                       |
| In-memory RDF (Python library)             | Load OWL into Python for programmatic manipulation      | Needed for generation and validation scripts.                                                                          |
| Triple store (Fuseki, GraphDB, Blazegraph) | SPARQL endpoint for complex queries                     | Overkill for current vocabulary size (~100 concepts).  Consider if model grows to 1000+ concepts with dense relations. |
| Graph database (Neo4j, etc.)               | Property graph model                                    | Impedance mismatch with OWL.  Not recommended.                                                                         |

**Recommended solution**: **RDFLib** for in-memory OWL manipulation in Python.
Generated OWL is serialized to Turtle format and committed to git. If LinkML
is adopted, its built-in OWL generator replaces custom RDFLib scripts.

**Dependency path**: RDFLib is already pure-Python with no external server
dependencies. Produces minimal technological debt.

### 6.3 Ontology Reasoning

**Functional need**: Infer implicit relations, check consistency of concept
definitions, validate OWL constraints.

**Paradigms**:

| Paradigm                              | Description                            | Suitability                                                                                                                    |
|---------------------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| OWL DL reasoner (HermiT, Pellet, ELK) | Full OWL reasoning                     | Needed if the ontology uses OWL axioms for consistency checking.  Java-based; can be called from Python via owlready2 or Jena. |
| SHACL validation                      | Shape-based constraint checking on RDF | **Preferred** for vocabulary-level validation (cardinality, value ranges, required properties).  Python support via pySHACL.   |
| SPARQL-based checks                   | Custom queries that detect violations  | Lightweight, no external reasoner needed.  Good for CI checks.                                                                 |

**Recommended solution**: **pySHACL** for shape-based validation of the
generated OWL. SHACL shapes are generated alongside OWL (from YAML or
LinkML). Full OWL DL reasoning (HermiT/Pellet) is deferred until the
ontology reaches a complexity that requires it.

**Dependency path**: pySHACL depends on RDFLib. Minimal additional debt.

### 6.4 Visualization and Graph Interaction

**Functional need**: Display the ontology as an interactive graph for
exploration, communication, and (optionally) editing.

**Paradigms**:

| Paradigm                                            | Description                                 | Suitability                                                                                    |
|-----------------------------------------------------|---------------------------------------------|------------------------------------------------------------------------------------------------|
| Web-based ontology browser (VocBench)               | Full OWL browsing, SPARQL, tree/graph views | **Best fit for collaborative exploration**.  Requires server deployment.                       |
| Python visualization (pyvis, NetworkX + matplotlib) | Programmatic graph rendering                | Good for CI-generated diagrams in documentation.  Not interactive enough for daily use.        |
| Standalone graph editor (yEd, Cytoscape)            | Desktop graph visualization                 | Requires manual export/import.  No semantic layer.                                             |
| Web-based graph library (D3.js, Cytoscape.js)       | Custom interactive visualization            | High development cost.  Consider for the Quarto website (embedded interactive vocab explorer). |

**Recommended solution**: **VocBench 3** for interactive exploration (import
generated OWL).  **pyvis or Mermaid** for auto-generated diagrams embedded in
Quarto documentation.

**Dependency path**: VocBench requires a Java/Tomcat server. For the team,
a shared deployment (e.g., on a university server or a small cloud VM) is
sufficient. pyvis/Mermaid produce no server dependency.

### 6.5 Documentation Generation

**Functional need**: Render the Quarto website with auto-generated reference
material (from the model) and manually curated content.

**Paradigms**:

| Paradigm         | Description                                      | Suitability                                                                         |
|------------------|--------------------------------------------------|-------------------------------------------------------------------------------------|
| Quarto (current) | Markdown/notebook rendering, multi-format output | **Already in use**.  Supports Jupyter, R, and plain Markdown.  Diataxis-compatible. |
| Sphinx           | Python-native documentation                      | Would require migration.  No clear advantage over Quarto for this project.          |
| MkDocs           | Markdown-based static site                       | Simpler than Quarto but less flexible.  No notebook support.                        |
| Docusaurus       | React-based documentation                        | Overkill.  JavaScript dependency.                                                   |

**Recommended solution**: **Quarto** (retain current setup). Auto-generated
reference pages (vocabulary table, concept pages, vignette stubs) are produced
by Python scripts that read YAML and output Markdown/QMD files into a
designated directory. The Quarto build includes these alongside the wiki
content.

**Dependency path**: Quarto depends on Pandoc and (for Jupyter) a Python
kernel. These are already in use.

### 6.6 Grammar and Parser Infrastructure

**Functional need**: Define the annotation label grammar, auto-generate a
parser, validate labels.

**Paradigms**:

| Paradigm                        | Description                                   | Suitability                                                                                                                    |
|---------------------------------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| EBNF + DHParser (current)       | EBNF grammar, auto-generated Python parser    | **Already in use**.  DHParser is maintained and produces working parsers.  The EBNF is the standard's normative specification. |
| EBNF + Lark                     | Alternative Python parser generator from EBNF | Lark is more widely used and better documented than DHParser.  Migration would require adapting the parse-tree processing.     |
| PEG + Parsimonious/Arpeggio     | PEG grammar variant                           | No clear advantage over EBNF for this grammar.                                                                                 |
| Custom regex/handwritten parser | No grammar file                               | Not maintainable for a growing standard.                                                                                       |

**Recommended solution**: **Retain DHParser** for now. The EBNF is generated
from YAML (G3b) and fed to DHParser. Evaluate migration to **Lark** if
DHParser maintenance becomes a concern (DHParser is a smaller project with
fewer maintainers).

**Dependency path**: DHParser is a single Python dependency. Lark migration
would require rewriting `core.py`'s parse-tree processing (~200 lines) but
no architectural changes.

### 6.7 Annotation Validation

**Functional need**: Validate annotation labels (strings, CSV files, TiLiA
JSON files) against the grammar and the model.

**Current state**: `musicalform validate` supports expression, file, CSV, and
JSON validation modes. Validation is grammar-level only (syntactic); it does
not check whether a label's semantic content is consistent with the model
(e.g., whether a function is valid at a given hierarchical level).

**Recommended expansion**:

1. **Syntactic validation** (current): grammar parsing via DHParser.
2. **Vocabulary validation**: check that all terms in a label exist in the
   VocabularyRegistry.
3. **Structural validation**: check that containment relations are respected
   (e.g., `presentation` must appear within a `sentence` or `hybrid` type).
4. **Cross-reference validation**: check that material references resolve to
   existing named segments.

**Dependency path**: Levels 2-4 depend on G5 (VocabularyRegistry) and the
YAML schema encoding containment/constraint rules.

### 6.8 CI/CD and Version Management

**Functional need**: Automated testing, consistency checking, and release
management.

**Current state**: GitHub Actions CI (`ci.yml`) runs tox on Python 3.11/3.12.
Release-please (`release-please.yml`) manages versioning on the `development`
branch.

**Recommended expansion**:

| CI Check          | Description                                                                  | Depends on        |
|-------------------|------------------------------------------------------------------------------|-------------------|
| `check-sync`      | Verify all derived artifacts (Python enums, EBNF, OWL) match the YAML source | G3a, G3b, G3c, G4 |
| `check-grammar`   | Re-generate parser from EBNF, run grammar tests                              | G3b               |
| `check-owl`       | Validate generated OWL with pySHACL shapes                                   | G3c               |
| `check-vignettes` | Verify all concepts in YAML have a vignette stub                             | G7                |
| `test-validation` | Run annotation validation on test corpus (annotation_pilot)                  | G6                |
| `preview-docs`    | Build Quarto site, deploy preview for PR review                              | G10               |

**Version numbering**: SemVer with domain-specific meaning:

- **Major**: Breaking changes to the annotation standard (existing labels may
  become invalid).
- **Minor**: New concepts, metaconcepts, or metafeatures added; existing labels
  remain valid.
- **Patch**: Bug fixes, documentation updates, tooling changes that do not
  affect the model.

---

## 7. Derivation Hierarchy and Change Propagation

### 7.1 Source of Truth

```
YAML control files (vocabulary/*.yaml)
    |
    |--- [G3a: generate] ---> Python enums + dataclasses
    |                           (musicalform/src/musicalform/enums.py, core.py)
    |
    |--- [G3b: generate] ---> EBNF grammar
    |                           (grammar/lcma_standard.ebnf)
    |                             |
    |                             |--- [DHParser] ---> Parser script
    |                                   (musicalform/src/musicalform/cli/lcma_standardParser.py)
    |
    |--- [G3c: generate] ---> OWL ontology
    |                           (ontology/generated/lcma_ontology.ttl)
    |
    |--- [G7: generate] ----> Vignette stubs
    |                           (wiki/vignettes/vignette-<concept>.md)
    |
    |--- [G10: generate] ---> Vocabulary reference pages
                                (docs/reference/generated/)
```

The **Python metaconcept hierarchy** (abstract classes, Protocols, structural
logic in `core.py`) is maintained directly in Python and is upstream of YAML
in the sense that the YAML schema must conform to the structural rules defined
in Python. However, the vocabulary data flows from YAML to Python.

```
Python metaconcept hierarchy (core.py, structural logic)
    ^
    | (schema constraints flow up)
    |
YAML control files (vocabulary/*.yaml)
    |
    | (data flows down to all derived artifacts)
    v
```

### 7.2 Change Propagation Rules

1. **Any change to a derived artifact that is not reflected in the YAML source
   is either (a) a manual curation in a designated overlay location, or (b) a
   bug.**

2. **Designated overlay locations** (where manual content coexists with
   generated content):
    - Vignette narratives: the `## Description` section (and below) in vignette
      files is manually curated. The header and metadata are generated.
    - Wiki pages: entirely manually curated.
    - Quarto configuration: manually maintained.

3. **CI enforcement**: The `check-sync` CI job regenerates all derived
   artifacts from YAML and compares them to the committed versions. Any
   difference causes a build failure. This ensures that no hand-edit to a
   generated file can be merged without updating the YAML source.

4. **Parser script duplication**: The parser script currently exists in two
   locations (`grammar/` and `musicalform/src/musicalform/cli/`). Under the
   new architecture, the canonical location is within the Python package. The
   `grammar/` copy is removed; the EBNF source remains in `grammar/` and the
   generation step places the parser directly into the package.

### 7.3 Change Propagation Example

A musicologist wants to add the concept "bridge" (abbreviation "br") as a
function at the section level:

1. Edit `vocabulary/functions.yaml`, adding:
   ```yaml
   bridge:
     abbreviations: [br]
     type: function
     hierarchical_level: section
     explanation: "Transition module."
     provenance: pop/rock form theory
   ```

2. Run `make generate` locally (or let CI do it):
    - `enums.py` gains `bridge = auto()` and `br = bridge` in
      `SpecificFunctionName`.
    - `lcma_standard.ebnf` gains `| 'bridge' | 'br'` in the
      `SpecificFunction` rule.
    - `lcma_ontology.ttl` gains a new OWL individual.
    - `wiki/vignettes/vignette-bridge.md` is created as a stub.

3. Commit all generated files + YAML change. Open PR.

4. CI runs: `check-sync` passes (generated files match YAML), grammar tests
   pass, OWL validation passes.

5. Reviewers inspect the YAML diff and the generated diffs. Approve.

6. Merge triggers release-please -> new minor version.

---

## 8. Collaborative Workflow

### 8.1 The Daily Cycle

The following workflow is optimized for the operation that will happen
thousands of times: changing a definition or adding a term.

```
1. Musicologist edits YAML file(s)
   (directly in GitHub web editor, VS Code, or vocabulary GUI)
       |
       v
2. Opens Pull Request
       |
       v
3. CI automatically:
   a. Validates YAML against JSON Schema
   b. Regenerates all derived artifacts
   c. Runs check-sync (generated == committed)
   d. Runs grammar tests (parse test corpus)
   e. Runs OWL validation (pySHACL)
   f. Builds Quarto preview site
       |
       v
4. PR shows:
   - YAML diff (the substantive change)
   - Generated diffs (auto-produced, reviewable)
   - Quarto preview link (rendered documentation)
   - CI status (all green / failures with messages)
       |
       v
5. Colleagues review and discuss
   (domain review of the concept definition,
    not code review of generated artifacts)
       |
       v
6. Merge -> release-please creates version bump PR
       |
       v
7. Merge version bump -> new release tag
   - GitHub Pages rebuilds
   - PyPI publish (if configured)
   - VocBench OWL import (if configured)
```

### 8.2 Roles

| Role                | Responsibilities                                                                    | Tools                                        |
|---------------------|-------------------------------------------------------------------------------------|----------------------------------------------|
| **Musicologist**    | Edit concept definitions (YAML), write vignette narratives, review peer definitions | GitHub web editor / VS Code / vocabulary GUI |
| **Model architect** | Maintain Python metaconcept hierarchy, design YAML schema, write generators         | IDE (PyCharm/VS Code), Python                |
| **Annotator**       | Create TiLiA analyses, report validation failures                                   | TiLiA, `musicalform validate` CLI            |
| **Maintainer**      | CI configuration, release management, infrastructure                                | GitHub Actions, Quarto, VocBench server      |

### 8.3 Branch Strategy

- `main`: production; protected; only release-please PRs merge here.
- `development`: integration branch; PRs from feature branches merge here.
  CI runs on push and PR.
- Feature branches: `vocab/<concept-name>`, `fix/<issue>`, `feat/<feature>`.

---

## 9. Documentation Architecture

### 9.1 Diataxis Structure (Retained)

| Quadrant         | Source                            | Content type     | Generation                                           |
|------------------|-----------------------------------|------------------|------------------------------------------------------|
| **Tutorial**     | `wiki/tutorials/`                 | Manually curated | None                                                 |
| **How-To**       | `wiki/`                           | Manually curated | None                                                 |
| **Explanations** | `wiki/`                           | Manually curated | None                                                 |
| **Reference**    | `wiki/Syntax.md`, generated pages | Mixed            | Vocabulary table, concept reference pages, vignettes |

### 9.2 Wiki Submodule Resolution

The wiki submodule is retained for manually curated content (tutorials,
how-tos, explanations, syntax reference). Browser-based editing via the
GitHub wiki interface remains available for these pages.

The vocabulary reference (currently `Vocabulary.ipynb` reading a CSV) is
replaced by auto-generated reference pages produced from YAML. The Jupyter
notebook is deprecated once the generated reference pages are operational.

The CSV file (`data/Form vocabulary.csv`) is deprecated once the YAML control
files are the source of truth. A one-time migration (CSV -> YAML) is part of
G1/G2.

### 9.3 Vignette Workflow

Each concept in the YAML source gets a vignette page. The page has two
sections:

1. **Auto-generated header** (regenerated on every build):
    - Concept name, abbreviations, hierarchical level, type/function
    - Metaconcept membership
    - Metafeature summary (when metafeatures are defined)
    - Related concepts (containment, see-also)
    - Theoretical provenance

2. **Manually curated body** (preserved across regeneration):
    - Narrative description
    - Musical examples with analysis
    - Edge cases and common mistakes
    - References

The generation script detects the boundary marker (e.g.,
`<!-- BEGIN MANUAL CONTENT -->`) and preserves everything below it. New
vignette stubs are created with a template body that the author fills in.

### 9.4 Quarto Build Pipeline

```
make docs:
  1. Generate reference pages from YAML -> docs/reference/generated/
  2. Generate vignette stubs (if missing) -> wiki/vignettes/
  3. Generate vocabulary table QMD -> docs/reference/vocabulary.qmd
  4. Run quarto render (includes wiki/ content + generated content)
  5. Output to docs/ (GitHub Pages source)
```

---

## 10. Phased Migration Path

### Phase 0: Preparation (1-2 weeks)

- G1: Audit and reconcile the term inventory across CSV, EBNF, and Python
  enums. Produce a consolidated term list.
- Set up the `vocabulary/` directory in the guidelines repo.

### Phase 1: Schema and Generators (2-4 weeks)

- G2: Design the canonical YAML schema. Evaluate LinkML vs. custom schema.
  Define JSON Schema for validation.
- G3a: Implement YAML -> Python generator. Verify it produces output
  identical to the current hand-written enums.
- G3b: Implement YAML -> EBNF generator (or EBNF back-import + YAML ->
  EBNF roundtrip).
- G4: Implement `check-sync` CI job.

### Phase 2: OWL and Validation (2-3 weeks)

- G3c: Implement YAML -> OWL generator with human-readable URIs and IFLA LRM
  imports.
- G8: Write cross-source consistency tests and property-based grammar tests.
- G9: Set up OWL export/import bridge (initially export-only).
- Deploy VocBench instance, import generated OWL.

### Phase 3: Documentation and Vignettes (2-4 weeks)

- G7: Implement vignette stub generator.
- G10: Rebuild Quarto pipeline with generated reference pages.
- Deprecate `Vocabulary.ipynb` and CSV.
- Begin vignette authoring campaign (assign concepts to musicologists).

### Phase 4: Validation Expansion (2-3 weeks)

- G5: Implement VocabularyRegistry.
- G6: Expand annotation validation to vocabulary/structural/cross-reference
  levels.
- Begin iterative consolidation (G11) with annotation_pilot analyses.

### Phase 5: Workflow Maturation (Ongoing)

- G12: Evaluate and deploy vocabulary management GUI (if YAML editing proves
  insufficient for the team).
- G13: Integrate human review workflow with CI previews.
- Continue vignette authoring, model refinement, annotation validation.

---

## 11. Open Questions

The following questions require human input about the domain model and cannot
be resolved by architectural decisions alone.

### Q1: Relations Between Concepts

What is the complete set of relation types between concepts? The current
model has:

- **contains** (hierarchical composition: a sentence contains a presentation
  and a continuation)
- **is realised as** (function -> type: a theme is realised as a sentence)

Are there additional relation types needed? Candidates:

- **precedes** / **follows** (temporal ordering within a parent)
- **contrasts with** (functional contrast between sibling concepts)
- **transforms into** (functional transformation relation)
- **is a specialization of** (sub-concept hierarchy beyond metaconcept ->
  concept)

### Q2: Metafeature Value Types

What types of values can a metafeature take? The terminology defines several
possibilities:

- Probability distribution
- Score-based ranking
- Single imperative value
- Logic-based values

Are all of these needed in v0.2? Which should be implemented first?

### Q3: Congruence Scoring

How is the congruence score computed when a concept is resolved against a
musical object? Is this:

- A weighted sum of individual metafeature scores?
- A threshold-based pass/fail for each metafeature?
- A fuzzy logic combination?
- Domain-specific and different per concept?

### Q4: Style Conditioning

How are metaconcepts conditioned by musical style? Is style an explicit
parameter in the YAML schema (e.g., `style: viennese_classic`), or is it
implicit in the concept hierarchy (e.g., `half_cadence_viennese_classic` is a
concept under the `half_cadence` metaconcept)?

### Q5: IFLA LRM Subclasses

Which specific subclasses of Work, Expression, Manifestation, and Item are
"most relevant" for inclusion in the OWL ontology? The paper
(`Brahms_Form_New_text.html`) may specify these, but explicit confirmation
is needed.

### Q6: Annotation Pilot Scope

How many TiLiA analysis files exist in annotation_pilot? What is the
expected pass rate when validated against the current grammar? This
determines the scope of G11 (iterative consolidation).

---

## Appendices

### Appendix A: Conceptual Package Structure (Draft)

> **Note**: This is a conceptual draft subject to substantial change depending
> on decisions about LinkML adoption, the YAML schema design, and evolving
> understanding of the domain model.

```
guidelines/                          # This repository
├── vocabulary/                      # YAML control files (source of truth)
│   ├── schema.yaml                  # YAML schema definition (or LinkML schema)
│   ├── functions.yaml               # Specific function definitions
│   ├── units.yaml                   # Generic unit definitions
│   ├── types.yaml                   # Formal type definitions
│   ├── operators.yaml               # Material operator definitions
│   └── relations.yaml               # Inter-concept relations
├── grammar/
│   └── lcma_standard.ebnf           # Generated from vocabulary/ YAML
├── ontology/
│   ├── generated/
│   │   └── lcma_ontology.ttl        # Generated from vocabulary/ YAML
│   ├── shapes/
│   │   └── lcma_shapes.ttl          # SHACL shapes for OWL validation
│   └── protege/
│       └── form_ontology.owl        # Deprecated; kept for reference
├── generators/
│   ├── yaml_to_python.py            # G3a
│   ├── yaml_to_ebnf.py             # G3b
│   ├── yaml_to_owl.py              # G3c
│   ├── yaml_to_vignettes.py        # G7
│   └── yaml_to_docs.py             # G10
├── wiki/                            # Submodule: manually curated content
│   ├── tutorials/
│   ├── vignettes/                   # Vignette stubs (generated) + narratives (manual)
│   ├── Syntax.md
│   └── ...
├── data/
│   └── Form vocabulary.csv          # Deprecated; kept for reference
├── _quarto.yml
├── Vocabulary.ipynb                 # Deprecated; replaced by generated pages
├── Makefile                         # Targets: generate, check-sync, docs, test
└── architecture.md                  # This document

musicalform/                         # Submodule: Python library
├── src/musicalform/
│   ├── __init__.py
│   ├── enums.py                     # Generated from vocabulary/ YAML (G3a)
│   ├── core.py                      # Domain model (manually maintained)
│   ├── registry.py                  # VocabularyRegistry (G5)
│   ├── utils.py
│   └── cli/
│       ├── main.py
│       ├── validate.py
│       └── lcma_standardParser.py   # Generated from EBNF by DHParser
├── tests/
│   ├── test_enums.py
│   ├── test_core.py
│   ├── test_registry.py
│   ├── test_validation.py
│   └── test_consistency.py          # Cross-source consistency tests (G8)
└── pyproject.toml
```

### Appendix B: Interface Contracts (Draft)

#### B.1 YAML Concept Entry Schema

```yaml
# JSON Schema for a single concept entry (conceptual draft)
type: object
required: [ abbreviations, category, hierarchical_level ]
properties:
  abbreviations:
    type: array
    items: { type: string }
    description: "Short labels; first element is the preferred abbreviation."
  category:
    type: string
    enum: [ function, type, subtype, operator ]
  hierarchical_level:
    type: string
    enum: [ movement, section, phrase, subphrase, cross-level ]
  contains:
    type: array
    items: { type: string }
    description: "Canonical names of concepts this concept contains."
  provenance:
    type: string
    description: "Theoretical source (e.g., 'Caplin1998')."
  explanation:
    type: string
  vignette:
    type: string
    description: "Path to the vignette file."
  metafeatures:
    type: object
    description: "Metafeature definitions (schema TBD per Q2)."
  style:
    type: string
    description: "Musical style scope (schema TBD per Q4)."
```

#### B.2 VocabularyRegistry Interface

```python
class VocabularyRegistry:
    """Runtime lookup for the generated vocabulary."""

    def lookup(self, name_or_abbreviation: str) -> ConceptEntry: ...

    def by_level(self, level: str) -> list[ConceptEntry]: ...

    def by_category(self, category: str) -> list[ConceptEntry]: ...

    def all_abbreviations(self) -> dict[str, str]: ...

    def contains_tree(self, concept: str) -> dict: ...
```

#### B.3 Generator Interface

Each generator follows the same interface:

```python
def generate(
        yaml_dir: Path,  # Directory containing YAML control files
        output_path: Path,  # Output file path
        check_only: bool = False  # If True, compare but do not write
) -> bool:  # Returns True if output matches source
    ...
```

When `check_only=True`, the generator produces output in memory and compares
it to the existing file at `output_path`. Returns `True` if they match,
`False` (and prints a diff) if they diverge. This is the mechanism used by
the `check-sync` CI job.

### Appendix C: File Mapping (Current -> Future)

| Current file                           | Future status                   | Replacement                              |
|----------------------------------------|---------------------------------|------------------------------------------|
| `data/Form vocabulary.csv`             | Deprecated                      | `vocabulary/*.yaml`                      |
| `Vocabulary.ipynb`                     | Deprecated                      | Generated reference pages                |
| `grammar/lcma_standard.ebnf`           | Generated                       | From `vocabulary/*.yaml` via G3b         |
| `grammar/lcma_standardParser.py`       | Removed                         | Single copy in musicalform package       |
| `musicalform/src/musicalform/enums.py` | Generated                       | From `vocabulary/*.yaml` via G3a         |
| `musicalform/src/musicalform/core.py`  | Manually maintained             | Metaconcept hierarchy stays in Python    |
| `ontology/protege/form_ontology.owl`   | Deprecated (kept for reference) | `ontology/generated/lcma_ontology.ttl`   |
| `wiki/vignettes/*.md`                  | Hybrid                          | Headers generated, body manually curated |
| `wiki/*.md` (non-vignette)             | Manually maintained             | No change                                |
| `_quarto.yml`                          | Manually maintained             | Updated to include generated content     |

### Appendix D: Technological Debt Inventory

Every 3rd-party dependency creates potential technological debt. The
following table assesses the risk for each dependency in the recommended
architecture.

| Dependency                 | Role                      | Maintenance status                    | Replacement difficulty                              | Risk       |
|----------------------------|---------------------------|---------------------------------------|-----------------------------------------------------|------------|
| **DHParser**               | EBNF -> parser generation | Maintained (small team)               | Medium (Lark is a viable alternative)               | Medium     |
| **RDFLib**                 | OWL/RDF manipulation      | Well-maintained, large community      | Low (standard Python RDF library)                   | Low        |
| **pySHACL**                | SHACL validation          | Maintained                            | Medium (could use SPARQL-based checks)              | Low-Medium |
| **Quarto**                 | Documentation rendering   | Well-maintained (Posit)               | Medium (MkDocs or Sphinx as alternatives)           | Low        |
| **LinkML** (if adopted)    | YAML schema + generators  | Actively developed, growing community | High (would need custom generators)                 | Medium     |
| **VocBench** (if deployed) | Ontology browsing         | EU-funded, actively developed         | Low (optional convenience; not the source of truth) | Low        |
| **pandas**                 | CSV/data processing       | Standard Python library               | Low                                                 | Negligible |
| **release-please**         | Version management        | Google-maintained                     | Low (conventional-commits alternatives exist)       | Low        |
| **tox/pytest**             | Testing                   | Standard Python ecosystem             | Low                                                 | Negligible |
