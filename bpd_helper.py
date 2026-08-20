# ruff: noqa: SLF001
# Private members are accessed intentionally.
"""Helper library for generating bl2/tps BehaviorProvideDefinition Commands.

Intended to be used by standalone scripts, one per BPD command.

General process is:
Create all variables with generate_variables.
Use edit_variable to modify any variables.
Construct all the EventData objects.
Construct all the Behavior objects.
Link Behaviors to events and Behaviors to Behaviors with BehaviorLinks.
Call generate_bpd to output the bpd to a file.

Variables, Events and Behaviors are all automatically tracked,
generate_bpd will automatically build the entire bpd based on how
everything is setup.
"""

from __future__ import annotations

import inspect
import json
import struct
from contextlib import contextmanager
from dataclasses import MISSING, dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal, Self, overload

import behavior_variable_values

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "Behavior",
    "BehaviorLink",
    "BehaviorSequence",
    "BpdVariable",
    "EBehaviorVariableLinkType",
    "EBehaviorVariableType",
    "EventData",
    "VariableLinkData",
    "edit_variable",
    "generate_bpd",
    "generate_bpd_sequence",
    "generate_variables",
]

BPD_SEQUENCE_COMMAND = """(
    BehaviorSequenceName = "{}",
    bEnabledOnSpawn = {},
    bSequenceEnabledMutex = {},
    CustomEnableCondition = {},
    EventData = ,
    EventData2 = ({}),
    BehaviorData = ,
    BehaviorData2 = ({}),
    VariableData = ,
    ConsolidatedOutputLinkData = ({}),
    ConsolidatedVariableLinkData = ({}),
    ConsolidatedLinkedVariables = ({})
)"""

"""_ALL_EVENTS: list[EventData] = []
_ALL_BEHAVIORS: list[Behavior] = []
_ALL_VARIABLES: list[BpdVariable] = []"""

_CURRENT_SEQUENCE: BehaviorSequence | None = None


class EBehaviorVariableType(Enum):  # noqa: D101
    BVAR_None = 0
    BVAR_Bool = 1
    BVAR_Int = 2
    BVAR_Float = 3
    BVAR_Vector = 4
    BVAR_Object = 5
    BVAR_AllPlayers = 6
    BVAR_Attribute = 7
    BVAR_InstanceData = 8
    BVAR_NamedVariable = 9
    BVAR_NamedKismetVariable = 10
    BVAR_DirectionVector = 11
    BVAR_AttachmentLocation = 12
    BVAR_UnaryMath = 13
    BVAR_BinaryMath = 14
    BVAR_Flag = 15


class EBehaviorVariableLinkType(Enum):  # noqa: D101
    BVARLINK_Unknown = 0
    BVARLINK_Context = 1
    BVARLINK_Input = 2
    BVARLINK_Output = 3


def validate_variable_value(  # noqa: C901, PLR0912, PLR0915
    var_type: EBehaviorVariableType,
    value: behavior_variable_values.BehaviorVariableDataValue,
) -> None:
    """Validate the value for the variable type."""
    msg = None
    match var_type:
        case EBehaviorVariableType.BVAR_None:
            if value is not None:
                msg = "Cannot set a value for BVAR_None."

        case EBehaviorVariableType.BVAR_Bool:
            if not isinstance(value, bool):
                msg = "Value for a BVAR_Bool must be a bool."

        case EBehaviorVariableType.BVAR_Int:
            if not isinstance(value, int):
                msg = "Value for a BVAR_Int must be a int."

        case EBehaviorVariableType.BVAR_Float:
            if not isinstance(value, float | int):
                msg = "Value for a BVAR_Float must be a float."

        case EBehaviorVariableType.BVAR_Vector:
            if not isinstance(value, behavior_variable_values.BVVector):
                msg = "Value for a BVAR_Vector must be a BVVector."

        case EBehaviorVariableType.BVAR_Object:
            if not isinstance(value, str):
                msg = "Value for a BVAR_Object must be a ObjectPath."

        case EBehaviorVariableType.BVAR_AllPlayers:
            if value is not None:
                msg = "Cannot set a value for BVAR_AllPlayers."

        case EBehaviorVariableType.BVAR_Attribute:
            if not isinstance(value, behavior_variable_values.BVAttributeData):
                msg = "Value for a BVAR_Attribute must be a BVAttributeData."

        case EBehaviorVariableType.BVAR_InstanceData:
            if not isinstance(value, behavior_variable_values.BVInstanceData):
                msg = "Value for a BVAR_InstanceData must be a BVInstanceData."

        case EBehaviorVariableType.BVAR_NamedVariable:
            if value is not None:
                msg = "Cannot set a value for BVAR_NamedVariable."

        case EBehaviorVariableType.BVAR_NamedKismetVariable:
            if value is not None:
                msg = "Cannot set a value for BVAR_NamedKismetVariable."

        case EBehaviorVariableType.BVAR_DirectionVector:
            if not isinstance(value, behavior_variable_values.BVDirectionVectorData):
                msg = "Value for a BVAR_DirectionVector must be a BVDirectionVectorData."

        case EBehaviorVariableType.BVAR_AttachmentLocation:
            if not isinstance(value, behavior_variable_values.BVAttachmentLocationData):
                msg = "Value for a BVAR_AttachmentLocation must be a BVAttachmentLocationData."

        case EBehaviorVariableType.BVAR_UnaryMath:
            if not isinstance(value, behavior_variable_values.BVUnaryMathData):
                msg = "Value for a BVAR_UnaryMath must be a BVUnaryMathData."

        case EBehaviorVariableType.BVAR_BinaryMath:
            if not isinstance(value, behavior_variable_values.BVBinaryMathData):
                msg = "Value for a BVAR_BinaryMath must be a BVBinaryMathData."

        case EBehaviorVariableType.BVAR_Flag:
            if not isinstance(value, behavior_variable_values.BVFlagData):
                msg = "Value for a BVAR_Flag must be a BVFlagData."

        case _:
            msg = f"Unknown variable type {var_type}."

    if msg is not None:
        raise ValueError(msg)


class BpdVariable:
    """An object to represent an entry in the VariableData array.

    By default commands will not be made for these as setting the VariableData array crashes,
    instead specific variables will have commands written for them if needs_command is True.
    Variables do not need to be set up to match their actual values in the bpd since they are
    only there for referencing when linking, you only need to properly set the properties
    when a command is to be written.
    By default the idx will be -1, once it is generated it will be automatically appended to
    the array of variables and given it's correct index.
    Specifying an index will override the specified index with the new variable, if the index
    is outisde the variables array, it will be extended with BpdVariable objects

    Attributes:
        var_type: the type of the variable
        name: the name of the variable
        idx: index in the VariableData array
        needs_command: if a command should be written to set this variable
                    'set {bpd_name} BehaviorSequences[{sequence}].VariableData[{idx}] {command_str}

    """

    name: str
    var_type: EBehaviorVariableType = EBehaviorVariableType.BVAR_None
    _value: behavior_variable_values.BehaviorVariableDataValue = None

    @property
    def value(self) -> behavior_variable_values.BehaviorVariableDataValue:
        """Get value."""
        return self._value

    @value.setter
    def value(self, value: behavior_variable_values.BehaviorVariableDataValue) -> None:
        """Check value is valid and set."""
        validate_variable_value(self.var_type, value)
        self._value = value

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_None],
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Bool],
        value: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Int],
        value: int = 0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Float],
        value: float = 0.0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Vector],
        value: behavior_variable_values.BVVector | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Object],
        value: behavior_variable_values.ObjectName | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_AllPlayers],
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Attribute],
        value: behavior_variable_values.BVAttributeData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_InstanceData],
        value: behavior_variable_values.BVInstanceData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_NamedVariable],
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_NamedKismetVariable],
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_DirectionVector],
        value: behavior_variable_values.BVDirectionVectorData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_AttachmentLocation],
        value: behavior_variable_values.BVAttachmentLocationData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_UnaryMath],
        value: behavior_variable_values.BVUnaryMathData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_BinaryMath],
        value: behavior_variable_values.BVBinaryMathData,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        var_type: Literal[EBehaviorVariableType.BVAR_Flag],
        value: behavior_variable_values.BVFlagData,
    ) -> None: ...

    @overload
    def __init__(
        self,
    ) -> None: ...

    def __init__(
        self,
        name: str = "",
        var_type: EBehaviorVariableType = EBehaviorVariableType.BVAR_None,
        value: behavior_variable_values.BehaviorVariableDataValue = None,
    ) -> None:
        self.name = name
        self.var_type = var_type
        self.value = value

        if _CURRENT_SEQUENCE is not None:
            _CURRENT_SEQUENCE.variables.append(self)

    def to_dict(self, sequence: BehaviorSequence) -> dict:
        """Get the value as a dictionary for set variable commands."""
        value = self.value
        if isinstance(value, behavior_variable_values.VariableValue):
            value = value.resolve(sequence)
        return {"Name": self.name, "Type": self.var_type.name, "Value": value}

    def copy(self) -> BpdVariable:
        """Get a copy.

        Automatically copies any variables in SubarrayData
        which will end up in the BehaviorSequence struct.
        """
        value = self.value
        if isinstance(value, behavior_variable_values.VariableValue):
            value = value.copy()
        return BpdVariable(self.name, self.var_type, value)  # ty: ignore[no-matching-overload]


def generate_variables(count: int) -> None:
    """Generate 'count' BpdVariable objects."""
    for _ in range(count):
        BpdVariable()


def edit_variable(
    idx: int,
    name: str | None = None,
    var_type: EBehaviorVariableType | None = None,
) -> int:
    """Set the properties of the BpdVariable.

    Set the properties of the BpdVariable at the specified index and enables 'needs_command'.
    Also returns the variable index for use.
    """
    if _CURRENT_SEQUENCE is None:
        msg = "There is no active sequence."
        raise RuntimeError(msg)

    var = _CURRENT_SEQUENCE.variables[idx]
    if var_type is not None:
        var.var_type = var_type
    if name is not None:
        var.name = name
    return idx


@dataclass
class VariableLinkData:
    """An object to represent an entry in the ConsolidatedVariableLinkData array.

    Specifies how variables are used by behaviors and events,
    events will only use BVARLINK_Output, while behaviors use any of the types.
    For BVARLINK_Output you need to specify the connection_index as it is used
    to specify which output variable is sent.
    For BVARLINK_Input the name is used to specify what property of the behavior
    the variable will be used for.
    For BVARLINK_Context the name should be just 'Context'.

    Attributes:
        variable_indexes: list of variable indexes to link to
        property_name: the PropertyName
        link_type: the LinkType
        connection_index: the ConnectionIndex

    """

    variable_indexes: list[int | BpdVariable]
    property_name: str
    link_type: EBehaviorVariableLinkType
    connection_index: int = 0

    _command_str: ClassVar[str] = (
        '(PropertyName="{}",'
        "VariableLinkType={},"
        "ConnectionIndex={},"
        "LinkedVariables=(ArrayIndexAndLength={}),"
        "CachedProperty=None)"
    )

    def _copy(self) -> VariableLinkData:
        return VariableLinkData(
            list(self.variable_indexes),
            self.property_name,
            self.link_type,
            self.connection_index,
        )

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"VariableLinkData({self.variable_indexes!r},"
            f"{self.property_name!r},"
            f"EBehaviorVariableLinkType.{self.link_type.name},"
            f"{self.connection_index})"
        )


@dataclass
class EventData:
    """An object to represent an entry in the EventData2 array.

    Attributes:
        event_name: the EventName property
        enabled: the bEnabled property
        replicate: the bReplicate property
        max_trigger_count: the MaxTriggerCount property
        retrigger_delay: the ReTriggerDelay property
        filter_object: the FilterObject property
        output_variables: list of VariableLinkData for the OutputVariables
        output_links: list of BehaviorLink for the OutputLinks

    """

    event_name: str
    enabled: bool = True
    replicate: bool = False
    max_trigger_count: int = 0
    retrigger_delay: float = 0.0
    filter_object: str = "None"
    output_variables: list[VariableLinkData] = field(default_factory=list)
    output_links: list[BehaviorLink] = field(default_factory=list)

    _command_str: ClassVar[str] = (
        '(UserData=(EventName="{}",'
        "bEnabled={},"
        "bReplicate={},"
        "MaxTriggerCount={},"
        "ReTriggerDelay={},"
        "FilterObject={}),"
        "OutputVariables=(ArrayIndexAndLength={}),"
        "OutputLinks=(ArrayIndexAndLength={}))"
    )

    def __post_init__(self):  # noqa: ANN204, D105
        if _CURRENT_SEQUENCE is not None:
            _CURRENT_SEQUENCE.events.append(self)

    def gen_output_link(self, behavior: Behavior, link_id: int = 0, delay: int = 0) -> None:
        """Generate a BehaviorLink.

        Generate a BehaviorLink. Generally deprecated with iadd being
        the now preferred method of linking.
        """
        self.output_links.append(BehaviorLink(behavior, link_id, delay))

    def add_output_link(self, link: BehaviorLink) -> None:
        """Add a BehaviorLink to output_links."""
        self.output_links.append(link)

    def __iadd__(self, link: BehaviorLink) -> Self:  # noqa: D105
        self.output_links.append(link)
        return self

    def __repr__(self) -> str:  # noqa: D105
        parts = []

        for f in fields(self):
            value = getattr(self, f.name)

            if f.default is not MISSING and value == f.default:
                continue

            if isinstance(value, list) and len(value) == 0:
                continue

            parts.append(f"{f.name}={value!r}")

        return f"{type(self).__name__}({', '.join(parts)})"


@dataclass(unsafe_hash=True)
class Behavior:
    """An object to represent an entry in the BehaviorData2 array.

    Attributes:
        behavior: the Behavior property
        linked_variables: list of VariableLinkData for the LinkedVariables
        output_links: list of BehaviorLink for the OutputLinks

    """

    short_name: str
    linked_variables: list[VariableLinkData] = field(default_factory=list, hash=False)
    output_links: list[BehaviorLink] = field(default_factory=list, hash=False)
    full_name: str | None = None

    _variables_ArrayIndexAndLength: int = field(default=0, init=False)  # noqa: N815
    _output_ArrayIndexAndLength: int = field(default=0, init=False)  # noqa: N815
    _command_str: ClassVar[str] = (
        "(Behavior={},LinkedVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))"
    )

    def gen_output_link(self, behavior: Behavior, link_id: int = 0, delay: int = 0) -> None:
        """Generate a BehaviorLink.

        Generate a BehaviorLink. Generally deprecated with iadd being
        the now preferred method of linking.
        """
        self.output_links.append(BehaviorLink(behavior, link_id, delay))

    def add_output_link(self, link: BehaviorLink) -> None:
        """Add a BehaviorLink to output_links."""
        self.output_links.append(link)

    def __iadd__(self, link: BehaviorLink) -> Self:  # noqa: D105
        self.output_links.append(link)
        return self

    def copy(self) -> Behavior:
        """Copy this object.

        Used to duplicate a behavior node for when you want to reuse a
        behavior without redefining the whole node.
        """
        return Behavior(
            self.short_name,
            [varlink._copy() for varlink in self.linked_variables],
            [outlink._copy() for outlink in self.output_links],
            self.full_name,
        )

    def __repr__(self) -> str:  # noqa: D105
        parts = []

        for f in fields(self):
            value = getattr(self, f.name)

            if f.default is not MISSING and value == f.default:
                continue

            if isinstance(value, list) and len(value) == 0:
                continue

            parts.append(f"{f.name}={value!r}")

        return f"{type(self).__name__}({', '.join(parts)})"


@dataclass
class BehaviorLink:
    """An object to represent an entry in the ConsolidatedOutputLinkData array.

    Attributes:
        behavior: the Behavior to link to
        link_id: the id to use for the LinkIdAndLinkedBehavior
        delay: the ActivateDelay property

    """

    behavior: Behavior
    link_id: int = 0
    delay: float = 0

    _command_str: ClassVar[str] = "(LinkIdAndLinkedBehavior={},ActivateDelay={})"

    def _copy(self) -> BehaviorLink:
        return BehaviorLink(self.behavior, self.link_id, self.delay)

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"BehaviorLink({self.behavior.short_name}"
            + (f",{self.link_id}" if self.link_id != 0 else "")
            + (f",{self.delay}" if self.delay != 0 else "")
            + (")")
        )


@dataclass
class BehaviorSequence:
    name: str = "Default"
    enabled_on_spawn: bool = True
    enabled_mutex: bool = False
    enable_condition: str = "None"
    events: list[EventData] = field(default_factory=list)
    variables: list[BpdVariable] = field(default_factory=list)

    linked_variables: list[int] = field(default_factory=list, init=False)

    @contextmanager
    def define_for_sequence(self) -> Iterator[None]:
        """Automatically add BpdVariables and EventData to this sequence."""
        global _CURRENT_SEQUENCE  # noqa: PLW0603
        if _CURRENT_SEQUENCE is not None:
            msg = "Cannot use define_for_sequence while already defining for a different sequence."
            raise RuntimeError(msg)
        _CURRENT_SEQUENCE = self
        try:
            yield
        finally:
            _CURRENT_SEQUENCE = None

    def lookup_variables_idx_len(self, bpd_vars: list[BpdVariable | int]) -> int:
        var_indexes = [
            self.variables.index(v) if isinstance(v, BpdVariable) else v for v in bpd_vars
        ]
        if (vars_len := len(var_indexes)) == 1:
            return get_arrayindexandlength(var_indexes[0], 1)
        if vars_len > 1:
            i = len(self.linked_variables)
            self.linked_variables.extend(var_indexes)
            return get_arrayindexandlength(i, vars_len)
        return 0

    def _get_var_link_commands(
        self,
        var_links: list[VariableLinkData],
    ) -> list[str]:
        """Generate all the individual variable link commands.

        Arguments:
            var_links: the list of VariableLinkData to make commands for

        """
        variable_link_commands = []
        for var_link in var_links:
            command_str = var_link._command_str.format(
                var_link.property_name,
                var_link.link_type.name,
                var_link.connection_index,
                self.lookup_variables_idx_len(var_link.variable_indexes),
            )
            variable_link_commands.append(command_str)
        return variable_link_commands

    def generate_command(self, bpd_name: str) -> list[str]:
        self.linked_variables = list(range(len(self.variables)))

        behavior_stack: list[Behavior] = []
        known_behaviors: list[Behavior] = []

        event_commands: list[str] = []
        behavior_commands: list[str] = []
        behavior_link_commands: list[str] = []
        variable_link_commands: list[str] = []

        for event in self.events:
            output_vars = get_arrayindexandlength(
                len(variable_link_commands),
                len(event.output_variables),
            )
            output_links = get_arrayindexandlength(
                len(behavior_link_commands),
                len(event.output_links),
            )

            variable_link_commands.extend(self._get_var_link_commands(event.output_variables))

            # Find unqiue set of unseen behaviours,
            behavior_stack.extend(
                reversed(
                    list(
                        {
                            link.behavior
                            for link in event.output_links
                            if link.behavior not in known_behaviors
                        },
                    ),
                ),
            )

            behavior_link_commands.extend(
                get_behavior_link_commands(event.output_links, known_behaviors),
            )

            command_str = event._command_str.format(
                event.event_name,
                event.enabled,
                event.replicate,
                event.max_trigger_count,
                f"{event.retrigger_delay:f}",
                event.filter_object,
                output_vars,
                output_links,
            )
            event_commands.append(command_str)

            while len(behavior_stack) > 0:
                behavior = behavior_stack.pop()
                if behavior is None:
                    continue
                behavior._variables_ArrayIndexAndLength = get_arrayindexandlength(
                    len(variable_link_commands),
                    len(behavior.linked_variables),
                )
                variable_link_commands.extend(
                    self._get_var_link_commands(behavior.linked_variables),
                )

                behavior._output_ArrayIndexAndLength = get_arrayindexandlength(
                    len(behavior_link_commands),
                    len(behavior.output_links),
                )

                behavior_stack.extend(
                    reversed(
                        list(
                            {
                                link.behavior
                                for link in behavior.output_links
                                if link.behavior not in known_behaviors
                            }
                        )
                    )
                )

                behavior_link_commands.extend(
                    get_behavior_link_commands(behavior.output_links, known_behaviors),
                )

        behavior_commands.extend(
            [
                behavior._command_str.format(
                    behavior.full_name
                    if behavior.full_name is not None
                    else f"{bpd_name}.{behavior.short_name}",
                    behavior._variables_ArrayIndexAndLength,
                    behavior._output_ArrayIndexAndLength,
                )
                for behavior in known_behaviors
            ],
        )
        for var in self.variables:
            if isinstance(var.value, behavior_variable_values.VariableValue):
                var.value.resolve(self)
        return [
            "(",
            f'    BehaviorSequenceName = "{self.name}",',
            f"    bEnabledOnSpawn = {self.enabled_on_spawn},",
            f"    bSequenceEnabledMutex = {self.enabled_mutex},",
            f"    CustomEnableCondition = {self.enable_condition},",
            f"    EventData2 = ({','.join(event_commands)}),",
            f"    BehaviorData2 = ({','.join(behavior_commands)}),",
            f"    ConsolidatedOutputLinkData = ({','.join(behavior_link_commands)}),",
            f"    ConsolidatedVariableLinkData = ({','.join(variable_link_commands)}),",
            f"    ConsolidatedLinkedVariables = ({','.join(str(v) for v in self.linked_variables)})",
            ")",
        ]

    def get_variable_commands(self, bpd_name: str, sequence_idx: int) -> list[str]:
        commands: list[str] = []

        set_all = EBehaviorVariableType.BVAR_None not in [var.var_type for var in self.variables]

        for idx, variable in enumerate(self.variables):
            match variable.var_type:
                case EBehaviorVariableType.BVAR_None:
                    continue
                case (
                    EBehaviorVariableType.BVAR_NamedVariable
                    | EBehaviorVariableType.BVAR_NamedKismetVariable
                ):
                    d = variable.to_dict(self)
                    d.pop("Value")
                case _:
                    d = variable.to_dict(self)
                    if d["Value"] is None:
                        d.pop("Value")

            if set_all:
                commands.append(f"{json.dumps(d, separators=(',', ':'))}")
            else:
                commands.append(
                    f"set_variable {bpd_name} {sequence_idx} {idx} "
                    f"{json.dumps(d, separators=(',', ':'))}\n"
                )
        if set_all:
            return [f"set_variable_data {bpd_name} {sequence_idx} [{','.join(commands)}]\n"]
        return commands


def get_arrayindexandlength(idx: int, length: int) -> int:
    """Convert an index and length into a single ArrayIndexAndLength."""
    if length == 0:
        return 0
    return struct.unpack("<i", struct.pack("<HH", length, idx))[0]


def get_linkidandlinkedbehavior(link_id: int, behavior_idx: int) -> int:
    """Convert an id and behavior idx into a single LinkIdAndLinkedBehavior."""
    return struct.unpack("<i", struct.pack("<Hxb", behavior_idx, link_id))[0]


def parse_arrayindexandlength(number: int) -> tuple[int, int]:
    """Return an array index and length tuple for the given number."""
    # Could just use >> and & for this, but since we have to be more
    # careful with LinkIdAndLinkedBehavior anyway, since that one's
    # weirder, we may as well just use struct here, as well.
    number = int(number)
    byteval = struct.pack(">i", number)
    return struct.unpack(">HH", byteval)


def parse_linkidandlinkedbehavior(number: int) -> tuple[int, int]:
    """Return a link ID index and behavior tuple for the given number."""
    number = int(number)
    byteval = struct.pack(">i", number)
    (linkid, _, behavior) = struct.unpack(">bbH", byteval)
    return (linkid, behavior)


def get_behavior_link_commands(
    behaviour_links: list[BehaviorLink],
    known_behaviors: list[Behavior],
) -> list[str]:
    """Generate all the individual behavior link commands.

    Arguments:
        behaviour_links: the list of BehaviorLink to make commands for
        known_behaviors: list of all previously seen behaviors,
                        will be the BehaviorData2

    """
    behavior_link_commands = []
    for link in behaviour_links:
        if link.behavior not in known_behaviors:
            known_behaviors.append(link.behavior)
        idx = known_behaviors.index(link.behavior)
        command_str = link._command_str.format(
            get_linkidandlinkedbehavior(link.link_id, idx),
            f"{link.delay:f}",
        )
        behavior_link_commands.append(command_str)
    return behavior_link_commands


def generate_bpd(bpd_name: str, sequences: list[BehaviorSequence], set_early: bool = True) -> None:
    """Generate the bpd.

    Generates the bpd for the data in _ALL_EVENTS and _ALL_VARIABLES
    and writes to a file, the file name is based on bpd_name.

    Events are all automatically included, regardless of if they link to behaviors,
    because events can have outputs, events have a use beyond just triggering behaviors.
    Only Behaviors linked to by Events and other Behaviors will be included.

    Arguments:
        bpd_name: The name of the BPD, will also be used as the file name
                    with any : replaced with . due to windows file limitations
        sequence: index in the BehaviorSequences as *usually* only one can be edited at a time
                    a sequence less than 0 results in it editing the entire BPD rather than just
                    one entry.

    """
    caller_dir = Path(inspect.stack()[1].filename).parent

    outfile_path = caller_dir / f"{bpd_name.replace(':', '.')}.txt"

    sequence_commands = []
    variable_commands = []
    for idx, sequence in enumerate(sequences):
        cmd = sequence.generate_command(bpd_name)
        if set_early:
            cmd = [line.lstrip() for line in cmd]
            sequence_commands.append("".join(cmd))
        else:
            cmd = [f"    {line}" for line in cmd]
            sequence_commands.append("\n".join(cmd))
        variable_commands.extend(sequence.get_variable_commands(bpd_name, idx))

    with outfile_path.open("w") as outfile:
        if set_early:
            outfile.write(
                f"set_early {bpd_name} BehaviorSequences ({','.join(sequence_commands)})",
            )
        else:
            outfile.write(
                f"set {bpd_name} BehaviorSequences\n(\n{',\n'.join(sequence_commands)}\n)",
            )
        outfile.write("\n")
        outfile.writelines(variable_commands)


def generate_bpd_sequence(bpd_name: str, sequence: BehaviorSequence, idx: int) -> None:
    caller_dir = Path(inspect.stack()[1].filename).parent

    outfile_path = caller_dir / f"{bpd_name.replace(':', '.')}[{idx}].txt"

    variable_commands = []
    cmd = sequence.generate_command(bpd_name)
    cmd = [f"{line}" for line in cmd]
    sequence_command = "\n".join(cmd)
    variable_commands.extend(sequence.get_variable_commands(bpd_name, idx))

    with outfile_path.open("w") as outfile:
        outfile.write(
            f"set {bpd_name} BehaviorSequences[{idx}]\n{sequence_command}",
        )
        outfile.write("\n")
        outfile.writelines(variable_commands)
