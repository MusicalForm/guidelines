# LCMA Model Architecture Draft

> **Status**: Draft for review -- v0.1, 2026-03-30
> **Purpose**: This document proposes an integrated architecture for the LCMA
> modelling infrastructure.  It is structured to present options where the path
> is not yet determined, and to flag open questions that require human decision.
> Nothing here is prescriptive until reviewed and approved by the project team.

---

## Table of Contents

1. [Current State Inventory](#1-current-state-inventory)
2. [Architecture Goals](#2-architecture-goals)
3. [Design Principles](#3-design-principles)
4. [The Central Root: `musicalform` Python Library](#4-the-central-root-musicalform-python-library)
5. [Downstream Components and Interfaces](#5-downstream-components-and-interfaces)
6. [Collaborative Workflow and Version Management](#6-collaborative-workflow-and-version-management)
7. [Tooling Recommendations](#7-tooling-recommendations)
8. [Migration Path](#8-migration-path)
9. [Open Questions Requiring Human Decision](#9-open-questions-requiring-human-decision)

---

## 1. Current State Inventory

### 1.1 Components at a Glance

| Component | Location | Version | Status |
|-----------|----------|---------|--------|
| Guidelines homepage | `_quarto.yml`, rendered to `docs/` | N/A | Outdated; needs rebuild after every change |
| Wiki content | `wiki/` (git submodule) | N/A | Partially outdated; browser-editable |
| Vocabulary spreadsheet | Nextcloud (external) | N/A | Partially deprecated; CSV export in `data/` |
| Vocabulary notebook | `Vocabulary.ipynb` | N/A | Renders CSV; will be superseded |
| EBNF grammar | `grammar/lcma_standard.ebnf` | v0.1 | Closest to authoritative v0.1.0 of standard |
| Auto-generated parser | `grammar/lcma_standardParser.py` | v0.1 | Generated from EBNF via DHParser |
| `musicalform` library | `musicalform/` (git submodule) | v0.1.0 | Minimal but functional; enums + domain model |
| OWL ontology | `ontology/protege/form_ontology.owl` | Sept 2024 | Deprecated; needs full rebuild |
| Analysis model paper | `ontology/model_of_music_analysis/` | N/A | Conceptual foundation; current |
| Vignettes | `wiki/vignettes/` (2 files) | N/A | Only 2 exist; every concept needs one |
| Annotation pilot | Separate repo (`annotation_pilot`) | N/A | Contains TiLiA analyses to be validated |
| draw.io diagrams | `ontology/drawio/classical.drawio` | N/A | Unknown currency |

### 1.2 The `musicalform` Library in Detail

The library (v0.1.0) currently contains:

- **`enums.py`** -- `FancyStrEnum` base class with 10 enum subclasses encoding
  the full analytical vocabulary: `SpecificFunctionName` (29 members + aliases),
  `UnitName` (14), `MainType` (18), `SubType` (3), `MaterialOperator` (14 +
  symbol aliases), `PlaceholderName`, `CertaintyName`, `ReferenceSentinel`,
  `FunctionSpecificity`.
- **`core.py`** -- Domain model as dataclasses: `AnnotationLabel`, `FormLabel`,
  `PlaceholderLabel`, `FormalFunction` (ABC), `SingleFunction`,
  `SpecificFunction`, `GenericFunction`, `FunctionalTransformation`,
  `FormalType`, `SingleReference`, `MaterialReferences`,
  `TransformationalReferences`.  Each with `from_parse()` classmethods that
  consume the DHParser JSON dict output.
- **`utils.py`** -- `compact_repr` decorator, recursive dict concatenation,
  parse-tree helpers.
- **`cli/validate.py`** -- CLI for validating expressions, CSVs, TiLiA JSON
  files, and directories thereof.
- **CI** -- pytest (8 tests), tox, pre-commit (black, isort, flake8, mypy),
  release-please for automated versioning.

### 1.3 The OWL Ontology in Detail

The `form_ontology.owl` (Sept 2024) defines:

- **Classes**: `Formal Function`, `Formal Type`, `Form-functional Aspect`
  (subclasses: `Directionality`, `Weightedness`, `Temporality`), `Feature`
  (subclasses: `Context-Independent Feature`, `Context-Dependent Feature`),
  `Intrinsic Function`, `Contextual Function` (subclass: `Positional
  Function`), `Musical Domain`, `Musical Expression`, `Timeline`, `Timespan`
  (subclass: `Musical Context`).
- **Properties**: `characterises`/`is characterised by`, `qualifies`/`is
  qualified by`, `informs`/`is informed by`, `operationalises`/`is
  operationalised by`, `realises`/`is realised as`, `embeds`/`is embedded in`,
  `elapses over`, `is context of`.

This ontology captures the *meta-level* (what a Formal Function is, how it
relates to Features and Types) but **not** the vocabulary itself (individual
functions, types, features).  It is deprecated but its conceptual structure
remains relevant.

### 1.4 The Vocab Spreadsheet

The CSV export (`data/Form vocabulary.csv`, 103 rows) contains columns:
`Formal label`, `Short label`, `Function/type`, `Hierarchical level`,
`Relation: contains`, `Short explanation`, `Open Music Theory Link`,
`Theoretical provenance`.  Rows 1--60 are broadly current; rows 61--103 include
deprecated, speculative, and cadence-related terms that do not all appear in the
EBNF grammar or the Python enums.

### 1.5 The Conceptual Foundation

The paper *Modelling Music Analysis: Ambiguity* (Brahms_Form_New_text.html)
establishes the project's conceptual basis:

- Music analysis is modelled as **Claim Production** by Agents with Sets of
  Beliefs.
- A **Concept Attribution** is a claim relating a Musical Object to a Concept
  via a Relationship (match, partial match, no match).
- **Concepts** are defined recursively in terms of Features with value ranges.
- Draws on IFLA LRM (Work/Expression/Manifestation) and CIDOC CRM, adapted for
  music-analytical claims.
- Key insight: analysts' concept definitions differ in **feature weighting**,
  not always in the features themselves.

### 1.6 What is Missing / Inconsistent

1. **No single source of truth**: the vocab spreadsheet, the EBNF grammar, and
   the Python enums all contain overlapping but non-identical sets of terms.
2. **No concept definitions**: neither the Python classes nor the OWL ontology
   encode what defines a concept (which features, which value ranges).
3. **No hierarchical relations** between concepts in Python (e.g., `antecedent`
   is a Beginning function -- this is only implicit).
4. **No version alignment**: the grammar is at v0.1, the library at v0.1.0, the
   ontology is deprecated, the docs are outdated.
5. **No automated propagation**: changing a term in one place does not update
   others.
6. **Vignettes**: only 2 of ~60+ needed exist.
7. **Test coverage**: 8 tests covering enums and basic construction; no
   end-to-end parsing tests, no validation against the annotation pilot.

---

## 2. Architecture Goals

Derived directly from the project specs:

| # | Goal | Priority |
|---|------|----------|
| G1 | **Single source of truth** in Python that determines all other representations | Critical |
| G2 | **Modification propagation**: changing the model in one place detects/flags every downstream impact | Critical |
| G3 | **Consistency at all times**: the "production version" is valid across all components | Critical |
| G4 | **Collaborative modelling**: multiple contributors work on different parts simultaneously | Critical |
| G5 | **Versioned releases**: a single version number spanning standard, model, ontology, documentation | High |
| G6 | **Dialectic validation**: iterative fitting between model and existing annotations | High |
| G7 | **Layered model**: vertical metaconcept layers + horizontal abstraction levels | High |
| G8 | **Documentation as first-class output**: auto-generated + manually curated, Diataxis structure | High |
| G9 | **Ontology synchronization**: Python class hierarchy mirrored in OWL | Medium |
| G10 | **Vocabulary management GUI**: graph + table views, filtering, navigation | Medium |
| G11 | **Backward compatibility**: older annotation labels remain parseable | Medium |

---

## 3. Design Principles

### 3.1 Python as the Single Root

The `musicalform` Python library becomes the **canonical encoding** of the
model.  Every other representation (OWL, EBNF, documentation tables, vignette
stubs) is **derived from** or **validated against** the Python code.

**Rationale** (confirming your stated reasoning):
- Python's ecosystem provides conversion paths to every other format.
- IDE navigation (PyCharm) makes the model browseable and refactorable.
- The library already has CI, testing, and release infrastructure.
- Python dataclasses + enums provide both human-readable definitions and
  machine-processable structure.

### 3.2 Declaration over Generation

Wherever possible, the model should be **declared** in Python (class
definitions, docstrings, type annotations, class attributes) rather than
constructed procedurally.  This makes the model inspectable, diffable, and
reviewable without running code.

### 3.3 Layered Derivation

Changes flow in one direction:

```
Python model (source of truth)
    |
    +--> EBNF grammar (generated or validated)
    |        |
    |        +--> DHParser parser (auto-generated)
    |
    +--> OWL ontology (generated or validated)
    |
    +--> Documentation (generated stubs + manually curated content)
    |
    +--> Validation reports (against annotation_pilot)
    |
    +--> Vocabulary tables (CSV, HTML)
```

Any change to a downstream artifact that is not reflected in the Python source
is either: (a) a manual curation that lives in a designated "overlay" location,
or (b) a bug.

### 3.4 Fail-Loud Consistency

CI checks must **fail** when:
- The OWL ontology is out of sync with the Python model.
- The EBNF grammar does not accept/reject the same labels as the Python enums.
- A vignette stub is missing for a concept that exists in the model.
- An annotation from the pilot corpus parses under the grammar but produces an
  invalid object, or vice versa.

---

## 4. The Central Root: `musicalform` Python Library

### 4.1 Terminological Convention

To avoid collision with Python's `class` and `metaclass` keywords, and to align
with the conceptual model of music analysis as concept attribution:

| Your term | Proposed Python name | Rationale |
|-----------|---------------------|-----------|
| Metaclass (abstract concept template) | **`Metaconcept`** | Aligns with "concept attribution" model; avoids Python metaclass confusion |
| Class (parametrized concept) | **`Concept`** | The concrete, applicable unit |
| Feature (atomic or composite) | **`Feature`** | Direct mapping; no ambiguity |
| Meta-feature (feature + value range) | **`FeatureSpec`** | "Specification" conveys the value-range + preference-rule semantics |

> **QUESTION FOR TEAM**: Do these names work?  Alternatives considered:
> `ConceptTemplate`/`ConceptInstance`, `AbstractConcept`/`AppliedConcept`,
> `Schema`/`Concept`.  The important constraint is that these are
> *domain-model terms*, not Python implementation terms -- they should be
> meaningful to musicologists reading the code and documentation.

### 4.2 Proposed Package Structure

```
musicalform/
  src/musicalform/
    __init__.py                 # Public API

    # ── Layer 1: Vocabulary & Atoms ──────────────────────────
    vocabulary/
      __init__.py
      _base.py                  # FancyStrEnum, ConceptEnum base
      functions.py              # SpecificFunctionName enum (expanded)
      types.py                  # MainType, SubType enums (expanded)
      units.py                  # UnitName enum
      operators.py              # MaterialOperator enum
      relations.py              # RelationType enum (new)
      registry.py               # Central VocabularyRegistry singleton

    # ── Layer 2: Concept Definitions ─────────────────────────
    concepts/
      __init__.py
      _metaconcept.py           # Metaconcept base class
      _feature.py               # Feature, FeatureSpec base classes
      _concept.py               # Concept base class
      formal_functions/         # One module per metaconcept family
        __init__.py
        _base.py                # FormalFunction metaconcept
        beginning.py            # Beginning functions
        middle.py               # Middle functions
        ending.py               # Ending functions
        # ... style-specific sub-packages later
      formal_types/
        __init__.py
        _base.py                # FormalType metaconcept
        sentence.py
        period.py
        binary.py
        ternary.py
        sonata.py
        rondo.py
        # ...
      relations/
        __init__.py
        _base.py                # Relation metaconcept (generalizes MaterialRelations)
        material.py             # Material relations
        # ...
      features/                 # Bottom-up: atomic features
        __init__.py
        _base.py
        temporal.py             # Duration, position, proportion
        harmonic.py             # Cadence types, key relations
        melodic.py              # Contour, interval content
        rhythmic.py             # Metric position, rhythmic density
        textural.py             # Voice count, density
        # ...

    # ── Layer 3: Annotation Standard ─────────────────────────
    standard/
      __init__.py
      label.py                  # AnnotationLabel, FormLabel (refactored from core.py)
      parsing.py                # from_parse() logic (refactored from core.py)
      grammar.py                # EBNF generation/validation interface
      versioning.py             # Standard version management, migration

    # ── Layer 4: Ontology Bridge ─────────────────────────────
    ontology/
      __init__.py
      owl_export.py             # Python model -> OWL/RDF serialization
      owl_import.py             # OWL -> Python model validation/diff
      skos_export.py            # Vocabulary -> SKOS concept scheme
      graph.py                  # Graph operations (hierarchy, visualization data)

    # ── Layer 5: Documentation Bridge ────────────────────────
    docs/
      __init__.py
      vignette_stubs.py         # Generate vignette stub markdown from model
      vocab_table.py            # Generate vocabulary tables (replaces notebook)
      reference_gen.py          # Generate reference pages from docstrings

    # ── CLI ──────────────────────────────────────────────────
    cli/
      __init__.py
      main.py
      validate.py               # Existing validation (expanded)
      check.py                  # New: model consistency checks
      export.py                 # New: export to OWL, SKOS, EBNF, docs

  tests/
    test_vocabulary/
    test_concepts/
    test_standard/
    test_ontology/
    test_docs/
    test_integration/           # End-to-end: parse label -> object -> OWL -> back
    conftest.py                 # Shared fixtures
```

### 4.3 The Vocabulary Registry

The `VocabularyRegistry` is a singleton that indexes every concept,
abbreviation, and alias in the model.  It serves as the integration
point between the enum-based vocabulary and the concept hierarchy.

```python
# Sketch -- not final implementation
class VocabularyRegistry:
    """Central index of all terms in the LCMA model.

    Populated at import time by scanning all ConceptEnum subclasses
    and Concept subclasses.  Provides:
    - Lookup by canonical name, abbreviation, or alias
    - Lookup by metaconcept family
    - Hierarchical parent/child queries
    - Diff against a previous version
    - Export to SKOS, CSV, OWL individuals
    """

    def lookup(self, term: str) -> ConceptEntry: ...
    def children_of(self, concept: str) -> list[ConceptEntry]: ...
    def concepts_in(self, metaconcept: str) -> list[ConceptEntry]: ...
    def diff(self, other: "VocabularyRegistry") -> VocabDiff: ...
    def to_skos(self) -> rdflib.Graph: ...
    def to_dataframe(self) -> pd.DataFrame: ...
```

> **QUESTION FOR TEAM**: Should the registry be populated by *scanning* Python
> classes at import time (introspection), or by explicit *registration* calls?
> Introspection is more DRY; explicit registration is more predictable and
> allows ordering.

### 4.4 Concept and Metaconcept Classes

Each concept in the model will be represented as a Python class with:

1. **A docstring** following a structured template (parseable for documentation
   generation):
   ```python
   class Antecedent(BeginningFunction):
       """A phrase-level beginning function.

       .. musicological::
           The first phrase of a period, ending with a weak cadence
           (HC or IAC), creating an expectation of continuation.
           [Caplin 1998, p. 49]

       .. formal::
           Metaconcept: FormalFunction
           Parent: BeginningFunction
           Hierarchical level: Phrase
           Abbreviations: ant
           Typical children: {basic_idea, contrasting_idea}
           Defining features:
               cadence_type: {HC, IAC} [required]
               position: beginning [required]
               length: ~2 phrases [typical]

       .. vignette:: vignettes/antecedent
       """
   ```

2. **Class-level attributes** encoding structural properties that the
   ontology bridge and documentation generator can read:
   ```python
   class Antecedent(BeginningFunction):
       _abbreviations = ("ant",)
       _hierarchical_level = HierarchicalLevel.PHRASE
       _typical_children = (BasicIdea, ContrastingIdea)
       _defining_features = {
           "cadence_type": FeatureSpec(CadenceType, required=True,
                                       values={CadenceType.HC, CadenceType.IAC}),
           "position": FeatureSpec(PositionFunction, required=True,
                                    values={PositionFunction.BEGINNING}),
       }
   ```

3. **Integration with the existing FancyStrEnum** for backward compatibility:
   the enum member `SpecificFunctionName.antecedent` continues to exist, and
   the `VocabularyRegistry` maps it to the `Antecedent` class.

> **QUESTION FOR TEAM**: How tightly should enum members and concept classes
> be coupled?  Options:
>
> **Option A -- Enum members reference classes**: Each enum member gets a
> `.concept_class` attribute pointing to the corresponding class.  The enum
> remains the primary way to instantiate from strings; the class provides
> the full definition.
>
> **Option B -- Classes replace enums for concepts**: Concepts are only
> classes; the enum is reduced to a pure string-lookup mechanism that returns
> the class.  More OOP-pure but bigger refactor.
>
> **Option C -- Parallel with cross-references**: Enums and classes coexist
> independently, linked through the registry.  Least disruption to existing
> code.
>
> **Recommendation**: Option A -- it preserves the convenient `FancyStrEnum`
> instantiation while giving each concept a rich class definition.

### 4.5 The Horizontal Layers (Abstraction Levels)

The model's horizontal layering (universal -> style-specific) maps to Python's
package/module hierarchy:

```
concepts/
  formal_functions/
    _base.py                    # Universal: BeginningFunction, MiddleFunction, EndingFunction
    beginning.py                # Universal beginning functions (abstract FeatureSpecs)
    middle.py
    ending.py
    classical/                  # Style layer: classical common practice
      __init__.py
      beginning.py              # e.g., Antecedent with classical FeatureSpec values
      middle.py
      ending.py
    romantic/                   # Style layer: 19th century
      ...
    popular/                    # Style layer: popular music
      ...
```

At each layer, a concept class can:
- **Inherit** from the layer above, adding or narrowing FeatureSpecs.
- **Override** FeatureSpec value ranges to be more specific.
- Carry a `_scope` attribute declaring its applicability.

This means that `concepts.formal_functions.classical.Antecedent` is a
subclass of `concepts.formal_functions.beginning.Antecedent` (or of a
universal `BeginningFunction`), with classical-specific feature constraints
added.

> **QUESTION FOR TEAM**: Is the inheritance approach correct here, or should
> style-specific layers be *compositions* (a universal Antecedent + a style
> configuration object)?  Inheritance is natural for "is-a" relations;
> composition is better if the same concept can appear in multiple style
> contexts with different configurations simultaneously.

### 4.6 The Feature Hierarchy (Bottom-Up)

Atomic features are Python classes that act as functions:

```python
class CadenceStrength(Feature):
    """Measures the strength of a cadential pattern.

    Returns a value on the ordinal scale:
    PAC > IAC > HC > DC > EC > none
    """
    domain = MusicalDomain.HARMONY
    return_type = CadenceType  # an enum

    def __call__(self, musical_object: MusicalObject) -> CadenceType:
        # Operationalization -- calls into music21, partitura, etc.
        ...
```

Features compose into FeatureSpecs within concept definitions.  The
bottom-up modelling work will populate the `concepts/features/` subpackage
over the coming year+.

---

## 5. Downstream Components and Interfaces

### 5.1 EBNF Grammar (Interface: `standard/grammar.py`)

**Current state**: The grammar is manually authored and the parser is
auto-generated from it.

**Two options going forward**:

**Option E1 -- Grammar generated from Python model**:
A script traverses all `FancyStrEnum` members (canonical names + aliases) and
generates the relevant EBNF production rules.  The structural rules (Label,
FormLabel, MaterialBrackets, etc.) remain manually maintained but the vocabulary
rules (`SpecificFunction`, `FormalType`, `Unit`) are generated.

- Pro: guarantees vocabulary sync; a new term added to the enum immediately
  appears in the grammar.
- Con: the grammar's structure still needs manual curation; the generated parts
  must be clearly delimited.

**Option E2 -- Grammar validated against Python model**:
The grammar remains manually authored but CI checks verify that every enum
member (and alias) appears in the grammar, and every grammar terminal maps to
an enum member.

- Pro: simpler; preserves the grammar as a human-readable specification.
- Con: requires discipline; two places to update.

**Recommendation**: **Option E1 for vocabulary rules, manual for structural
rules**, with a CI check that the generated grammar round-trips correctly
through the parser.

### 5.2 OWL Ontology (Interface: `ontology/owl_export.py`)

**Goal**: The class hierarchy in Python produces an isomorphic OWL class
hierarchy.  OWL-specific constructs (properties with domain/range, restrictions,
SWRL rules) are encoded as Python class attributes and exported.

**Architecture**:

```
Python concept class hierarchy
    |
    v
owl_export.py  ──>  form_ontology.owl  (RDF/XML or Turtle)
    |                     |
    |                     v
    |              pyLODE  ──>  ontology reference HTML
    |
    v
owl_import.py  <──  (validation: does the OWL match Python?)
```

**Key mappings**:

| Python | OWL |
|--------|-----|
| Concept class | `owl:Class` |
| Class inheritance | `rdfs:subClassOf` |
| `_abbreviations` | `skos:altLabel` |
| Class docstring (formal section) | `rdfs:comment`, `skos:definition` |
| `_defining_features` | `owl:Restriction` (someValuesFrom/allValuesFrom) |
| Feature class | `owl:ObjectProperty` or `owl:DatatypeProperty` |
| `domain`/`return_type` | `rdfs:domain`/`rdfs:range` |
| Enum members | `owl:NamedIndividual` (if needed) or `skos:Concept` |

> **QUESTION FOR TEAM**: Should we maintain a single monolithic OWL file, or
> split into modular ontologies (one per metaconcept family) that import each
> other?  Modular is more maintainable and allows independent loading, but
> requires careful namespace management.

### 5.3 Documentation Homepage (Interface: `docs/`)

**Current state**: Quarto renders the wiki submodule into a static site.

**Proposed changes**:

1. **Keep Quarto** as the rendering engine (it handles markdown, Jupyter
   notebooks, cross-references, and bibliography well).
2. **Replace** the wiki submodule approach with a model where:
   - Auto-generated pages (vocabulary tables, vignette stubs, concept
     reference) are produced by `musicalform`'s doc bridge and committed
     to the guidelines repo.
   - Manually curated content (tutorials, how-tos, explanations) remains
     in the wiki or moves to the guidelines repo directly.
3. **Vignette workflow**: Each concept gets a vignette directory containing:
   - `_generated.md` -- auto-generated stub with formal definition, hierarchy
     position, abbreviations, links (regenerated on every release; never
     manually edited).
   - `content.md` -- manually curated musicological discussion, examples,
     figures (created once as a stub, then edited by domain experts).
   - The final vignette page includes both via Quarto's `include` mechanism.

> **QUESTION FOR TEAM**: Should we keep the wiki submodule for browser-editable
> content, or move everything into the guidelines repo proper?
>
> **Option D1 -- Keep wiki submodule**: Non-technical contributors edit in the
> browser; a CI step updates the submodule and rebuilds.  Friction: submodule
> update is a manual step; merge conflicts possible.
>
> **Option D2 -- Direct editing in repo**: Contributors edit markdown directly
> via GitHub's web editor or PRs.  Friction: slightly less discoverable than
> the wiki; requires basic git knowledge.
>
> **Option D3 -- Hybrid**: Generated content lives in the repo; manually curated
> content stays in the wiki.  Risk: split-brain.
>
> **Recommendation**: Option D2 for simplicity and consistency, with clear
> `CONTRIBUTING.md` instructions.  The wiki can remain as a staging area for
> rough notes, but the authoritative content lives in the repo.

### 5.4 Vocabulary Management and Visualization

**Goal**: A way to view the concept hierarchy as a graph, filter by metaconcept
family, inspect definitions, and (potentially) manipulate relations.

**Proposed approach** (layered, build incrementally):

1. **Phase 1 -- Static exports** (immediate):
   - `VocabularyRegistry.to_dataframe()` produces the table currently in
     `Vocabulary.ipynb`, replacing it with an auto-generated CSV/markdown.
   - A Graphviz DOT export produces a static hierarchy diagram for the docs.

2. **Phase 2 -- Interactive notebook** (short-term):
   - A Jupyter notebook using `pyvis` or `plotly` renders an interactive graph
     from the registry.  Can be hosted on the Quarto site.

3. **Phase 3 -- Dedicated GUI** (medium-term, if needed):
   - A lightweight web app (e.g., Streamlit, Panel, or a custom Flask app)
     providing search, filter, graph navigation, and potentially inline
     editing of concept properties.

> **QUESTION FOR TEAM**: How important is in-browser editing of the model
> graph?  If it is a must-have, it significantly impacts architecture (needs
> a server, persistence layer, conflict resolution).  If read-only
> visualization suffices for now, Phases 1--2 cover the need.

### 5.5 Annotation Validation Pipeline (Interface: `cli/validate.py`)

**Current state**: The CLI validates individual labels and TiLiA JSON files
against the EBNF grammar.

**Proposed expansion**:

```
annotation_pilot repo
    |
    v
musicalform validate -d /path/to/pilot  (existing)
    |
    v
Validation Report CSV
    |
    +--> Syntactic validity (grammar parse: pass/fail)
    +--> Semantic validity (object construction: pass/fail)  [existing]
    +--> Constraint violations (new: FeatureSpec checks)
    +--> Version compatibility (new: which standard version?)
    +--> Suggested migrations (new: old label -> current label)
```

### 5.6 Nextcloud Vocab Spreadsheet (Deprecation Path)

The spreadsheet has served its purpose as a low-barrier entry point.  Going
forward:

1. **Freeze** the spreadsheet at its current state.
2. **Import** all non-deprecated rows into the Python model (enum members +
   concept class stubs).
3. **Replace** the `Vocabulary.ipynb` with an auto-generated markdown table
   produced by the doc bridge.
4. **Archive** the spreadsheet with a note pointing to the Python model.

> **QUESTION FOR TEAM**: Are there active users of the spreadsheet who would
> be disrupted by this transition?  If so, we can maintain a read-only CSV
> export as a transitional measure.

---

## 6. Collaborative Workflow and Version Management

### 6.1 The Modelling Iteration Cycle

```
                    +---------+
                    | PROPOSE |   (branch: feature/xxx or model/xxx)
                    +----+----+
                         |
                         v
                    +---------+
                    | DEVELOP |   modify Python model, add tests
                    +----+----+
                         |
                         v
                    +---------+
                    |  CHECK  |   CI: lint, test, consistency checks
                    +----+----+   (grammar sync, OWL sync, vignette stubs)
                         |
                  pass    |    fail
                  +-------+-------+
                  |               |
                  v               v
            +---------+     +---------+
            | REVIEW  |     |   FIX   |
            | (human) |     +----+----+
            +----+----+          |
                 |               v
                 |          (back to CHECK)
                 v
            +---------+
            |  MERGE  |   -> development branch
            +----+----+
                 |
                 v
            +---------+
            | RELEASE |   version bump, tag, rebuild docs,
            +----+----+   regenerate OWL, update guidelines site
                 |
                 v
            +---------+
            |VALIDATE |   run against annotation_pilot
            +---------+
```

### 6.2 Branch Strategy

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Production releases only | Requires PR + 2 approvals |
| `development` | Integration branch; always consistent | Requires PR + CI pass |
| `model/*` | Model changes (new concepts, hierarchy changes) | PR to development |
| `standard/*` | Annotation standard changes (grammar, parsing) | PR to development |
| `docs/*` | Documentation-only changes | PR to development |
| `fix/*` | Bug fixes | PR to development |

### 6.3 Version Numbering

A single version number applies to the entire model ecosystem.

**Proposed scheme**: Semantic Versioning with domain-specific meaning:

| Increment | When |
|-----------|------|
| **Major** (e.g., 1.0.0 -> 2.0.0) | Breaking changes to the annotation standard that invalidate existing annotations without a migration path |
| **Minor** (e.g., 0.1.0 -> 0.2.0) | New concepts, new features, new metaconcept families; non-breaking additions to the standard |
| **Patch** (e.g., 0.1.0 -> 0.1.1) | Bug fixes, documentation improvements, clarifications that do not change the model |

**Version alignment**: The `musicalform` library, the EBNF grammar, the OWL
ontology, and the documentation homepage all carry the same version number.
Release-please (already configured) manages this in the library; the other
artifacts are regenerated and tagged as part of the release workflow.

### 6.4 CI Consistency Checks

The following checks run on every PR to `development`:

| Check | What it verifies |
|-------|-----------------|
| `test-unit` | All pytest tests pass |
| `test-integration` | End-to-end: random label generation -> parse -> object -> serialize -> re-parse |
| `check-grammar-sync` | Every enum member/alias appears in the EBNF grammar and vice versa |
| `check-owl-sync` | The generated OWL is structurally equivalent to the committed OWL |
| `check-vignette-stubs` | Every concept has a vignette directory with at least a generated stub |
| `check-vocab-table` | The generated vocab table matches the committed table |
| `lint` | black, isort, flake8, mypy |

### 6.5 The Human Review Stage

For model changes (PRs to `development` from `model/*` branches):

1. The PR description must include a **Model Change Summary** using a template:
   - What concepts were added/modified/removed
   - What metaconcept families are affected
   - What downstream artifacts need updating
   - Whether existing annotations are affected
2. At least **two project members** must approve, ideally from different
   sub-teams.
3. The review explicitly checks whether the musicological definitions
   (docstrings, vignette content) are accurate and reflect the group's
   consensus.

---

## 7. Tooling Recommendations

### 7.1 Core Python Stack

| Package | Purpose | Maturity / Risk |
|---------|---------|-----------------|
| **rdflib** (7.6.0) | RDF foundation: parse/serialize OWL, SPARQL queries | Very active; multi-maintainer; very low risk |
| **owlready2** (0.50) | OWL semantics: class manipulation, reasoning | Active; single maintainer; medium risk |
| **pySHACL** | SHACL validation of RDF graphs | Active; RDFLib org; low risk |
| **pyLODE** (3.4.2) | HTML documentation from OWL | Active; RDFLib org; low risk |
| **OWL-RL** | Lightweight OWL reasoning (no Java) | Active; RDFLib org; low risk |
| **skosify** | SKOS vocabulary validation | Maintained; institutional; low-medium risk |
| **DHParser** (1.8.3+) | EBNF -> parser generation | Current dependency; working |
| **pandas** | Data manipulation (validation reports) | Current dependency; ubiquitous |

> **QUESTION FOR TEAM**: The owlready2 single-maintainer risk.  Mitigation
> options:
>
> **M1**: Use owlready2 only for reasoning; use rdflib for all I/O.  If
> owlready2 is abandoned, reasoning can be replaced with OWL-RL or a Java
> reasoner.
>
> **M2**: Use rdflib exclusively and encode OWL semantics manually.  More work
> upfront; no reasoning out-of-the-box.
>
> **M3**: Use owlready2 now, monitor maintenance, plan migration if needed.
> Pragmatic, but requires vigilance.
>
> **Recommendation**: M1 -- use owlready2 behind an abstraction layer
> (`ontology/` subpackage) so it can be swapped if necessary.

### 7.2 Visualization

| Phase | Tool | Output |
|-------|------|--------|
| Immediate | Graphviz via `rdflib` + `pydot` | Static SVG/PNG for docs |
| Short-term | Mermaid diagrams (generated) | Inline in Quarto docs |
| Medium-term | `plotly` or `pyvis` | Interactive HTML embeds |

### 7.3 Documentation

| Component | Tool | Notes |
|-----------|------|-------|
| Static site | **Quarto** (current) | Supports markdown, Jupyter, cross-refs, bibliography |
| API reference | **Sphinx** or **mkdocstrings** | For Python API docs specifically |
| Ontology reference | **pyLODE** | Standalone HTML from OWL |

> **QUESTION FOR TEAM**: Should the Python API docs be hosted separately from
> the guidelines site, or integrated into it?  Quarto can render Sphinx output
> via includes, but it is not seamless.

---

## 8. Migration Path

### Phase 0: Foundation (Weeks 1--3)

**Goal**: Restructure the `musicalform` library without changing functionality.

1. Reorganize into the proposed package structure (Section 4.2).
2. Move enums into `vocabulary/` with one module per enum family.
3. Move `core.py` domain classes into `standard/label.py` and
   `standard/parsing.py`.
4. Create `vocabulary/registry.py` with a basic `VocabularyRegistry`.
5. Add a `__version__` that matches the grammar's stated version.
6. Expand test coverage to include end-to-end parsing.
7. Ensure all existing functionality still works.

### Phase 1: Vocabulary Consolidation (Weeks 3--6)

**Goal**: Establish the Python model as the single source of truth for
vocabulary.

1. Audit the vocab spreadsheet, the EBNF grammar, and the Python enums:
   produce a three-way diff showing what is in each but not the others.
2. With human review, decide the canonical status of each term.
3. Update the Python enums to reflect the canonical vocabulary.
4. Implement grammar generation (Option E1) for vocabulary rules.
5. Replace `Vocabulary.ipynb` with a generated table.
6. Add CI checks for grammar-vocabulary sync.

### Phase 2: Concept Hierarchy (Weeks 6--12)

**Goal**: Introduce the concept class hierarchy and metaconcept framework.

1. Define the `Metaconcept`, `Concept`, `Feature`, `FeatureSpec` base classes.
2. Create concept classes for all existing `SpecificFunctionName` members,
   with structured docstrings and basic `_defining_features`.
3. Establish the formal_functions hierarchy (Beginning, Middle, End).
4. Create concept classes for all existing `MainType` members.
5. Wire the `VocabularyRegistry` to index both enums and classes.
6. Add tests verifying hierarchy consistency.

### Phase 3: Ontology Bridge (Weeks 10--14, overlapping with Phase 2)

**Goal**: Generate OWL from Python and validate round-trip consistency.

1. Implement `owl_export.py` using rdflib (and optionally owlready2).
2. Generate a new `form_ontology.owl` from the Python model.
3. Implement `owl_import.py` for validation.
4. Add the `check-owl-sync` CI step.
5. Generate first pyLODE HTML documentation.

### Phase 4: Documentation Integration (Weeks 12--16)

**Goal**: Auto-generated + manually curated documentation pipeline.

1. Implement `vignette_stubs.py`: generate a stub directory for every concept.
2. Implement `vocab_table.py`: replace the notebook.
3. Update `_quarto.yml` to include generated content.
4. Create `CONTRIBUTING.md` with instructions for editing vignettes.
5. Establish the release workflow that rebuilds the guidelines site.
6. Decide the future of the wiki submodule.

### Phase 5: Validation Pipeline (Weeks 14--18)

**Goal**: Continuous validation against the annotation pilot corpus.

1. Expand `validate.py` with version-aware parsing.
2. Implement label migration logic (old abbreviation -> current).
3. Run validation against the full annotation pilot corpus.
4. Produce a baseline validation report.
5. Begin the dialectic process: identify labels that the grammar rejects
   but should accept (or vice versa); iterate on the model.

### Phase 6: Feature Modelling (Ongoing, from Week 16)

**Goal**: Bottom-up feature definitions meeting top-down metaconcept specs.

This is the long-term research work.  The architecture supports it; the
content is driven by the musicological research.

---

## 9. Open Questions Requiring Human Decision

These are collected from throughout the document.  Each must be resolved before
the relevant phase can proceed.

### Q1. Terminology (Section 4.1)

> Do `Metaconcept` / `Concept` / `Feature` / `FeatureSpec` work as names?
> Do they align with how the team thinks about the model?

### Q2. Enum-Class Coupling (Section 4.4)

> How tightly should FancyStrEnum members be coupled to Concept classes?
> (Options A/B/C)

### Q3. Style-Layer Architecture (Section 4.5)

> Should style-specific concepts be Python subclasses (inheritance) or
> compositions (base concept + style configuration)?

### Q4. OWL Modularity (Section 5.2)

> Single monolithic OWL file or modular ontologies per metaconcept family?

### Q5. Wiki Submodule Future (Section 5.3)

> Keep the wiki submodule for browser editing, move everything to the repo,
> or hybrid? (Options D1/D2/D3)

### Q6. Vocabulary Visualization Scope (Section 5.4)

> Is read-only visualization sufficient, or is in-browser model editing
> required?

### Q7. Spreadsheet Deprecation (Section 5.6)

> Are there active spreadsheet users who need a transition period?

### Q8. owlready2 Risk Mitigation (Section 7.1)

> Use owlready2 behind abstraction, use rdflib-only, or pragmatic adoption?
> (Options M1/M2/M3)

### Q9. API Documentation Hosting (Section 7.3)

> Integrated into the Quarto guidelines site or separate?

### Q10. Grammar Generation vs. Validation (Section 5.1)

> Generate vocabulary rules from Python, or manually maintain the grammar
> and validate sync? (Options E1/E2)

### Q11. Concept Definition Content

> This is the big one: the architecture provides the *containers* for concept
> definitions (docstrings, FeatureSpecs, vignettes), but the *content* must
> come from the project team.  What is the process for collaboratively writing
> and reviewing concept definitions?  Should there be a dedicated "definition
> sprint" for each metaconcept family, or should definitions accrete
> organically?

### Q12. Relations as First-Class Metaconcept

> The current standard encodes MaterialRelations.  The spec mentions
> generalizing to a `Relations` superclass.  What other relation types are
> anticipated?  Temporal relations (overlap, adjacency)?  Similarity relations?
> This affects the concept hierarchy design.

### Q13. Integration with External Ontologies

> To what extent should CIDOC CRM and IFLA LRM classes appear in the Python
> model?  Options:
> - Import their OWL files and reference them via URIs only (loose coupling).
> - Create Python wrapper classes for the relevant CRM/LRM classes (tight
>   coupling).
> - Define our own classes that are *mapped to* CRM/LRM via `owl:equivalentClass`
>   or `rdfs:subClassOf` (moderate coupling).

---

## Appendix A: Component Dependency Graph

```
                    +-----------------------+
                    |   musicalform (Python) |
                    |   [source of truth]    |
                    +-----------+-----------+
                                |
          +----------+----------+----------+-----------+
          |          |          |          |           |
          v          v          v          v           v
      +-------+  +------+  +------+  +--------+  +--------+
      | EBNF  |  | OWL  |  | Docs |  | Vocab  |  | Valid. |
      |grammar|  |ontol.|  | site |  | tables |  |pipeline|
      +---+---+  +--+---+  +--+---+  +--------+  +----+---+
          |          |         |                        |
          v          v         v                        v
      +-------+  +------+  +------+              +-----------+
      |DHParser|  |pyLODE|  |Quarto|              |annot_pilot|
      |parser  |  | HTML |  | HTML |              |  reports  |
      +-------+  +------+  +------+              +-----------+
```

## Appendix B: Existing File Mapping to Proposed Structure

| Current location | Proposed location | Action |
|-----------------|-------------------|--------|
| `musicalform/src/musicalform/enums.py` | `vocabulary/_base.py`, `vocabulary/functions.py`, `vocabulary/types.py`, etc. | Split by family |
| `musicalform/src/musicalform/core.py` | `standard/label.py`, `standard/parsing.py`, `concepts/` | Split by concern |
| `musicalform/src/musicalform/utils.py` | `utils.py` (unchanged) | Keep |
| `musicalform/src/musicalform/cli/validate.py` | `cli/validate.py` (expanded) | Extend |
| `grammar/lcma_standard.ebnf` | Remains; also generated/validated from Python | Bridge via `standard/grammar.py` |
| `grammar/lcma_standardParser.py` | Moves into the musicalform library | Already effectively there via cli/ |
| `ontology/protege/form_ontology.owl` | Regenerated from Python model | Archive old version |
| `data/Form vocabulary.csv` | Generated from `VocabularyRegistry` | Archive old version |
| `Vocabulary.ipynb` | Replaced by generated markdown table | Archive |
| `wiki/vignettes/*.md` | `docs/vignettes/<concept>/content.md` + generated stubs | Restructure |
| `wiki/*.md` | Remains or moves to repo root | TBD (Q5) |

## Appendix C: Key Interface Contracts

### C1. VocabularyRegistry API (minimum)

```python
class ConceptEntry:
    canonical_name: str
    abbreviations: tuple[str, ...]
    aliases: tuple[str, ...]
    enum_class: type[FancyStrEnum]
    enum_member: FancyStrEnum
    concept_class: type[Concept] | None  # None during migration
    metaconcept: str
    hierarchical_level: str | None
    parent: str | None
    children: tuple[str, ...]

class VocabularyRegistry:
    def lookup(self, term: str) -> ConceptEntry
    def all_entries(self) -> list[ConceptEntry]
    def by_metaconcept(self, name: str) -> list[ConceptEntry]
    def by_level(self, level: str) -> list[ConceptEntry]
    def hierarchy_roots(self) -> list[ConceptEntry]
    def diff(self, other: VocabularyRegistry) -> VocabDiff
    def to_dataframe(self) -> pd.DataFrame
    def to_skos(self) -> rdflib.Graph
    def to_dot(self) -> str  # Graphviz DOT
    def validate_ebnf(self, ebnf_path: Path) -> list[SyncIssue]
```

### C2. OWL Export Contract

```python
def export_owl(
    registry: VocabularyRegistry,
    concept_classes: list[type[Concept]],
    base_uri: str = "https://musicalform.github.io/ontology/",
    format: str = "xml",  # or "turtle", "json-ld"
) -> rdflib.Graph
```

### C3. Vignette Stub Contract

Each generated stub contains at minimum:

```markdown
---
title: "{concept.canonical_name}"
generated: true
model_version: "0.2.0"
---

# {concept.canonical_name}

**Abbreviation(s)**: {concept.abbreviations}
**Metaconcept**: {concept.metaconcept}
**Parent**: {concept.parent}
**Hierarchical level**: {concept.hierarchical_level}

## Formal Definition

{concept.docstring.formal_section}

## Defining Features

| Feature | Required | Values |
|---------|----------|--------|
{concept.feature_table}

## Child Concepts

{concept.children_list}

## Related Concepts

{concept.related_list}

---

*This section is auto-generated from the musicalform library v{version}.
Do not edit above this line.  Curated content follows below.*

{{< include content.md >}}
```
