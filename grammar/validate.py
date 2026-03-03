from __future__ import annotations

import argparse
import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from pprint import pprint
from typing import Iterator, Optional, Self, Set, Tuple
from warnings import warn

import pandas as pd
from DHParser import RootNode
from lcma_standardParser import compile_snippet, compile_src

VERBOSE = False


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
        warn(f"Encountered unhandled keys: {keys!r}", UserWarning)


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


class MainType(FancyStrEnum):
    hybrid1 = auto()
    hyb1 = hybrid1
    hybrid2 = auto()
    hyb2 = hybrid2
    hybrid3 = auto()
    hyb3 = hybrid3
    hybrid4 = auto()
    hyb4 = hybrid4
    period = auto()
    pd = period
    ritornello_form = auto()
    ritornello = ritornello_form
    rondo_form = auto()
    rondo = rondo_form
    sentence = auto()
    sent = sentence
    sequence = auto()
    seq = sequence
    sonata_form = auto()
    sonata = sonata_form
    unary_form = auto()
    unary = unary_form
    simple_binary = auto()
    rounded_binary = auto()
    ternary = auto()


class SubType(FancyStrEnum):
    # simple_binary
    balanced = auto()
    # ternary
    through_composed = auto()
    da_capo = auto()


MAIN_TO_SUBTYPES: dict[MainType, set[SubType]] = {
    MainType.simple_binary: {SubType.balanced},
    MainType.ternary: {SubType.through_composed, SubType.da_capo},
}


class MaterialOperator(FancyStrEnum):
    adaptation = auto()  # $adapt symbol: °
    adapt = adaptation
    augmentation = auto()  # $aug
    aug = augmentation
    combination = auto()  # $comb symbol: &
    comb = combination
    concatenation = auto()  # $conc symbol: ,
    conc = concatenation
    diminution = auto()  # $dim
    dim = diminution
    extension = auto()  # $ext symbol: +
    ext = extension
    interpolation = auto()  # $interp symbol: **
    interp = interpolation
    inversion = auto()  # $inv
    inv = inversion
    ornamentation = auto()  # $orn symbol: ~
    orn = ornamentation
    partial = auto()  # $part symbol: *
    part = partial
    repetition = auto()  # $rep symbol: !
    rep = repetition
    retrograde = auto()  # $retr
    retr = retrograde
    transposition = auto()  # $transp symbol: ^
    transp = transposition
    variation = auto()  # $var
    var = variation

    @classmethod
    def _missing_(cls, value: object):
        """Allow instantiation from symbols or aliases.

        Args:
            value: The value, symbol, or alias string to look up.

        Returns:
            The corresponding enum member, or None if not found.

        Raises:
            ValueError: If the value does not match any member, symbol, or alias.
        """
        symbol_map = {
            "°": cls.adaptation,
            "&": cls.combination,
            ",": cls.concatenation,
            "+": cls.extension,
            "**": cls.interpolation,
            "~": cls.ornamentation,
            "*": cls.partial,
            "!": cls.repetition,
            "^": cls.transposition,
        }
        if isinstance(value, str) and value in symbol_map:
            return symbol_map[value]
        return super()._missing_(value)


# endregion enums
# region classes


class FormalFunction(ABC):

    @abstractmethod
    def specificity(self) -> FunctionSpecificity:
        raise NotImplementedError


@dataclass
class SingleFunction(FormalFunction):
    name: SpecificFunctionName | UnitName
    notional: bool = False  # "function"
    crossing_rightward: bool = False  # function /

    @classmethod
    def from_name(
        cls,
        name: SpecificFunctionName | UnitName,
        notional=False,
        crossing_rightward=False,
        cardinality=None,
    ) -> SpecificFunction | GenericFunction:
        """Dispatch to the appropriate subclass based on the type of the name.
        Cardinality is only applicable to generic functions and must be None for specific functions.
        """
        if isinstance(name, SpecificFunctionName):
            if cardinality is not None:
                raise ValueError(
                    f"Cardinality is not applicable to specific functions. Got {cardinality=}"
                )
            return SpecificFunction(
                name=name, notional=notional, crossing_rightward=crossing_rightward
            )
        elif isinstance(name, UnitName):
            return GenericFunction(
                name=name,
                notional=notional,
                crossing_rightward=crossing_rightward,
                cardinality=cardinality,
            )
        else:
            raise ValueError(
                f"Name must be either SpecificFunctionName or UnitName. Got {name!r} of type {type(name)}"
            )


@dataclass
class SpecificFunction(SingleFunction):
    name: SpecificFunctionName

    @property
    def specificity(self) -> FunctionSpecificity:
        return FunctionSpecificity.specific


@dataclass
class GenericFunction(SingleFunction):
    """Inheritance only in terms of attributes, not in terms of the music-theoretical concept."""

    name: UnitName
    cardinality: Optional[int] = None  # e.g. 1st unit => 1

    @property
    def specificity(self) -> FunctionSpecificity:
        return FunctionSpecificity.generic


@dataclass
class FunctionalTransformation(FormalFunction):
    source: SpecificFunction | GenericFunction
    target: SpecificFunction | GenericFunction

    @property
    def specificity(self) -> Tuple[FunctionSpecificity, FunctionSpecificity]:
        return self.source.specificity, self.target.specificity


@dataclass
class FormalType:
    main_type: MainType
    sub_type: Optional[SubType] = None
    notional: bool = False  # "type"

    @classmethod
    def from_parse(cls, parse: Optional[dict | list]) -> Optional[FormalType]:
        if parse is None:
            return None
        if isinstance(parse, dict):
            type_name = parse.pop("FormalType")
            check_for_unhandled_keys(parse)
            main, sub = parse_type_name(type_name)
            return cls(main_type=main, sub_type=sub, notional=False)
        main, sub = None, None
        for thing in parse:
            # 3 things: '"', <TypeName>, '"'
            match thing:
                case ["FormalType", type_name]:
                    main, sub = parse_type_name(type_name)
                case [":Text", '"']:
                    pass
                case _:
                    warn(
                        f"Encountered unknown thing in formal type: {thing!r}",
                        UserWarning,
                    )
        return cls(main_type=main, sub_type=sub, notional=True)

    def __repr__(self) -> str:
        repr = f"FormalType({self.main_type}"
        if self.sub_type:
            repr += f".{self.sub_type}"
        repr += ")"
        return repr


class References(ABC):
    pass


@dataclass
class SingleReference(References):
    reference: Optional[str] = None
    operators: Set[MaterialOperator] = field(default_factory=set)

    @classmethod
    def from_parse(cls, parse: dict):
        if parse is None:
            return None
        name = parse.pop("Name", None)
        operator_chars = parse.pop("MaterialOperators", [])
        operators = parse_material_operator_chars(operator_chars)
        return cls(reference=name, operators=operators)


@dataclass
class MaterialReferences(References):
    """One or several material references, possibly with operators."""

    references: Tuple[SingleReference, ...]
    unordered: bool = False  # if True, this is considered a non-repeating set

    @classmethod
    def from_parse(
        cls, parse: Optional[list], shorthand: Optional[SingleReference]
    ) -> Optional[MaterialReferences]:
        if parse is None and shorthand is None:
            return None
        if shorthand and parse:
            raise ValueError("Shorthand and material brackets cannot be combined.")
        if shorthand:
            return cls(references=(shorthand,))
        for thing in parse:
            match thing:
                case ["MaterialPositions", positions]:
                    return parse_material_positions(positions)
                case [":Text", _] | [":Whitespace", _]:
                    pass
                case _:
                    warn(
                        f"Encountered unknown thing in material brackets: {thing!r}",
                        UserWarning,
                    )
        return None


@dataclass
class TransformationalReferences(References):
    source_references: Optional[MaterialReferences] = None
    target_references: Optional[MaterialReferences] = None

    @classmethod
    def from_parse(
        cls, parse: Optional[list], shorthand: Optional[tuple]
    ) -> Optional[TransformationalReferences | MaterialReferences]:
        if parse is None and shorthand is None:
            return None
        if parse is None and shorthand is not None:
            source_short, target_short = shorthand
            return cls(
                source_references=(
                    MaterialReferences(references=(source_short,))
                    if source_short
                    else None
                ),
                target_references=(
                    MaterialReferences(references=(target_short,))
                    if target_short
                    else None
                ),
            )
        for thing in parse:
            match thing:
                case ["MaterialPositions", positions]:
                    if shorthand is not None:
                        source_short, target_short = shorthand
                        if source_short or target_short:
                            raise ValueError(
                                "Shorthand and material brackets cannot be combined."
                            )
                    return parse_transformational_positions(positions)
                case [":Text", _] | [":Whitespace", _]:
                    pass
                case _:
                    warn(
                        f"Encountered unknown thing in material brackets: {thing!r}",
                        UserWarning,
                    )
        return None


@dataclass
class FormLabel:
    function: FormalFunction
    type: Optional[FormalType] = None
    material: Optional[MaterialReferences] = None

    @classmethod
    def from_parse(cls, parse: dict):
        form_dict = parse["Form"]
        function, shorthand = parse_function_label(form_dict.pop("FunctionLabel"))
        formal_type = FormalType.from_parse(form_dict.pop("TypeExp", None))
        material_refs = parse_material_brackets(
            parse.pop("MaterialBrackets", None),
            shorthand=shorthand,
            transformational=isinstance(function, FunctionalTransformation),
        )
        check_for_unhandled_keys(form_dict)
        return cls(function=function, type=formal_type, material=material_refs)


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
        if VERBOSE:
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
                        warn(f"Encountered unknown thing: {thing!r}", UserWarning)
        return cls(name=name, form_labels=labels)


# endregion classes
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
        name = UnitName(generic_function.pop("Unit"))

        cardinality = generic_function.pop("Cardinality", None)
        if cardinality is not None:
            # has the shape "1st", or "2nd", ... "9th"
            cardinality = int(cardinality[0])
        check_for_unhandled_keys(generic_function)
        return name, cardinality
    else:
        warn(f"Encountered unknown function type: {function_name!r}", UserWarning)
        return None, None


def parse_function(
    function: dict | list,
) -> SpecificFunction | GenericFunction:
    """Can be either function or "function" (for notional function attribution)."""
    if isinstance(function, dict):
        function_name = function.pop("FunctionName")
        check_for_unhandled_keys(function)
        name, cardinality = parse_function_name(function_name)
        return SingleFunction.from_name(
            name=name, notional=False, cardinality=cardinality
        )
    name, cardinality = None, None
    for thing in function:
        # 3 things: '"', <FunctionName>, '"'
        match thing:
            case ["FunctionName", function_name]:
                name, cardinality = parse_function_name(function_name)
            case [":Text", '"']:
                pass
            case _:
                warn(f"Encountered unknown thing in function: {thing!r}", UserWarning)
    return SingleFunction.from_name(name=name, notional=True, cardinality=cardinality)


def parse_function_expr(
    function_expr: dict,
) -> Tuple[SpecificFunction | GenericFunction, Optional[SingleReference]]:
    function = function_expr.pop("Function")
    formal_function = parse_function(function)

    shorthand = function_expr.pop("Shorthand", None)
    shorthand_ref = SingleReference.from_parse(shorthand)
    check_for_unhandled_keys(function_expr)
    return formal_function, shorthand_ref


TransformationalShorthand = Tuple[SingleReference, SingleReference]


def parse_function_label(
    parse: dict | list,
) -> (
    Tuple[FormalFunction, Optional[SingleReference]]
    | Tuple[FunctionalTransformation, TransformationalShorthand]
):
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
            case [":Text", _] | [":Whitespace", _]:
                pass
            case _:
                warn(
                    f"Encountered unknown thing in function label: {thing!r}",
                    UserWarning,
                )
    if len(functions) == 1:
        function = functions[0]
        assert operator == "/"
        function.crossing_rightward = True
        return function, shorthands[0]
    # interpret as transformation from first to second function
    assert len(functions) == 2
    assert operator == ">"
    transformation = FunctionalTransformation(source=functions[0], target=functions[1])
    return transformation, tuple(shorthands)


def parse_name(name_list: list) -> str:
    return concatenate_regex_results(name_list)


def parse_type_name(type_name: str) -> Tuple[MainType, Optional[SubType]]:
    if "." in type_name:
        main_str, sub_str = type_name.split(".", 1)
        main = MainType(main_str)
        sub = SubType(sub_str)
        if main not in MAIN_TO_SUBTYPES:
            raise ValueError(
                f"Main type {main} does not have any subtypes, but got subtype {sub}"
            )
        elif sub not in MAIN_TO_SUBTYPES[main]:
            raise ValueError(
                f"Subtype {sub} is not valid for main type {main}. "
                f"Valid subtypes are: {MAIN_TO_SUBTYPES[main]}"
            )
        return main, sub
    return MainType(type_name), None


def parse_material_operator_chars(operator_chars: list | str) -> Set[MaterialOperator]:
    """For simplicity, the standard allows for any combination of the operators [°, &, +, ~, *, !, ^].
    However, each operator is taken into account only once and ** needs to be extracted before * (although both
    should not appear at the same time in the first place).
    """
    if not operator_chars:
        return set()
    if isinstance(operator_chars, str):
        operators_string = operator_chars
    else:
        operators_string = concatenate_regex_results(operator_chars)

    # Symbol map in alphabetical order
    symbol_map = {
        "°": MaterialOperator.adaptation,
        "&": MaterialOperator.combination,
        ",": MaterialOperator.concatenation,
        "+": MaterialOperator.extension,
        "**": MaterialOperator.interpolation,
        "~": MaterialOperator.ornamentation,
        "*": MaterialOperator.partial,
        "!": MaterialOperator.repetition,
        "^": MaterialOperator.transposition,
    }

    # Sort by length descending to match ** before *
    sorted_symbols = sorted(symbol_map.keys(), key=len, reverse=True)
    pattern = "|".join(re.escape(symbol) for symbol in sorted_symbols)
    matches = re.findall(pattern, operators_string)
    return set(symbol_map[match] for match in matches)


def parse_material_concatenation(concat_list: list) -> Tuple[SingleReference, ...]:
    refs = []
    for thing in concat_list:
        match thing:
            case ["Entry", entry_dict]:
                refs.append(SingleReference.from_parse(entry_dict))
            case [":Text", _] | [":Whitespace", _]:
                pass
            case _:
                warn(
                    f"Encountered unknown thing in material concatenation: {thing!r}",
                    UserWarning,
                )
    return tuple(refs)


def parse_material_ref(material_ref: dict | list) -> MaterialReferences:
    if isinstance(material_ref, dict):
        if "Entry" in material_ref:
            entry = material_ref.pop("Entry", None)
            ref = SingleReference.from_parse(entry)
            check_for_unhandled_keys(material_ref)
            return MaterialReferences(references=(ref,))
        elif "Concatenation" in material_ref:
            refs = parse_material_concatenation(material_ref.pop("Concatenation"))
            check_for_unhandled_keys(material_ref)
            return MaterialReferences(references=refs)
    # list: bracket-wrapped or paren-wrapped
    unordered = False
    refs = ()
    for thing in material_ref:
        match thing:
            case ["Concatenation", concat_list]:
                refs = parse_material_concatenation(concat_list)
            case [":Text", "(" | ")"]:
                unordered = True
            case [":Text", _] | [":Whitespace", _]:
                pass
            case _:
                warn(
                    f"Encountered unknown thing in material ref: {thing!r}", UserWarning
                )
    return MaterialReferences(references=refs, unordered=unordered)


def parse_material_positions(
    positions: dict | list,
) -> Optional[MaterialReferences]:
    """For a single function: only a single MaterialRef without positional syntax."""
    if isinstance(positions, list):
        raise ValueError(
            "Two material positions are not allowed for a single function."
        )
    if "SourceOnly" in positions or "TargetOnly" in positions:
        raise ValueError(
            "Positional material references are not allowed for a single function."
        )
        return None
    if "MaterialRef" in positions:
        return parse_material_ref(positions["MaterialRef"])
    return None


def parse_transformational_positions(
    positions: dict | list,
) -> Optional[TransformationalReferences | MaterialReferences]:
    """For a functional transformation: disambiguate between positions and overrides."""
    if isinstance(positions, list):
        # two explicit MaterialRef positions
        refs = []
        for thing in positions:
            match thing:
                case ["MaterialRef", ref_data]:
                    refs.append(parse_material_ref(ref_data))
                case [":Text", _] | [":Whitespace", _]:
                    pass
                case _:
                    warn(
                        f"Encountered unknown thing in material positions: {thing!r}",
                        UserWarning,
                    )
        return TransformationalReferences(
            source_references=refs[0] if len(refs) > 0 else None,
            target_references=refs[1] if len(refs) > 1 else None,
        )
    if "SourceOnly" in positions:
        return TransformationalReferences(
            source_references=parse_material_ref(
                positions["SourceOnly"]["MaterialRef"]
            ),
            target_references=None,
        )
    if "TargetOnly" in positions:
        return TransformationalReferences(
            source_references=None,
            target_references=parse_material_ref(
                positions["TargetOnly"]["MaterialRef"]
            ),
        )
    if "MaterialRef" not in positions:
        return None
    material_ref = positions["MaterialRef"]
    # bare concatenation: reinterpret based on entry count
    if isinstance(material_ref, dict) and "Concatenation" in material_ref:
        entries = [
            thing for thing in material_ref["Concatenation"] if thing[0] == "Entry"
        ]
        if len(entries) == 2:
            source_single = SingleReference.from_parse(entries[0][1])
            target_single = SingleReference.from_parse(entries[1][1])
            return TransformationalReferences(
                source_references=MaterialReferences(references=(source_single,)),
                target_references=MaterialReferences(references=(target_single,)),
            )
        raise ValueError(
            f"Bare concatenation with {len(entries)} entries is not allowed "
            f"for a functional transformation."
        )
        return None
    # bracket/paren-wrapped or single entry: override to MaterialReferences
    return parse_material_ref(material_ref)


MaterialPosition = Optional[SingleReference]


def parse_material_brackets(
    material_brackets: Optional[dict | list],
    shorthand: MaterialPosition | Tuple[MaterialPosition, MaterialPosition],
    transformational: bool = False,
) -> Optional[MaterialReferences]:
    if transformational:
        return TransformationalReferences.from_parse(material_brackets, shorthand)
    else:
        return MaterialReferences.from_parse(material_brackets, shorthand)


def parse_tree(tree: dict) -> AnnotationLabel:
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
        df["passing"] = pd.Series([False] * len(df), dtype=bool)
    else:
        df["passing"] = df["passing"].astype(bool)
    if "output" not in df.columns:
        df["output"] = ""
    else:
        df["output"] = df["output"].astype(str)

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
# region JSON processing


def is_valid_json_format(data: dict) -> bool:
    """Check if a JSON dict has 'timelines' as its first top-level key."""
    if not isinstance(data, dict):
        return False
    first_key = next(iter(data), None)
    return first_key == "timelines"


def json_to_dataframe(json_path: str | Path) -> Optional[pd.DataFrame]:
    """Extract HIERARCHY_TIMELINE components from a JSON file into a DataFrame.

    Returns a DataFrame with columns: passing, expression, output, description,
    <component properties>, <timeline properties>, <media_metadata properties>.
    Returns None if the file doesn't have the expected format or no HIERARCHY_TIMELINEs.
    """
    json_path = Path(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not is_valid_json_format(data):
        return None

    media_metadata = data.get("media_metadata", {})
    hierarchy_timelines = [
        tl for tl in data.get("timelines", []) if tl.get("kind") == "HIERARCHY_TIMELINE"
    ]

    if not hierarchy_timelines:
        return None

    all_frames = []
    for tl in hierarchy_timelines:
        components = tl.get("components", [])
        if not components:
            continue

        # Normalize components into a flat DataFrame
        df_components = pd.json_normalize(components)

        # Add timeline-level properties as repeated columns (prefixed)
        tl_props = {k: v for k, v in tl.items() if k != "components"}
        for key, val in tl_props.items():
            df_components[f"timeline.{key}"] = val

        # Add media_metadata as repeated columns (prefixed)
        for key, val in media_metadata.items():
            df_components[f"media_metadata.{key}"] = val

        all_frames.append(df_components)

    if not all_frames:
        return None

    df = pd.concat(all_frames, ignore_index=True)

    # Rename 'label' to 'expression'
    if "label" in df.columns:
        df = df.rename(columns={"label": "expression"})

    # Add core columns if missing
    for col, default in [
        ("passing", False),
        ("expression", ""),
        ("output", ""),
        ("description", ""),
    ]:
        if col not in df.columns:
            df[col] = default

    # Reorder columns: core first, then component properties, then timeline, then media_metadata
    core_cols = ["passing", "expression", "output", "description"]
    comp_cols = [
        c
        for c in df.columns
        if not c.startswith("timeline.")
        and not c.startswith("media_metadata.")
        and c not in core_cols
    ]
    timeline_cols = sorted(c for c in df.columns if c.startswith("timeline."))
    metadata_cols = sorted(c for c in df.columns if c.startswith("media_metadata."))

    ordered_cols = core_cols + comp_cols + timeline_cols + metadata_cols
    df = df[ordered_cols]

    return df


def resolve_output_path(
    json_path: str | Path,
    output: Optional[str | Path] = None,
) -> Path:
    """Determine the output CSV path for a given JSON file.

    Args:
        json_path: Path to the source JSON file.
        output: Optional -o argument. Can be:
            - None: report file is placed next to the JSON file with .report.csv suffix.
            - A path ending in .csv or .tsv: used as-is (for single-file output).
            - A directory path: report file placed in that directory with automatic naming.

    Returns:
        The resolved output Path.
    """
    json_path = Path(json_path)
    default_name = json_path.stem + ".report.csv"

    if output is None:
        return json_path.parent / default_name

    output = Path(output)
    if output.suffix.lower() in (".csv", ".tsv"):
        return output

    # Treat as directory
    output.mkdir(parents=True, exist_ok=True)
    return output / default_name


def process_json_file(
    json_path: str | Path,
    output: Optional[str | Path] = None,
    verbose: bool = False,
) -> Optional[Path]:
    """Process a single JSON file: extract to CSV, then validate.

    Returns the path to the generated report CSV, or None if the file was skipped.
    """
    json_path = Path(json_path)
    df = json_to_dataframe(json_path)
    if df is None:
        if verbose:
            print(
                f"Skipping {json_path}: not a valid format or no HIERARCHY_TIMELINEs found."
            )
        return None

    csv_path = resolve_output_path(json_path, output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"Extracted {len(df)} components from {json_path} -> {csv_path}")

    # Validate the CSV (populates 'passing' and 'output' columns)
    parse_csv_file(str(csv_path))
    return csv_path


def process_json_directory(
    directory: str | Path,
    output: Optional[str | Path] = None,
    verbose: bool = False,
) -> list[Path]:
    """Recursively process all JSON files in a directory.

    Behaviour depends on -o:
        1. No -o: each JSON file gets a sibling .report.csv
        2. -o is a directory: reports are created in that directory with automatic names
        3. -o is a .csv/.tsv file: all expressions are concatenated into one file before validation

    Returns a list of generated report CSV paths.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Determine mode
    concat_mode = False
    if output is not None:
        output_path = Path(output)
        if output_path.suffix.lower() in (".csv", ".tsv"):
            concat_mode = True

    # Collect all JSON files recursively
    json_files = sorted(directory.rglob("*.json"))

    if not json_files:
        print(f"No JSON files found in {directory}")
        return []

    if concat_mode:
        # Mode 3: concatenate all into one file
        all_frames = []
        for json_file in json_files:
            df = json_to_dataframe(json_file)
            if df is None:
                if verbose:
                    print(
                        f"Skipping {json_file}: not a valid format or no HIERARCHY_TIMELINEs found."
                    )
                continue
            # Add a source column to track which file each row came from
            df.insert(0, "source_file", str(json_file))
            all_frames.append(df)

        if not all_frames:
            print(f"No valid JSON files with HIERARCHY_TIMELINEs found in {directory}")
            return []

        combined_df = pd.concat(all_frames, ignore_index=True)
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        print(
            f"Extracted {len(combined_df)} total components from {len(all_frames)} files -> {output_path}"
        )

        # Validate the combined CSV
        parse_csv_file(str(output_path))
        return [output_path]

    # Mode 1 or 2: per-file reports
    report_paths = []
    for json_file in json_files:
        result = process_json_file(json_file, output=output, verbose=verbose)
        if result is not None:
            report_paths.append(result)

    if not report_paths:
        print(f"No valid JSON files with HIERARCHY_TIMELINEs found in {directory}")

    return report_paths


# endregion JSON processing
# region argument dispatch

DEFAULT_REPORT_NAME = "lcma_validation_report.csv"


def _resolve_single_output(
    output: Optional[str | Path],
    default_stem: Optional[str] = None,
) -> Optional[Path]:
    """Resolve -o for single-expression modes (-e, -f).

    Returns None if no output was requested, otherwise the resolved Path.
    """
    if output is None:
        return None
    output = Path(output)
    if output.suffix.lower() in (".csv", ".tsv"):
        return output
    # Treat as directory
    output.mkdir(parents=True, exist_ok=True)
    name = (default_stem + ".report.csv") if default_stem else DEFAULT_REPORT_NAME
    return output / name


def _validate_and_report(
    expression: str,
    output_path: Path,
) -> None:
    """Validate a single expression and write/update a one-row report CSV."""
    try:
        parsed_result = parse_expression_as_objects(expression)
        passing = True
        result_str = str(parsed_result)
    except Exception as e:
        passing = False
        result_str = str(e)

    df = pd.DataFrame(
        [{"passing": passing, "expression": expression, "output": result_str}]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    status = "passed" if passing else "FAILED"
    print(f"Expression {status}. Report saved to {output_path}")


def main(
    expression: Optional[str] = None,
    txt_file: Optional[str] = None,
    csv_file: Optional[str] = None,
    json_file: Optional[str] = None,
    json_dir: Optional[str] = None,
    output: Optional[str] = None,
    verbose: bool = False,
):
    global VERBOSE
    VERBOSE = verbose
    if all(
        arg is None for arg in (expression, txt_file, csv_file, json_file, json_dir)
    ):
        raise ValueError("At least one argument must be provided.")
    if expression:
        parsed_expression = parse_expression_as_objects(expression)
        pprint(parsed_expression, sort_dicts=False)
        out_path = _resolve_single_output(output)
        if out_path:
            _validate_and_report(expression, out_path)
    if txt_file:
        parsed_file = parse_file_as_objects(txt_file)
        pprint(parsed_file, sort_dicts=False)
        out_path = _resolve_single_output(output, default_stem=Path(txt_file).stem)
        if out_path:
            # Read the expression from the file and validate it
            with open(txt_file, "r", encoding="utf-8") as f:
                file_expression = f.read().strip()
            _validate_and_report(file_expression, out_path)
    if csv_file:
        parse_csv_file(csv_file)
    if json_file:
        process_json_file(json_file, output=output, verbose=verbose)
    if json_dir:
        process_json_directory(json_dir, output=output, verbose=verbose)


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
    parser.add_argument(
        "-j",
        "--json",
        help="A JSON file with 'timelines' as its first top-level key. Components from HIERARCHY_TIMELINEs "
        "are extracted, validated, and saved as a report CSV.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="A directory to recursively scan for JSON files with HIERARCHY_TIMELINEs. "
        "Each valid file is processed like -j.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for report files. If a .csv/.tsv filepath, used as the output file. "
        "If a directory, reports are placed there with automatic names. "
        "Default for -j/-d: report CSV next to each JSON file. "
        "For -e/-f: no CSV output unless -o is specified.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed parse trees during validation. Also print information "
        "about skipped files when using -d.",
    )
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    main(
        expression=args.expression,
        txt_file=args.file,
        csv_file=args.csv,
        json_file=args.json,
        json_dir=args.directory,
        output=args.output,
        verbose=args.verbose,
    )


# endregion argument dispatch

if __name__ == "__main__":
    run()
