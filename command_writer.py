from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import TYPE_CHECKING

from bpd_helper import EBehaviorVariableType, compile_sequence

if TYPE_CHECKING:
    from bpd_helper import BehaviorSequence

__all__ = ["generate_bpd", "generate_bpd_sequence"]

VAR_LINK_COMMAND_STRING: str = (
    '(PropertyName="{}",'
    "VariableLinkType={},"
    "ConnectionIndex={},"
    "LinkedVariables=(ArrayIndexAndLength={}),"
    "CachedProperty=None)"
)

EVENT_COMMAND_STRING: str = (
    '(UserData=(EventName="{}",'
    "bEnabled={},"
    "bReplicate={},"
    "MaxTriggerCount={},"
    "ReTriggerDelay={},"
    "FilterObject={}),"
    "OutputVariables=(ArrayIndexAndLength={}),"
    "OutputLinks=(ArrayIndexAndLength={}))"
)

BEHAVIOR_COMMAND_STRING: str = (
    "(Behavior={},LinkedVariables=(ArrayIndexAndLength={}),OutputLinks=(ArrayIndexAndLength={}))"
)

BEHAVIOR_LINK_COMMAND_STR: str = "(LinkIdAndLinkedBehavior={},ActivateDelay={})"


def _generate_sequence_command(sequence: BehaviorSequence, bpd_name: str) -> list[str]:
    compiled = compile_sequence(sequence)

    event_commands = [
        EVENT_COMMAND_STRING.format(
            event.event_name,
            event.enabled,
            event.replicate,
            event.max_trigger_count,
            f"{event.retrigger_delay:f}",
            event.filter_object,
            variable_span,
            output_span,
        )
        for event, variable_span, output_span in compiled.events
    ]

    behavior_commands = [
        BEHAVIOR_COMMAND_STRING.format(
            behavior.full_name
            if behavior.full_name is not None
            else f"{bpd_name}.{behavior.short_name}",
            variable_span,
            output_span,
        )
        for behavior, variable_span, output_span in compiled.behaviors
    ]

    behavior_link_commands = [
        BEHAVIOR_LINK_COMMAND_STR.format(target, f"{link.delay:f}")
        for link, target in compiled.output_links
    ]

    variable_link_commands = [
        VAR_LINK_COMMAND_STRING.format(
            link.property_name, link.link_type.name, link.connection_index, variable_span
        )
        for link, variable_span in compiled.variable_links
    ]

    return [
        "(",
        f'    BehaviorSequenceName = "{sequence.name}",',
        f"    bEnabledOnSpawn = {sequence.enabled_on_spawn},",
        f"    bSequenceEnabledMutex = {sequence.enabled_mutex},",
        f"    CustomEnableCondition = {sequence.enable_condition},",
        f"    EventData2 = ({','.join(event_commands)}),",
        f"    BehaviorData2 = ({','.join(behavior_commands)}),",
        f"    ConsolidatedOutputLinkData = ({','.join(behavior_link_commands)}),",
        f"    ConsolidatedVariableLinkData = ({','.join(variable_link_commands)}),",
        (
            "    ConsolidatedLinkedVariables = "
            f"({','.join(str(index) for index in compiled.linked_variables)})"
        ),
        ")",
    ]


def _get_sequence_variable_commands(
    sequence: BehaviorSequence, bpd_name: str, sequence_idx: int
) -> list[str]:
    commands: list[str] = []

    set_all = EBehaviorVariableType.BVAR_None not in [var.var_type for var in sequence.variables]

    for idx, variable in enumerate(sequence.variables):
        match variable.var_type:
            case EBehaviorVariableType.BVAR_None:
                continue
            case (
                EBehaviorVariableType.BVAR_NamedVariable
                | EBehaviorVariableType.BVAR_NamedKismetVariable
            ):
                d = variable.to_dict(sequence)
                d.pop("Value")
            case _:
                d = variable.to_dict(sequence)
                if d["Value"] is None:
                    d.pop("Value")

        if set_all:
            commands.append(f"{json.dumps(d, separators=(',', ':'))}")
        else:
            commands.append(
                f"set_variable {bpd_name} {sequence_idx} "
                f"{idx} {json.dumps(d, separators=(',', ':'))!s}\n"
            )
    if set_all:
        return [f"set_variable_data {bpd_name} {sequence_idx} [{','.join(commands)}]\n"]
    return commands


def generate_bpd(bpd_name: str, sequences: list[BehaviorSequence], set_early: bool = True) -> None:
    """Generate the bpd.

    Generates the bpd for the data in _ALL_EVENTS and _ALL_VARIABLES
    and writes to a file, the file name is based on bpd_name.

    Events are all automatically included, regardless of if they link to behaviors,
    since events can have outputs they have a use beyond just triggering behaviors.
    Only Behaviors linked to by Events and other Behaviors will be included.

    Arguments:
        bpd_name: The name of the BPD, will also be used as the file name
                    with any : replaced with . due to windows file limitations
        sequences: The list of sequences to generate commands for.
        set_early: Should the command be generated as a set_early command.

    """
    caller_dir = Path(inspect.stack()[1].filename).parent

    outfile_path = caller_dir / f"{bpd_name.replace(':', '.')}.txt"

    sequence_commands: list[str] = []
    variable_commands: list[str] = []
    for idx, sequence in enumerate(sequences):
        cmd = _generate_sequence_command(sequence, bpd_name)
        if set_early:
            cmd = [line.lstrip() for line in cmd]
            sequence_commands.append("".join(cmd))
        else:
            cmd = [f"    {line}" for line in cmd]
            sequence_commands.append("\n".join(cmd))
        variable_commands.extend(_get_sequence_variable_commands(sequence, bpd_name, idx))

    with outfile_path.open("w") as outfile:
        if set_early:
            _ = outfile.write(
                f"set_early {bpd_name} BehaviorSequences ({','.join(sequence_commands)})"
            )
        else:
            _ = outfile.write(
                f"set {bpd_name} BehaviorSequences\n(\n{',\n'.join(sequence_commands)}\n)"
            )
        _ = outfile.write("\n")
        outfile.writelines(variable_commands)


def generate_bpd_sequence(bpd_name: str, sequence: BehaviorSequence, idx: int) -> None:
    """Generate the command to set a specific bpd sequence."""
    caller_dir = Path(inspect.stack()[1].filename).parent

    outfile_path = caller_dir / f"{bpd_name.replace(':', '.')}[{idx}].txt"

    variable_commands: list[str] = []
    cmd = _generate_sequence_command(sequence, bpd_name)
    cmd = [f"{line}" for line in cmd]
    sequence_command = "\n".join(cmd)
    variable_commands.extend(_get_sequence_variable_commands(sequence, bpd_name, idx))

    with outfile_path.open("w") as outfile:
        _ = outfile.write(f"set {bpd_name} BehaviorSequences[{idx}]\n{sequence_command}")
        _ = outfile.write("\n")
        outfile.writelines(variable_commands)
