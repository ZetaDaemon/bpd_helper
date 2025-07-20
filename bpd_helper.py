from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, ClassVar
import struct
import inspect
import os

__all__ = [
    "Behavior",
    "BehaviorLink",
    "EBehaviorVariableType",
    "EBehaviorVariableLinkType",
    "edit_variable",
    "EventData",
    "generate_bpd",
    "generate_variables",
    "VariableLinkData",
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

_ALL_EVENTS: List[EventData] = []
_ALL_BEHAVIORS: List[Behavior] = []
_ALL_VARIABLES: List[BpdVariable] = []


class EBehaviorVariableType(Enum):
    BVAR_None = auto()
    BVAR_Bool = auto()
    BVAR_Int = auto()
    BVAR_Float = auto()
    BVAR_Vector = auto()
    BVAR_Object = auto()
    BVAR_AllPlayers = auto()
    BVAR_Attribute = auto()
    BVAR_InstanceData = auto()
    BVAR_NamedVariable = auto()
    BVAR_NamedKismetVariable = auto()
    BVAR_DirectionVector = auto()
    BVAR_AttachmentLocation = auto()
    BVAR_UnaryMath = auto()
    BVAR_BinaryMath = auto()
    BVAR_Flag = auto()


class EBehaviorVariableLinkType(Enum):
    BVARLINK_Unknown = auto()
    BVARLINK_Context = auto()
    BVARLINK_Input = auto()
    BVARLINK_Output = auto()


@dataclass
class BpdVariable:
    """
    An object to represent an entry in the VariableData array.

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

    _command_str: ClassVar[str] = '(Name="{}",Type={})'

    def __post_init__(self):
        if self.idx == -1:
            self.idx = len(_ALL_VARIABLES)
            _ALL_VARIABLES.append(self)
            return
        if len(_ALL_VARIABLES) < (self.idx + 1):
            _ALL_VARIABLES.extend(
                [BpdVariable() for _ in range(self.idx + 1 - len(_ALL_VARIABLES))]
            )
        _ALL_VARIABLES[self.idx] = self


def generate_variables(count: int) -> None:
    """generates 'count' BpdVariable objects"""
    for _ in range(count):
        BpdVariable()


def edit_variable(idx: int, var_type: EBehaviorVariableType, name: str) -> None:
    """
    sets the properties of the BpdVariable at the specified index and enables 'needs_command'
    """
    var = _ALL_VARIABLES[idx]
    var.idx = idx
    var.var_type = var_type
    var.name = name
    var.needs_command = True


@dataclass
class VariableLinkData:
    """
    An object to represent an entry in the ConsolidatedVariableLinkData array.

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
        connection_index: the ConnectionIndex
    """

    variable_indexes: List[int]
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

    def __post_init__(self):
        if not isinstance(self.variable_indexes, list):
            raise TypeError("variable_indexes is not a list")
        for var_idx in self.variable_indexes:
            if var_idx >= len(_ALL_VARIABLES):
                raise IndexError(
                    f"Variable index {var_idx} out of range of defined variables."
                )


@dataclass
class EventData:
    """
    An object to represent an entry in the EventData2 array.

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
    output_variables: List[VariableLinkData] = field(default_factory=lambda: [])
    output_links: List[BehaviorLink] = field(default_factory=lambda: [])

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

    def __post_init__(self):
        _ALL_EVENTS.append(self)

    def gen_output_link(self, behavior: Behavior, link_id: int = 0, delay: int = 0):
        self.output_links.append(BehaviorLink(behavior, link_id, delay))

    def add_output_link(self, link: BehaviorLink):
        """Add a BehaviorLink to output_links"""
        self.output_links.append(link)

    def __iadd__(self, link: BehaviorLink):
        self.output_links.append(link)
        return self


@dataclass(unsafe_hash=True)
class Behavior:
    """
    An object to represent an entry in the BehaviorData2 array.

    Attributes:
        behavior: the Behavior property
        linked_variables: list of VariableLinkData for the LinkedVariables
        output_links: list of BehaviorLink for the OutputLinks

    """

    behavior: str
    linked_variables: List[VariableLinkData] = field(
        default_factory=lambda: [], hash=False
    )
    output_links: List[BehaviorLink] = field(default_factory=lambda: [], hash=False)

    _variables_ArrayIndexAndLength: ClassVar[int] = 0
    _output_ArrayIndexAndLength: ClassVar[int] = 0
    _command_str: ClassVar[str] = (
        "(Behavior={},LinkedVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))"
    )

    def __post_init__(self):
        _ALL_BEHAVIORS.append(self)

    def gen_output_link(self, behavior: Behavior, link_id: int = 0, delay: int = 0):
        self.output_links.append(BehaviorLink(behavior, link_id, delay))

    def add_output_link(self, link: BehaviorLink):
        """Add a BehaviorLink to output_links"""
        self.output_links.append(link)

    def __iadd__(self, link: BehaviorLink):
        self.output_links.append(link)
        return self


@dataclass
class BehaviorLink:
    """
    An object to represent an entry in the ConsolidatedOutputLinkData array.

    Attributes:
        behavior: the Behavior to link to
        link_id: the id to use for the LinkIdAndLinkedBehavior
        delay: the ActivateDelay property
    """

    behavior: Behavior
    link_id: int = 0
    delay: float = 0

    _command_str: ClassVar[str] = "(LinkIdAndLinkedBehavior={},ActivateDelay={})"


def get_arrayindexandlength(idx: int, length: int) -> int:
    """Converts an index and length into a single ArrayIndexAndLength"""
    if length == 0:
        return 0
    return struct.unpack("<i", struct.pack("<HH", length, idx))[0]


def get_linkidandlinkedbehavior(link_id: int, behavior_idx: int) -> int:
    """Converts an id and behavior idx into a single LinkIdAndLinkedBehavior"""
    return struct.unpack("<i", struct.pack("<Hxb", behavior_idx, link_id))[0]


def get_var_link_commands(
    var_links: List[VariableLinkData], variable_links: List[int]
) -> List[str]:
    """
    generates all the individual variable link commands

    Arguments:
        var_links: the list of VariableLinkData to make commands for
        variable_links: list of indexes to Variables, will be the ConsolidatedLinkedVariables
    """
    variable_link_commands = []
    for var_link in var_links:
        idx = 0
        length = len(var_link.variable_indexes)
        if length > 1:
            idx = len(variable_links)
            variable_links.extend(var_link.variable_indexes)
        elif length == 1:
            idx = var_link.variable_indexes[0]
        command_str = var_link._command_str.format(
            var_link.property_name,
            var_link.link_type.name,
            var_link.connection_index,
            get_arrayindexandlength(idx, length),
        )
        variable_link_commands.append(command_str)
    return variable_link_commands


def get_behavior_link_commands(
    behaviour_links: List[BehaviorLink], known_behaviors: List[Behavior]
) -> List[str]:
    """
    generates all the individual behavior link commands

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
            get_linkidandlinkedbehavior(link.link_id, idx), link.delay
        )
        behavior_link_commands.append(command_str)
    return behavior_link_commands


def generate_bpd(
    bpd_name: str,
    sequence: int = 0,
    sequence_name: str = "Default",
    enabled_on_spawn: bool = True,
    sequence_enabled_mutex: bool = False,
    custom_enable_condition: str = "None",
    include_variable_data: bool = False,
):
    """
    Generate's the bpd for the data in _ALL_EVENTS and _ALL_VARIABLES
    and writes to a file

    Arguments:
        bpd_name: the name of the BPD, will also be used as the file name
                    with any : replaced with . due to windows file limitations
        sequence: index in the BehaviorSequences as only one can be edited at a time
    """
    caller_path = os.path.dirname(inspect.stack()[1].filename)
    event_commands: List[str] = []
    behavior_commands: List[str] = []
    variable_data_commands: List[str] = []
    behavior_link_commands: List[str] = []
    variable_link_commands: List[str] = []
    variable_links: List[int] = [x for x in range(len(_ALL_VARIABLES))]
    behavior_stack: List[Behavior] = []
    known_behaviors: List[Behavior] = []
    for event in _ALL_EVENTS:
        output_vars = get_arrayindexandlength(
            len(variable_link_commands), len(event.output_variables)
        )
        output_links = get_arrayindexandlength(
            len(behavior_link_commands), len(event.output_links)
        )

        variable_link_commands.extend(
            get_var_link_commands(event.output_variables, variable_links)
        )

        # Find unqiue set of unseen behaviours, add to stack in reverse order so they will be handled in order linked to
        new_behaviors = reversed(
            list(
                {
                    link.behavior
                    for link in event.output_links
                    if link.behavior not in known_behaviors
                }
            )
        )
        behavior_stack.extend(new_behaviors)

        behavior_link_commands.extend(
            get_behavior_link_commands(event.output_links, known_behaviors)
        )

        command_str = event._command_str.format(
            event.event_name,
            event.enabled,
            event.replicate,
            event.max_trigger_count,
            event.retrigger_delay,
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
                len(variable_link_commands), len(behavior.linked_variables)
            )
            variable_link_commands.extend(
                get_var_link_commands(behavior.linked_variables, variable_links)
            )

            behavior._output_ArrayIndexAndLength = get_arrayindexandlength(
                len(behavior_link_commands), len(behavior.output_links)
            )

            new_behaviors = reversed(
                list(
                    {
                        link.behavior
                        for link in behavior.output_links
                        if link.behavior not in known_behaviors
                    }
                )
            )
            behavior_stack.extend(new_behaviors)

            behavior_link_commands.extend(
                get_behavior_link_commands(behavior.output_links, known_behaviors)
            )

    for behavior in known_behaviors:
        command_str = behavior._command_str.format(
            behavior.behavior,
            behavior._variables_ArrayIndexAndLength,
            behavior._output_ArrayIndexAndLength,
        )
        behavior_commands.append(command_str)

    if include_variable_data:
        for variable in _ALL_VARIABLES:
            variable_data_commands.append(
                f'(Name="{variable.name}",Type={variable.var_type.name})'
            )

    with open(
        f"{caller_path}/{bpd_name.replace(':','.')}[{sequence}].txt", "w"
    ) as FILE:
        if include_variable_data:
            FILE.write(
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
                        f"    VariableData = ({','.join(variable_data_commands)}),",
                        f"    ConsolidatedOutputLinkData = ({','.join(behavior_link_commands)}),",
                        f"    ConsolidatedVariableLinkData = ({','.join(variable_link_commands)}),",
                        f"    ConsolidatedLinkedVariables = ({','.join([str(x) for x in variable_links])})",
                        ")\n",
                    )
                )
            )
        else:
            FILE.write(
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
                        f"    ConsolidatedLinkedVariables = ({','.join([str(x) for x in variable_links])})",
                        ")\n",
                    )
                )
            )
        if not include_variable_data:
            for variable in _ALL_VARIABLES:
                if not variable.needs_command:
                    continue
                FILE.write(
                    f'set {bpd_name} BehaviorSequences[{sequence}].VariableData[{variable.idx}] (Name="{variable.name}",Type={variable.var_type.name})\n'
                )
