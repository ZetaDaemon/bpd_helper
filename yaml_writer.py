from __future__ import annotations

from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from behavior_variable_values import EDirectionRelativeToParent
from bpd_helper import EBehaviorVariableType, compile_sequence

if TYPE_CHECKING:
    from bpd_helper import BehaviorSequence, BpdVariable

__all__ = ["generate_bpd_yaml"]


def generate_bpd_yaml(output_path: str | Path, sequences: list[BehaviorSequence]) -> None:
    """Write a standalone BPD object to the given YAML file."""
    document = {
        "Class": "GearboxFramework.BehaviorProviderDefinition",
        "BehaviorSequences": [_sequence_yaml(sequence) for sequence in sequences],
    }
    contents = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    Path(output_path).write_text(contents, encoding="utf-8")


def _sequence_yaml(sequence: BehaviorSequence) -> dict[str, Any]:
    compiled = compile_sequence(sequence)
    result: dict[str, Any] = {
        "BehaviorSequenceName": sequence.name,
        "bEnabledOnSpawn": sequence.enabled_on_spawn,
        "bSequenceEnabledMutex": sequence.enabled_mutex,
        "EventData2": [
            {
                "UserData": {
                    "EventName": event.event_name,
                    "bEnabled": event.enabled,
                    "bReplicate": event.replicate,
                    "MaxTriggerCount": event.max_trigger_count,
                    "ReTriggerDelay": float(event.retrigger_delay),
                    "FilterObject": (
                        None if event.filter_object == "None" else event.filter_object
                    ),
                },
                "OutputVariables": {"ArrayIndexAndLength": variables},
                "OutputLinks": {"ArrayIndexAndLength": outputs},
            }
            for event, variables, outputs in compiled.events
        ],
        "BehaviorData2": [
            {
                "Behavior": (
                    behavior.full_name
                    if behavior.full_name is not None
                    else f"./{behavior.short_name}"
                ),
                "LinkedVariables": {"ArrayIndexAndLength": variables},
                "OutputLinks": {"ArrayIndexAndLength": outputs},
            }
            for behavior, variables, outputs in compiled.behaviors
        ],
        "VariableData": [
            _variable_yaml(sequence, index, variable)
            for index, variable in enumerate(sequence.variables)
        ],
        "ConsolidatedOutputLinkData": [
            {"LinkIdAndLinkedBehavior": target, "ActivateDelay": float(link.delay)}
            for link, target in compiled.output_links
        ],
        "ConsolidatedVariableLinkData": [
            {
                "PropertyName": link.property_name,
                "VariableLinkType": link.link_type.name,
                "ConnectionIndex": int(link.connection_index),
                "LinkedVariables": {"ArrayIndexAndLength": variables},
            }
            for link, variables in compiled.variable_links
        ],
        "ConsolidatedLinkedVariables": compiled.linked_variables,
    }

    if sequence.enable_condition != "None":
        result["CustomEnableCondition"] = sequence.enable_condition

    return result


def _variable_yaml(sequence: BehaviorSequence, index: int, variable: BpdVariable) -> dict[str, Any]:
    if variable.var_type is EBehaviorVariableType.BVAR_None:
        msg = f"{sequence.name!r}.VariableData[{index}] requires a concrete variable type."
        raise ValueError(msg)

    row = variable.to_dict(sequence)
    value = row.pop("Value")
    if value is None:
        return row

    if isinstance(value, IntEnum):
        value = int(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, EDirectionRelativeToParent):
                value[key] = item.name
            elif isinstance(item, IntEnum) or key == "bDefaultToSourceLocation":
                value[key] = int(item)  # pyright: ignore[reportUnknownArgumentType]

    row["Value"] = value
    return row
