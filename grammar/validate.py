import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pprint import pprint
from typing import Iterator, Optional, Self, Tuple
from warnings import warn

import pandas as pd
from DHParser import RootNode
from lcma_standardParser import compile_snippet, compile_src

WARNING_NOT_ERROR = True


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


def warn_or_raise(msg: str):
    if WARNING_NOT_ERROR:
        warn(msg, UserWarning)
    else:
        raise ValueError(msg)


def check_for_unhandled_keys(dct: dict, ignore_keys=(":Text", ":Whitespace")):
    if ignore_keys:
        if isinstance(ignore_keys, str):
            ignore_keys = {ignore_keys}
        else:
            ignore_keys = set(ignore_keys)
    else:
        ignore_keys = set()
    keys = ", ".join(repr(key) for key in dct.keys() if key not in ignore_keys)
    if keys:
        warn_or_raise(f"Encountered unhandled keys: {keys!r}")


# endregion Helper functions
# region enums


class FancyStrEnum(StrEnum):
    """A StrEnum with support for abbreviation aliases and flexible instantiation.

    Features:
        * Can be instantiated from any alias: FancyStrEnum("abbr") == FancyStrEnum.abbreviation
        * list(FancyStrEnum) returns only non-aliases (canonical members)
        * FancyStrEnum.get_abbreviations() returns a mapping from names to abbreviations

    Example:
        class Vocabulary(FancyStrEnum):
            abbreviation = auto()  # assigns the name as value (lowercase per StrEnum)
            abbr = abbreviation    # alias 1
            abb = abbreviation     # alias 2
    """

    @classmethod
    def _missing_(cls, value: object) -> "FancyStrEnum | None":
        """Allow instantiation from values, including aliases.

        Args:
            value: The value or name string to look up.

        Returns:
            The corresponding enum member, or None if not found.

        Raises:
            ValueError: If the value does not match any member or alias.
        """
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in cls.__members__:
                name = cls.__members__[lower_value]
                return cls(name)
        abbrv = cls.get_abbreviations(string=True)
        raise ValueError(
            f"'{value}' is not a valid {cls.__name__}. Available values are: {abbrv}"
        )

    @classmethod
    def get_abbreviations(cls, string: bool = False) -> dict[str, list[str]] | str:
        """Returns a mapping from enum names/values to abbreviated alias values.

        Args:
            string: If True, return a formatted string instead of a dict.

        Returns:
            A dict mapping canonical names to lists of aliases, or a formatted string.
        """
        name2values: dict[str, list[str]] = defaultdict(list)
        for value, name in cls.__members__.items():
            name2values[name].append(value)
        abbreviations: dict[str, list[str]] = {}
        for name, values in name2values.items():
            # Sort by length descending, skip the first (canonical name)
            abbreviations[name] = sorted(values, key=lambda x: len(x), reverse=True)[1:]
        if not string:
            return abbreviations
        str_components = []
        for name, values in abbreviations.items():
            if not values:
                str_components.append(name)
                continue
            abbrev_str = ", ".join(values)
            str_components.append(f"{name} ({abbrev_str})")
        return ", ".join(str_components)

    def __repr__(self) -> str:
        return f'"{self.name}"'

    def __str__(self) -> str:
        return self.name


class SpecificFunctionName(FancyStrEnum):
    antecedent = auto()
    ant = antecedent
    after_the_end = auto()
    ate = after_the_end
    basic_idea = auto()
    bi = basic_idea
    cadential_subphrase = auto()
    cad = cadential_subphrase
    compound_basic_idea = auto()
    cbi = compound_basic_idea
    codetta = auto()
    cdta = codetta
    contrasting_idea = auto()
    ci = contrasting_idea
    closing_theme = auto()
    cls = closing_theme
    coda = auto()
    consequent = auto()
    cons = consequent
    continuation_idea = auto()
    conti = continuation_idea
    continuation = continuation_idea
    cont = continuation
    development_section = auto()
    dev = development_section
    essential_expositional_closure = auto()
    eec = essential_expositional_closure
    essential_sonata_closure = auto()
    esc = essential_sonata_closure
    exposition = auto()
    exp = exposition
    fragmentation = auto()
    frag = fragmentation
    introduction = auto()
    intro = introduction
    lead_in = auto()
    lin = lead_in
    model = auto()
    mod = model
    movement = auto()
    mvt = movement
    postcadential = auto()
    pcad = postcadential
    presentation = auto()
    pres = presentation
    primary_theme_zone = auto()
    ptz = primary_theme_zone
    primary_theme = primary_theme_zone
    pt = primary_theme
    recapitulation = auto()
    recap = recapitulation
    ritornello = auto()
    rit = ritornello
    retransition = auto()
    rtr = retransition
    secondary_theme_zone = auto()
    stz = secondary_theme_zone
    secondary_theme = secondary_theme_zone
    st = secondary_theme
    sequence = auto()
    seq = sequence
    transition = auto()
    tr = transition


class UnitName(FancyStrEnum):
    unit = auto()
    x = unit
    part = auto()
    section = auto()
    phrase = auto()
    sub_phrase = auto()
    idea = auto()
    work = auto()
    movement = auto()
    zone = auto()
    theme = auto()
    album = auto()
    song = auto()
    cycle = auto()
    group = auto()


class FunctionSpecificity(FancyStrEnum):
    specific = auto()
    generic = auto()


# endregion enums
# region dataclasses


@dataclass
class FormalFunction:
    name: SpecificFunctionName | UnitName
    cardinality: Optional[int] = None  # e.g. 1st unit => 1
    notional: bool = False  # "function"
    crossing_rightward: bool = False  # function /

    @property
    def specificity(self) -> FunctionSpecificity:
        if isinstance(self.name, SpecificFunctionName):
            return FunctionSpecificity.specific
        elif isinstance(self.name, UnitName):
            return FunctionSpecificity.generic
        else:
            raise ValueError(f"Unexpected function name: {self.name!r}")


@dataclass
class FunctionalTransformation:
    source: FormalFunction
    target: FormalFunction


@dataclass
class FormalType:
    name: str


@dataclass
class MaterialReferences:
    references: list[str]


@dataclass
class ShorthandReference:
    reference: str


@dataclass
class FormLabel:
    function: FormalFunction
    type: Optional[FormalType] = None
    material: Optional[MaterialReferences] = None

    @classmethod
    def from_parse(cls, parse: dict):
        form_dict = parse["Form"]
        function, shorthand = parse_function_label(form_dict.pop("FunctionLabel"))
        type_exp = form_dict.pop("TypeExp", None)
        material_brackets = form_dict.pop("MaterialBrackets", None)
        check_for_unhandled_keys(form_dict)
        cls(function=function, type=type_exp, material=material_brackets)


@dataclass
class AnnotationLabel:
    name: Optional[str]
    form_labels: field(default_factory=list)

    @classmethod
    def from_parse(cls, parse: dict) -> Self:
        try:
            label = parse["Label"]
        except KeyError:
            raise ValueError(parse)
        pprint(parse, sort_dicts=False)
        name = None
        labels = []
        if "Name" in label:
            name = parse_name(label["Name"])
        if isinstance(label, dict):
            label_dict = label["FormLabel"]
            labels.append(FormLabel.from_parse(label_dict))
        else:
            for thing in label:
                match thing:
                    case ["Name", name_list]:
                        name = parse_name(name_list)
                    case ["FormLabel", label_dict]:
                        labels.append(FormLabel.from_parse(label_dict))
                    case [":Text", _] | [":Whitespace", _]:
                        pass
                    case _:
                        warn_or_raise(f"Encountered unknown thing: {thing!r}")
        return cls(name=name, form_labels=labels)


# endregion dataclasses
# region parsing functions
def parse_generic_function(generic_function: dict) -> str:
    raise NotImplementedError


def parse_function_name(
    function_name: dict,
) -> Tuple[SpecificFunctionName | UnitName, Optional[int]]:
    if "SpecificFunction" in function_name:
        return SpecificFunctionName(function_name["SpecificFunction"]), None
    elif "GenericFunction" in function_name:
        generic_function = function_name["GenericFunction"]
        cardinality_str = generic_function.pop("Cardinality")
        cardinality = int(cardinality_str[0])
        name = UnitName(generic_function.pop("Unit"))
        check_for_unhandled_keys(generic_function)
        return name, cardinality
    else:
        warn_or_raise(f"Encountered unknown function type: {function_name!r}")
        return None, None


def parse_function(
    function: dict | list,
) -> Tuple[SpecificFunctionName | UnitName, Optional[int], bool]:
    """Can be either function or "function" (for notional function attribution)."""
    if isinstance(function, dict):
        function_name = function.pop("FunctionName")
        check_for_unhandled_keys(function)
        name, cardinality = parse_function_name(function_name)
        return name, cardinality, False
    for thing in function:
        # 3 things: '"', <FunctionName>, '"'
        match thing:
            case ["FunctionName", function_name]:
                name, cardinality = parse_function_name(function_name)
            case [":Text", '"']:
                pass
            case _:
                warn_or_raise(f"Encountered unknown thing in function: {thing!r}")
    return name, cardinality, True


def parse_function_expr(
    function_expr: dict,
) -> Tuple[FormalFunction, Optional[ShorthandReference]]:
    function = function_expr.pop("Function")
    name, cardinality, notional = parse_function(function)
    formal_function = FormalFunction(
        name=name, cardinality=cardinality, notional=notional
    )

    shorthand = function_expr.pop("Shorthand", "")
    shorthand_ref = ShorthandReference(reference=shorthand) if shorthand else None
    check_for_unhandled_keys(function_expr)
    return formal_function, shorthand_ref


def parse_function_label(
    parse: dict | list,
) -> Tuple[FormalFunction | FunctionalTransformation, Optional[ShorthandReference]]:
    if isinstance(parse, dict):
        function_expr = parse.pop("FunctionExpr")
        check_for_unhandled_keys(parse)
        return parse_function_expr(function_expr)
    functions, shorthands = [], []
    operator = None
    for thing in parse:
        match thing:
            case ["FunctionExpr", function_expr]:
                function, shorthand = parse_function_expr(function_expr)
                functions.append(function)
                shorthands.append(shorthand)
            case ["Combinator", combinator]:
                operator = combinator
            case _:
                warn_or_raise(f"Encountered unknown thing in function label: {thing!r}")
    if len(functions) == 1:
        function = functions[0]
        assert operator == "/"
        function.crossing_rightward = True
        return function, shorthands[0]
    # interpret as transformation from first to second function
    assert len(functions) == 2
    assert operator == ">"
    transformation = FunctionalTransformation(source=functions[0], target=functions[1])
    return transformation, ShorthandReference(
        ", ".join(str(s) for s in shorthands if s)
    )


def parse_name(name_list: list) -> str:
    return concatenate_regex_results(name_list)


def parse_tree(tree: dict) -> dict | list:
    return AnnotationLabel.from_parse(tree)


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


# endregion parsing functions
# region argument dispatch


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


# endregion argument dispatch

if __name__ == "__main__":
    run()
