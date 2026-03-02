import argparse
import json
from pprint import pprint
from typing import Iterator, Optional, Tuple
from warnings import warn

import pandas as pd
from DHParser import RootNode
from lcma_standardParser import compile_snippet, compile_src


# region Helper functions
def concatenate_dict_values_recursively(specs: Iterator[str | dict]) -> str:
    """Recursively concatenates dict values. Pass dict.values() iterator or some other iterator of
    strings and (nested) dicts."""
    result = ""
    for val in specs:
        if isinstance(val, str):
            result += val
        else:
            # assumes that val is dict
            result += concatenate_dict_values_recursively(val.values())
    return result


def concatenate_regex_results(name_list: list) -> str:
    """Processes a list of regEx matches and returns the result.

    Example input:
        [[':RegExp', 'n'],
         [':RegExp', 'a'],
         [':RegExp', 'm'],
         [':RegExp', 'e']]
    """
    return "".join(character for (_, character) in name_list)


# endregion Helper functions


def parse_name(name_list: list) -> str:
    return concatenate_regex_results(name_list)


def warn_about_leftover_keys(dct: dict, ignore_keys=":Text"):
    if ignore_keys:
        if isinstance(ignore_keys, str):
            ignore_keys = {ignore_keys}
        else:
            ignore_keys = set(ignore_keys)
    else:
        ignore_keys = set()
    keys = ", ".join(repr(key) for key in dct.keys() if key not in ignore_keys)
    if keys:
        msg = f"Warning: Unprocessed keys in dict: {keys}"
        warn(msg, UserWarning)


def parse_form_label(form_label: dict) -> dict:
    form_dict = form_label["Form"]
    function_label = form_dict.pop("FunctionLabel")
    type_exp = form_dict.pop("TypeExp", None)
    material_brackets = form_dict.pop("MaterialBrackets", None)
    warn_about_leftover_keys(form_dict)
    return {
        "function": function_label,
        "type": type_exp,
        "material": material_brackets,
    }


def parse_tree(tree: dict) -> dict | list:
    try:
        label = tree["Label"]
    except KeyError:
        raise ValueError(tree)
    pprint(tree, sort_dicts=False)
    name = None
    labels = []
    if "Name" in label:
        name = parse_name(label["Name"])
    if isinstance(label, dict):
        label_dict = label["FormLabel"]
        labels.append(parse_form_label(label_dict))
    else:
        for thing in label:
            match thing:
                case ["Name", name_list]:
                    name = parse_name(name_list)
                case ["FormLabel", label_dict]:
                    labels.append(parse_form_label(label_dict))
                case [":Text", _] | [":Whitespace", _]:
                    pass
                case _:
                    # context = pformat(tree)
                    msg = f"Encountered unknown thing: {thing!r}"
                    raise ValueError(msg)
                    # warn(msg, UserWarning)
    return {"name": name, "labels": labels}


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
        pprint(parsed_expression, width=40, sort_dicts=False)
    if txt_file:
        parsed_file = parse_file_as_objects(txt_file)
        pprint(parsed_file, width=40, sort_dicts=False)
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
