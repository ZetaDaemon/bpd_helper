# ruff: noqa: F405
from bpd_helper import *  # noqa: F403
from output_links import Behavior_CompareFloat

generate_variables(4)

VAR_INSTIGATOR = 0
VAR_CURRENT_SHIELD_ATTR = 1
VAR_AMP_DRAIN_ATTR = 2
# I'm not sure what this one is.
VAR_UNKNOWN_ATTR = 3

OnWeaponFired = EventData(
    "OnWeaponFired",
    output_variables=[
        VariableLinkData(
            [VAR_INSTIGATOR],
            "SkillInstigator",
            EBehaviorVariableLinkType.BVARLINK_Output,
        ),
    ],
)

Behavior_SetShieldTriggeredState_35 = Behavior(
    "GD_Shields.Skills.Impact_Shield_Skill:BehaviorProviderDefinition_0.Behavior_SetShieldTriggeredState_35",
    [VariableLinkData([VAR_INSTIGATOR], "Context", EBehaviorVariableLinkType.BVARLINK_Context)],
)
Behavior_CompareFloat_4 = Behavior(
    "GD_Shields.Skills.Impact_Shield_Skill:BehaviorProviderDefinition_0.Behavior_CompareFloat_4",
    [
        VariableLinkData([VAR_UNKNOWN_ATTR], "A", EBehaviorVariableLinkType.BVARLINK_Input),
        VariableLinkData([VAR_CURRENT_SHIELD_ATTR], "B", EBehaviorVariableLinkType.BVARLINK_Input),
    ],
)
Behavior_SimpleMath_4 = Behavior(
    "GD_Shields.Skills.Impact_Shield_Skill:BehaviorProviderDefinition_0.Behavior_SimpleMath_4",
    [
        VariableLinkData([VAR_CURRENT_SHIELD_ATTR], "A", EBehaviorVariableLinkType.BVARLINK_Input),
        VariableLinkData([VAR_AMP_DRAIN_ATTR], "B", EBehaviorVariableLinkType.BVARLINK_Input),
        VariableLinkData(
            [VAR_CURRENT_SHIELD_ATTR],
            "Result",
            EBehaviorVariableLinkType.BVARLINK_Output,
        ),
    ],
)
Behavior_PostAkEvent_57 = Behavior(
    "GD_Shields.Skills.Impact_Shield_Skill:BehaviorProviderDefinition_0.Behavior_PostAkEvent_57",
    [VariableLinkData([VAR_INSTIGATOR], "Context", EBehaviorVariableLinkType.BVARLINK_Context)],
)

OnWeaponFired += BehaviorLink(Behavior_SetShieldTriggeredState_35)
Behavior_SetShieldTriggeredState_35 += BehaviorLink(Behavior_CompareFloat_4, -1)
Behavior_CompareFloat_4 += BehaviorLink(Behavior_SimpleMath_4, Behavior_CompareFloat.Equal)
Behavior_SetShieldTriggeredState_35 += BehaviorLink(Behavior_PostAkEvent_57, -1)

generate_bpd("GD_Shields.Skills.Impact_Shield_Skill:BehaviorProviderDefinition_0")
