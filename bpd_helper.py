# ruff: noqa: SLF001
# Private members are accessed intentionally.
"""Helper library for generating bl2/tps BehaviorProvideDefinition Commands.

Intended to be used by standalone scripts, one per BPD command.
"""

from __future__ import annotations

import inspect
import struct
from dataclasses import MISSING, dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import ClassVar, Self

__all__ = [
    "Behavior",
    "BehaviorLink",
    "EBehaviorVariableLinkType",
    "EBehaviorVariableType",
    "EventData",
    "VariableLinkData",
    "edit_variable",
    "generate_bpd",
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

_ALL_EVENTS: list[EventData] = []
_ALL_BEHAVIORS: list[Behavior] = []
_ALL_VARIABLES: list[BpdVariable] = []


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


@dataclass
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

    var_type: EBehaviorVariableType = EBehaviorVariableType.BVAR_None
    name: str = ""
    idx: int = -1
    needs_command: bool = False
    updated_name: bool = False
    updated_type: bool = False

    _command_str: ClassVar[str] = '(Name="{}",Type={})'

    def __post_init__(self):  # noqa: ANN204
        if self.idx == -1:
            self.idx = len(_ALL_VARIABLES)
            _ALL_VARIABLES.append(self)
            return
        if len(_ALL_VARIABLES) < (self.idx + 1):
            _ALL_VARIABLES.extend(
                [BpdVariable() for _ in range(self.idx + 1 - len(_ALL_VARIABLES))],
            )
        _ALL_VARIABLES[self.idx] = self


def generate_variables(count: int) -> None:
    """Generate 'count' BpdVariable objects."""
    for _ in range(count):
        BpdVariable()


def edit_variable(
    idx: int,
    name: str | None = None,
    var_type: EBehaviorVariableType = None,
) -> int:
    """Set the properties of the BpdVariable.

    Set the properties of the BpdVariable at the specified index and enables 'needs_command'.
    Also returns the variable index for use.
    """
    var = _ALL_VARIABLES[idx]
    var.idx = idx
    if var_type is not None:
        var.var_type = var_type
        var.updated_type = True
    if name is not None:
        var.name = name
        var.updated_name = True
    var.needs_command = True
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

    def __post_init__(self):  # noqa: ANN204, D105
        if not isinstance(self.variable_indexes, list):
            msg = "variable_indexes is not a list"
            raise TypeError(msg)
        for var_idx in self.variable_indexes:
            if var_idx >= len(_ALL_VARIABLES):
                msg = f"Variable index {var_idx} out of range of defined variables."
                raise IndexError(msg)

    def get_variable_indexes(self) -> list[int]:
        """Get variable indexes."""
        return [x if isinstance(x, int) else x.idx for x in self.variable_indexes]

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
        _ALL_EVENTS.append(self)

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

    behavior: str
    linked_variables: list[VariableLinkData] = field(default_factory=list, hash=False)
    output_links: list[BehaviorLink] = field(default_factory=list, hash=False)

    _variables_ArrayIndexAndLength: ClassVar[int] = 0  # noqa: N815
    _output_ArrayIndexAndLength: ClassVar[int] = 0  # noqa: N815
    _command_str: ClassVar[str] = (
        "(Behavior={},LinkedVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))"
    )

    def __post_init__(self) -> None:  # noqa: D105
        _ALL_BEHAVIORS.append(self)

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
            self.behavior,
            [varlink._copy() for varlink in self.linked_variables],
            [outlink._copy() for outlink in self.output_links],
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
            f"BehaviorLink({self.behavior.behavior.split('.')[-1]}"
            + (f",{self.link_id}" if self.link_id != 0 else "")
            + (f",{self.delay}" if self.delay != 0 else "")
            + (")")
        )


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


def get_var_link_commands(
    var_links: list[VariableLinkData],
    variable_links: list[int],
) -> list[str]:
    """Generate all the individual variable link commands.

    Arguments:
        var_links: the list of VariableLinkData to make commands for
        variable_links: list of indexes to Variables, will be the ConsolidatedLinkedVariables

    """
    variable_link_commands = []
    for var_link in var_links:
        idx = 0
        length = len(var_link.get_variable_indexes())
        if length > 1:
            idx = len(variable_links)
            variable_links.extend(var_link.get_variable_indexes())
        elif length == 1:
            idx = var_link.get_variable_indexes()[0]
        command_str = var_link._command_str.format(
            var_link.property_name,
            var_link.link_type.name,
            var_link.connection_index,
            get_arrayindexandlength(idx, length),
        )
        variable_link_commands.append(command_str)
    return variable_link_commands


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


def generate_bpd(  # noqa: PLR0913
    bpd_name: str,
    sequence: int = 0,
    sequence_name: str = "Default",
    enabled_on_spawn: bool = True,
    sequence_enabled_mutex: bool = False,
    custom_enable_condition: str = "None",
    include_variable_data: bool = False,
) -> None:
    """Generate the bpd.

    Generates the bpd for the data in _ALL_EVENTS and _ALL_VARIABLES
    and writes to a file.

    Arguments:
        bpd_name: The name of the BPD, will also be used as the file name
                    with any : replaced with . due to windows file limitations
        sequence: index in the BehaviorSequences as *usually* only one can be edited at a time
                    a sequence less than 0 results in it editing the entire BPD rather than just
                    one entry.
        sequence_name: BehaviorSequenceName
        enabled_on_spawn: bEnabledOnSpawn
        sequence_enabled_mutex: bSequenceEnabledMutex
        custom_enable_condition: CustomEnableCondition
        include_variable_data: Should variables be included within the bpd itself or as
                                additional hotfixes for the modified ones.

    """
    caller_dir = Path(inspect.stack()[1].filename).parent
    event_commands: list[str] = []
    behavior_commands: list[str] = []
    variable_data_commands: list[str] = []
    behavior_link_commands: list[str] = []
    variable_link_commands: list[str] = []
    variable_links: list[int] = list(range(len(_ALL_VARIABLES)))
    behavior_stack: list[Behavior] = []
    known_behaviors: list[Behavior] = []
    for event in _ALL_EVENTS:
        output_vars = get_arrayindexandlength(
            len(variable_link_commands),
            len(event.output_variables),
        )
        output_links = get_arrayindexandlength(len(behavior_link_commands), len(event.output_links))

        variable_link_commands.extend(get_var_link_commands(event.output_variables, variable_links))

        # Find unqiue set of unseen behaviours,
        # add to stack in reverse order so they will be handled in order linked to
        new_behaviors = reversed(
            list(
                {
                    link.behavior
                    for link in event.output_links
                    if link.behavior not in known_behaviors
                },
            ),
        )
        behavior_stack.extend(new_behaviors)

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
            behavior = behavior_stack[-1]
            behavior_stack.pop()
            if behavior is None:
                continue
            behavior._variables_ArrayIndexAndLength = get_arrayindexandlength(
                len(variable_link_commands),
                len(behavior.linked_variables),
            )
            variable_link_commands.extend(
                get_var_link_commands(behavior.linked_variables, variable_links),
            )

            behavior._output_ArrayIndexAndLength = get_arrayindexandlength(
                len(behavior_link_commands),
                len(behavior.output_links),
            )

            new_behaviors = reversed(
                list(
                    {
                        link.behavior
                        for link in behavior.output_links
                        if link.behavior not in known_behaviors
                    },
                ),
            )
            behavior_stack.extend(new_behaviors)

            behavior_link_commands.extend(
                get_behavior_link_commands(behavior.output_links, known_behaviors),
            )

    behavior_commands.extend(
        [
            behavior._command_str.format(
                behavior.behavior,
                behavior._variables_ArrayIndexAndLength,
                behavior._output_ArrayIndexAndLength,
            )
            for behavior in known_behaviors
        ],
    )

    # Appends all unused behaviors to the end of the bpd.
    # Was mostly used for testing but I'm leaving it here just in case.
    # May later add a toggle for it in the function call?
    """for behavior in _ALL_BEHAVIORS:
        if behavior in known_behaviors:
            continue
        behavior._variables_ArrayIndexAndLength = get_arrayindexandlength(
            len(variable_link_commands),
            len(behavior.linked_variables),
        )
        variable_link_commands.extend(
            get_var_link_commands(behavior.linked_variables, variable_links),
        )
        behavior_commands.append(
            behavior._command_str.format(
                behavior.behavior,
                behavior._variables_ArrayIndexAndLength,
                behavior._output_ArrayIndexAndLength,
            ),
        )"""

    if include_variable_data:
        for variable in _ALL_VARIABLES:
            name = f'"{variable.name}"' if variable.name != "" else ""
            variable_data_commands.append(f"(Name={name},Type={variable.var_type.name})")

    outfile_path = (
        caller_dir / f"{bpd_name.replace(':', '.')}{f'[{sequence}]' if sequence >= 0 else ''}.txt"
    )

    with outfile_path.open("w") as outfile:
        if include_variable_data:
            outfile.write(
                "\n".join(
                    (
                        f"set {bpd_name} BehaviorSequences"
                        f"{f'[{sequence}]' if sequence >= 0 else '('}",
                        "(",
                        f'    BehaviorSequenceName = "{sequence_name}",',
                        f"    bEnabledOnSpawn = {enabled_on_spawn},",
                        f"    bSequenceEnabledMutex = {sequence_enabled_mutex},",
                        f"    CustomEnableCondition = {custom_enable_condition},",
                        f"    EventData2 = ({','.join(event_commands)}),",
                        f"    BehaviorData2 = ({','.join(behavior_commands)}),",
                        f"    VariableData = ({','.join(variable_data_commands)}),",
                        f"    ConsolidatedOutputLinkData = ({','.join(behavior_link_commands)}),",
                        f"    ConsolidatedVariableLinkData = ({','.join(variable_link_commands)}),",
                        f"    ConsolidatedLinkedVariables = ({','.join([str(x) for x in variable_links])})",  # noqa: E501
                        f"{')' if sequence < 0 else ''})\n",
                    ),
                ),
            )
        else:
            outfile.write(
                "\n".join(
                    (
                        f"set {bpd_name} BehaviorSequences[{sequence}]",
                        "(",
                        f'    BehaviorSequenceName = "{sequence_name}",',
                        f"    bEnabledOnSpawn = {enabled_on_spawn},",
                        f"    bSequenceEnabledMutex = {sequence_enabled_mutex},",
                        f"    CustomEnableCondition = {custom_enable_condition},",
                        f"    EventData2 = ({','.join(event_commands)}),",
                        f"    BehaviorData2 = ({','.join(behavior_commands)}),",
                        f"    ConsolidatedOutputLinkData = ({','.join(behavior_link_commands)}),",
                        f"    ConsolidatedVariableLinkData = ({','.join(variable_link_commands)}),",
                        f"    ConsolidatedLinkedVariables = ({','.join([str(x) for x in variable_links])})",  # noqa: E501
                        ")\n",
                    ),
                ),
            )
        if not include_variable_data:
            for variable in _ALL_VARIABLES:
                if not variable.needs_command:
                    continue
                outfile.write(
                    f"set {bpd_name} BehaviorSequences[{sequence}].VariableData[{variable.idx}] "
                    f'(Name="{variable.name}",Type={variable.var_type.name})\n',
                )
