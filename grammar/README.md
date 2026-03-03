# LCMA Form Annotation Standard Specification

This document specifies how annotation labels need to be structure in order to conform to the syntax devised
at the Linz Computational Music Analysis (LCMA) group. The syntax is being encoded in Extended Backus-Naur Form (EBNF)
and [visualised](index.md) using railroad diagrams generated on https://www.bottlecaps.de/rr/ui .
The grammar is contained in the file [lcma_standard.ebnf](lcma_standard.ebnf) in this directory.

## Setup

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Validator

The validator (`validate.py`) checks whether form-label expressions conform to the LCMA grammar.
It can be invoked in several ways, summarized in the table below.

### Options at a glance

| Flag | Long form | Argument | Description |
|------|-----------|----------|-------------|
| `-e` | `--expression` | `STRING` | Validate a single expression passed on the command line |
| `-f` | `--file` | `FILE` | Validate a single expression contained in a text file |
| `-c` | `--csv` | `FILE` | Validate all expressions in a CSV file (must have an `expression` column) |
| `-j` | `--json` | `FILE` | Extract and validate expressions from a structured JSON file |
| `-d` | `--directory` | `DIR` | Recursively scan a directory for JSON files and validate all of them |
| `-o` | `--output` | `PATH` | Control where report CSV files are written (used with `-j` or `-d`) |
| `-v` | `--verbose` | — | Print information about skipped files (e.g., JSON files without the expected format) |

### Validating a single expression (`-e`)

Parse and validate one expression directly from the command line:

```bash
python validate.py -e "ant"
python validate.py -e "theme|pd"
```

### Validating an expression from a text file (`-f`)

Parse a text file containing a single expression:

```bash
python validate.py -f test_symbol
```

### Validating expressions from a CSV file (`-c`)

The CSV file must contain at least a column named `expression`. The validator iterates over all
rows, parses each expression, and adds/updates the columns `passing` (bool) and `output`
(parse result or error message). The CSV file is **modified in place**.

```bash
python validate.py -c test_cases.csv
```

### Validating expressions from a JSON file (`-j`)

Accepts a JSON file whose first top-level key is `"timelines"`. The validator extracts components
from all timelines of `kind: HIERARCHY_TIMELINE`, collecting each component's `label` as the
expression to validate. The resulting report CSV contains:

1. **Core columns:** `passing`, `expression`, `output`, `description`
2. **Component properties:** all fields from each component object (e.g., `start`, `end`, `level`, `start_measure`, …)
3. **Timeline properties:** the parent timeline's properties, prefixed with `timeline.` (e.g., `timeline.name`, `timeline.ordinal`)
4. **Media metadata:** the file's top-level `media_metadata`, prefixed with `media_metadata.` (e.g., `media_metadata.composer`)

By default, the report is written next to the JSON file with the suffix `.report.csv`:

```bash
python validate.py -j test_files/D790ländler03.json
# creates test_files/D790ländler03.report.csv
```

Use `-o` to redirect the output (see below).

### Validating a directory of JSON files (`-d`)

Recursively scans a directory for `.json` files with the expected format and processes each one.
Files that do not match (no `"timelines"` key or no `HIERARCHY_TIMELINE`) are silently skipped
(use `-v` to see which files are skipped).

The behaviour depends on `-o`:

1. **Without `-o`:** each JSON file gets a sibling `.report.csv`.

   ```bash
   python validate.py -d test_files/
   ```

2. **`-o` with a directory:** reports are placed in that directory with automatic names
   (the directory is created if it does not exist).

   ```bash
   python validate.py -d test_files/ -o test_files/reports
   ```

3. **`-o` with a `.csv` or `.tsv` filepath:** all expressions from all valid JSON files are
   concatenated into a single DataFrame (with an additional `source_file` column) and validated
   together.

   ```bash
   python validate.py -d test_files/ -o all_expressions.csv
   ```

### Controlling report output (`-o`)

The `-o` flag is used together with `-j` or `-d`:

- If the path ends in `.csv` or `.tsv`, it is treated as a **file path** and used directly.
- Otherwise, it is treated as a **directory** (created automatically if needed), and report files
  are placed inside with automatic names (`<stem>.report.csv`).

```bash
# Write a single JSON's report to a specific file
python validate.py -j test_files/D790ländler03.json -o my_report.csv

# Write a single JSON's report into a directory
python validate.py -j test_files/D790ländler03.json -o reports/
```

### Verbose output (`-v`)

When using `-d`, files that lack the expected JSON format are silently skipped. Pass `-v` to print
a message for each skipped file:

```bash
python validate.py -d test_files/ -v
```

## For developers

### Pre-commit hooks

Before making changes to the validator or other Python code, install the pre-commit hooks:

```bash
pre-commit install
```

This enables automatic formatting (black, isort) and linting (flake8) checks on every commit.

### Generating railroad diagrams

To generate railroad diagrams from the EBNF grammar (https://www.bottlecaps.de/rr/ui),
you first need to remove all `~` characters from `lcma_standard.ebnf`, as the diagram generator
does not support them. You can do this via find-and-replace in your editor or on the command line:

```bash
sed 's/~//g' lcma_standard.ebnf > lcma_standard_no_tilde.ebnf
```
