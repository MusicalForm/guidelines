import argparse
import json
from pprint import pprint, pformat
from typing import Tuple, Optional, List, Dict, TypeAlias, Union, Iterable, Iterator

from DHParser import RootNode
import pandas as pd

from lcma_standardParser import compile_src, compile_snippet


def parse_label(form_label: dict) -> dict:
    return form_label



def parse_tree(tree: dict) -> dict | list:
    try:
        label = tree["Label"]
    except KeyError:
        raise ValueError(tree)
    if isinstance(label, dict):
        return parse_label(label["FormLabel"])
    result = []
    for thing in label:
        match thing:
            case [":RegExp", sign]:
                result.append(sign)
            case ["OHR", OHR]:
                result.append(parse_label(OHR))
            case _:
                context = pformat(tree)
                raise ValueError(f"Encountered unknown thing: {thing!r} in:\n{context}")
    return result


def parse_file(file):
    T: Tuple[RootNode, list] = compile_src(file)
    result, errors = T
    return result


def parse_expression(exp: str, remove_whitespace: bool = True):
    if remove_whitespace:
        exp = exp.replace(" ", "")
    T: Tuple[RootNode, list] = compile_snippet(exp)
    result, errors = T
    return result


def parse_file_as(file, format):
    result = parse_file(file)
    return result.serialize(format)


def parse_expression_as(exp, format):
    result = parse_expression(exp)
    return result.serialize(format)


def parse_file_as_dict(file) -> dict:
    json_str = parse_file_as(file, "jsondict")
    tree = json.loads(json_str)
    return tree


def parse_expression_as_dict(exp: str) -> dict:
    json_str = parse_expression_as(exp, "jsondict")
    tree = json.loads(json_str)
    return tree


def parse_file_as_objects(file="test_symbol"):
    tree_dict = parse_file_as_dict(file)
    return parse_tree(tree_dict)


def parse_expression_as_objects(exp: str):
    tree_dict = parse_expression_as_dict(exp)
    # pprint(tree_dict)
    return parse_tree(tree_dict)


def parse_csv_file(csv_file: str):

    # Load the CSV file
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f"Error loading CSV file: {e}")

    # Check if 'expression' column exists
    if "expression" not in df.columns:
        raise ValueError("CSV file must contain an 'expression' column")

    # Add 'passing' and 'output' columns if they don't exist
    if "passing" not in df.columns:
        df["passing"] = False
    if "output" not in df.columns:
        df["output"] = ""

    # Iterate over expressions and test them
    for idx, row in df.iterrows():
        expression = row["expression"]
        try:
            # Try to parse the expression
            parsed_result = parse_expression_as_objects(expression)
            df.at[idx, "passing"] = True
            df.at[idx, "output"] = str(parsed_result)
        except Exception as e:
            # If parsing fails, record the error
            df.at[idx, "passing"] = False
            df.at[idx, "output"] = str(e)

    # Save the modified DataFrame back to the CSV file
    df.to_csv(csv_file, index=False)
    passing = df.passing.sum()
    failing = len(df) - passing
    print(
        f"Processed {len(df)} expressions: {passing} passed, {failing} failed. Results saved to {csv_file}"
    )


def main(
    expression: Optional[str] = None,
    txt_file: Optional[str] = None,
    csv_file: Optional[str] = None,
):
    if all(arg is None for arg in (expression, txt_file, csv_file)):
        raise ValueError("At least one argument must be provided.")
    if expression:
        parsed_expression = parse_expression_as_objects(expression)
        pprint(parsed_expression, width=40)
    if txt_file:
        parsed_file = parse_file_as_objects(txt_file)
        pprint(parsed_file, width=40)
    if csv_file:
        parse_csv_file(csv_file)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test an expression against the current grammar."
    )
    parser.add_argument("-e", "--expression", help="A string expressing a form label.")
    parser.add_argument("-f", "--file", help="A text file containing a form label.")
    parser.add_argument(
        "-c",
        "--csv",
        help="A CSV file containing at least the column 'expression'. The script will iterate over the expressions "
        "and (add and) update the columns 'passing' and 'output'. The CSV file will be modified and overwritten!",
    )
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    main(expression=args.expression, txt_file=args.file, csv_file=args.csv)


if __name__ == "__main__":
    run()
