from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, ClassVar

__all__ = [
    "Behavior",
    "BehaviorLink",
    "BpdVariable",
    "EBehaviorVariableType",
    "EBehaviorVariableLinkType",
    "EventData",
    "generate_bpd",
    "VariableLinkData",
]

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
    BVAR_MAX = auto()


class EBehaviorVariableLinkType(Enum):
    BVARLINK_Unknown = auto()
    BVARLINK_Context = auto()
    BVARLINK_Input = auto()
    BVARLINK_Output = auto()
    BVARLINK_MAX = auto()


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
        command_str: string used to generate variable commands
    """

    var_type: EBehaviorVariableType = EBehaviorVariableType.BVAR_MAX
    name: str = ""
    idx: int = -1
    needs_command: bool = False

    command_str: ClassVar[str] = '(Name="{}",Type={})'

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
        vars: list of variable indexes to link to
        name: the PropertyName
        connection_index: the ConnectionIndex
        command_str: string used to generate variable commands
    """

    vars: List[int]
    name: str
    link_type: EBehaviorVariableLinkType
    connection_index: int = 0

    command_str: ClassVar[
        str
    ] = '(PropertyName="{}",VariableLinkType={},ConnectionIndex={},LinkedVariables=(ArrayIndexAndLength={}),CachedProperty=None)'


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

    command_str: ClassVar[
        str
    ] = '(UserData=(EventName="{}",bEnabled={},bReplicate={},MaxTriggerCount={},ReTriggerDelay={},FilterObject={}),OutputVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))'

    def __post_init__(self):
        _ALL_EVENTS.append(self)

    def add_output_link(self, link: BehaviorLink):
        self.output_links.append(link)


@dataclass(unsafe_hash=True)
class Behavior:
    behavior: str
    linked_variables: List[VariableLinkData] = field(default_factory=lambda: [], hash=False)
    output_links: List[BehaviorLink] = field(default_factory=lambda: [], hash=False)

    variables_ArrayIndexAndLength: ClassVar[int] = 0
    output_ArrayIndexAndLength: ClassVar[int] = 0
    command_str: ClassVar[
        str
    ] = "(Behavior={},LinkedVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))"

    def __post_init__(self):
        _ALL_BEHAVIORS.append(self)

    def add_output_link(self, link: BehaviorLink):
        self.output_links.append(link)


@dataclass
class BehaviorLink:
    behavior: Behavior
    link_id: int = 0
    delay: int = 0

    command_str: ClassVar[str] = "(LinkIdAndLinkedBehavior={},ActivateDelay={})"


def get_arrayindexandlength(idx: int, length: int):
    if length == 0:
        return 0
    return idx << 16 | length


def get_linkidandlinkedbehavior(id: int, idx: int):
    return id << 24 | idx


def get_var_link_commands(var_links: List[VariableLinkData], variable_links: List[int]):
    variable_link_commands = []
    for var_link in var_links:
        idx = 0
        length = len(var_link.vars)
        if length > 1:
            idx = len(variable_links)
            variable_links.extend(var_link.vars)
        elif length == 1:
            idx = var_link.vars[0]
        command_str = var_link.command_str.format(
            var_link.name,
            var_link.link_type.name,
            var_link.connection_index,
            get_arrayindexandlength(idx, length),
        )
        variable_link_commands.append(command_str)
    return variable_link_commands


def get_behavior_link_commands(
    behaviour_links: List[BehaviorLink], known_behaviors: List[Behavior]
):
    behavior_link_commands = []
    for link in behaviour_links:
        if link.behavior not in known_behaviors:
            known_behaviors.append(link.behavior)
        idx = known_behaviors.index(link.behavior)
        command_str = link.command_str.format(
            get_linkidandlinkedbehavior(link.link_id, idx), link.delay
        )
        behavior_link_commands.append(command_str)
    return behavior_link_commands


def generate_bpd(bpd_name: str, sequence: int = 0):
    event_commands: List[str] = []
    behavior_commands: List[str] = []
    behavior_link_commands: List[str] = []
    variable_link_commands: List[str] = []
    variable_links: List[int] = [x for x in range(len(_ALL_VARIABLES))]
    behavior_stack: List[Behavior] = []
    known_behaviors: List[Behavior] = []
    for event in _ALL_EVENTS:
        output_vars = get_arrayindexandlength(
            len(variable_link_commands), len(event.output_variables)
        )
        output_links = get_arrayindexandlength(len(behavior_link_commands), len(event.output_links))

        variable_link_commands.extend(get_var_link_commands(event.output_variables, variable_links))

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

        command_str = event.command_str.format(
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
            behavior.variables_ArrayIndexAndLength = get_arrayindexandlength(
                len(variable_link_commands), len(behavior.linked_variables)
            )
            variable_link_commands.extend(
                get_var_link_commands(behavior.linked_variables, variable_links)
            )

            behavior.output_ArrayIndexAndLength = get_arrayindexandlength(
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
        command_str = behavior.command_str.format(
            behavior.behavior,
            behavior.variables_ArrayIndexAndLength,
            behavior.output_ArrayIndexAndLength,
        )
        behavior_commands.append(command_str)

    with open(f"{bpd_name.replace(':','.')}[{sequence}].txt", "w") as FILE:
        FILE.write(
            f"set {bpd_name} BehaviorSequences[{sequence}].EventData2 ({','.join(event_commands)})\n"
        )
        FILE.write(
            f"set {bpd_name} BehaviorSequences[{sequence}].BehaviorData2 ({','.join(behavior_commands)})\n"
        )
        FILE.write(
            f"set {bpd_name} BehaviorSequences[{sequence}].ConsolidatedOutputLinkData ({','.join(behavior_link_commands)})\n"
        )
        FILE.write(
            f"set {bpd_name} BehaviorSequences[{sequence}].ConsolidatedVariableLinkData ({','.join(variable_link_commands)})\n"
        )
        FILE.write(
            f"set {bpd_name} BehaviorSequences[{sequence}].ConsolidatedLinkedVariables ({','.join([str(x) for x in variable_links])})\n"
        )
        for variable in _ALL_VARIABLES:
            if not variable.needs_command:
                continue
            FILE.write(
                f'set {bpd_name} BehaviorSequences[{sequence}].VariableData[{variable.idx}] (Name="{variable.name}",Type={variable.var_type.name})\n'
            )
