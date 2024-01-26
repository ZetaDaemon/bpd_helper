from bpd_helper import *

[BpdVariable() for _ in range(2)]

OnEquip = EventData(
    "OnEquip",
    output_variables=[
        VariableLinkData([0], "Instigator", EBehaviorVariableLinkType.BVARLINK_Output)
    ],
)
OnUnequip = EventData(
    "OnUnequip",
    output_variables=[
        VariableLinkData([1], "Instigator", EBehaviorVariableLinkType.BVARLINK_Output)
    ],
)

Behavior_ActivateSkill_0 = Behavior(
    "GD_Weap_AssaultRifle.Barrel.AR_Barrel_MyCustomGun:BehaviorProviderDefinition_0.Behavior_ActivateSkill_0",
    [
        VariableLinkData([0], "Context", EBehaviorVariableLinkType.BVARLINK_Context),
        VariableLinkData([0], "AdditionalTargetContext", EBehaviorVariableLinkType.BVARLINK_Input),
    ],
)
Behavior_DeactivateSkill_0 = Behavior(
    "GD_Weap_AssaultRifle.Barrel.AR_Barrel_MyCustomGun:BehaviorProviderDefinition_0.Behavior_DeactivateSkill_0",
    [
        VariableLinkData([1], "Context", EBehaviorVariableLinkType.BVARLINK_Context),
    ],
)
Behavior_DeactivateSkill_1 = Behavior(
    "GD_Weap_AssaultRifle.Barrel.AR_Barrel_MyCustomGun:BehaviorProviderDefinition_0.Behavior_DeactivateSkill_1",
    [
        VariableLinkData([1], "Context", EBehaviorVariableLinkType.BVARLINK_Context),
    ],
)

OnEquip.add_output_link(BehaviorLink(Behavior_ActivateSkill_0))

OnUnequip.add_output_link(BehaviorLink(Behavior_DeactivateSkill_0))
Behavior_DeactivateSkill_0.add_output_link(BehaviorLink(Behavior_DeactivateSkill_1, -1))

generate_bpd("GD_Weap_AssaultRifle.Barrel.AR_Barrel_MyCustomGun:BehaviorProviderDefinition_0")
