# ruff: noqa: N801, D101, D106, N815, N802
# Naming matches the UE objects and functions so those warnings can be ignored.
"""Variable and Event templates.

Clases containing templates for VariableLinkData using partial objects.
Can also generate the EventData for a class which is a BPD Event.

This is written by hand so is by no means an extensive collection, just a bunch of
the one's i've used commonly.

The structure of the classes doesnt not nessasarily represent the UE
classes 1:1, classes that represent a function will sometimes inherit
from other function classes due to having similar function signatures,
this just makes writing the logic here cleaner and has no impact on usage.
"""

from collections.abc import Callable
from functools import partial

from bpd_helper import (
    BehaviorLink,
    EBehaviorVariableLinkType,
    EventData,
    VariableLinkData,
)

type VariableLinkTemplate = Callable[[list[int]], VariableLinkData]


Context: VariableLinkTemplate = partial(
    VariableLinkData,
    property_name="Context",
    link_type=EBehaviorVariableLinkType.BVARLINK_Context,
)
InputVariableLink: Callable[[list[int], str], VariableLinkData] = partial(
    VariableLinkData,
    link_type=EBehaviorVariableLinkType.BVARLINK_Input,
)


class BPD_Event:
    """Base class for BPD Events.

    Used so you can call Event to generate the EventData.

    """

    @classmethod
    def Event(
        cls,
        enabled: bool | None = True,  # noqa: FBT002
        replicate: bool | None = False,  # noqa: FBT002
        max_trigger_count: int | None = 0,
        retrigger_delay: float | None = 0.0,
        filter_object: str | None = "None",
        output_variables: list[VariableLinkData] | None = None,
        output_links: list[BehaviorLink] | None = None,
    ) -> EventData:
        """Create the EventData based on the class' name."""
        return EventData(
            cls.__name__,
            enabled,
            replicate,
            max_trigger_count,
            retrigger_delay,
            filter_object,
            output_variables,
            output_links,
        )


class Behavior_Math:
    class Input:
        A: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="A",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )
        B: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="B",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )

    class Output:
        Result: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Result",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
        )


class Behavior_SimpleMath(Behavior_Math): ...


class Behavior_BoolMath(Behavior_Math): ...


class Behavior_IntMath(Behavior_Math): ...


class Behavior_VectorMath(Behavior_Math): ...


class Behavior_CompareFloat:
    class Input:
        ValueA: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ValueA",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )
        ValueB: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ValueB",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )


class Behavior_CompareValues:
    class Input:
        ValueA: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ValueA",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )
        ContextB: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ContextB",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )
        ValueB: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ValueB",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )


class SkillDefinition:
    class _SkillEvent(BPD_Event):
        """Base for all the SkillDefinition events, dont use.

        All the events on a SkillDefinition have a SkillInstigator
        output at output 0, so a base class to capture this just makes
        things cleaner, it doesnt match anything in UE and should not be
        used.
        """

        SkillInstigator: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="SkillInstigator",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
        )

    class OnActivated(_SkillEvent): ...

    class OnDeactivated(_SkillEvent): ...

    class OnPaused(_SkillEvent): ...

    class OnResumed(_SkillEvent): ...

    class OnMeleeOverrideSkillActivated(_SkillEvent): ...

    class OnThrowGrenadeOverrideSkillActivated(_SkillEvent): ...

    class OnWeaponZoomed(_SkillEvent): ...

    class OnWeaponUnzoomed(_SkillEvent): ...

    class OnWeaponFired(_SkillEvent):
        WeaponFired: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="WeaponFired",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnWeaponReloaded(_SkillEvent):
        WeaponReloaded: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="WeaponReloaded",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnWeaponManuallyReloaded(OnWeaponReloaded): ...

    class OnWeaponSwapped(_SkillEvent):
        NewWeapon: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="NewWeapon",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnShieldDepletedAfterBeingFull(_SkillEvent): ...

    class OnShieldDepleted(_SkillEvent): ...

    class OnShieldFull(_SkillEvent): ...

    class OnKilledEnemy(_SkillEvent):
        Enemy: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Enemy",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        bWasCrit: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasCrit",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )
        HealthDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HealthDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )
        ShieldDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ShieldDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=4,
        )
        ExcessDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ExcessDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=5,
        )

    class OnKilledByEnemy(OnKilledEnemy): ...

    class OnWeaponStartReload(_SkillEvent):
        WeaponReloading: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="WeaponReloading",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnDamagedEnemy(_SkillEvent):
        Enemy: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Enemy",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        bWasCrit: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasCrit",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )
        HealthDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HealthDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )
        ShieldDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ShieldDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=4,
        )
        bWasInjured: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasInjured",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=5,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=6,
        )
        ExcessDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ExcessDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=7,
        )
        PenetrationCount: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="PenetrationCount",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=8,
        )

    class OnDamagedEnemyExposeDamageSurfaceType(OnDamagedEnemy):
        DamageSurfaceType: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="DamageSurfaceType",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=9,
        )

    class OnDamagedFriendly(_SkillEvent):
        Friendly: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Friendly",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        bWasCrit: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasCrit",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )
        HealthDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HealthDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )
        ShieldDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ShieldDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=4,
        )
        ExcessDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ExcessDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=5,
        )

    class OnDamagedByEnemy(_SkillEvent):
        Enemy: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Enemy",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        bWasCrit: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasCrit",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )
        HealthDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HealthDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )
        ShieldDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ShieldDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=4,
        )
        DamageSource: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="DamageSource",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=5,
        )
        ExcessDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ExcessDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=6,
        )

    class OnDamagedByFriendly(OnDamagedFriendly): ...

    class OnPlayerDeathAverted(_SkillEvent): ...

    class OnPlayerRecoveredFromDownState(_SkillEvent): ...

    class OnPlayerResurrected(_SkillEvent): ...

    class OnActionSkillCooldownAbilityActivated(_SkillEvent):
        AutoAimTarget: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="AutoAimTarget",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnActionSkillActiveAbilityActivated(OnActionSkillCooldownAbilityActivated): ...

    class OnDamagedUnawareEnemy(_SkillEvent):
        Enemy: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Enemy",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )
        ExcessDamageDone: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ExcessDamageDone",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )

    class OnDamagedEnemyWithMeleeFromBehind(OnDamagedUnawareEnemy): ...


class ProjectileDefinition:
    class OnSpawn(BPD_Event):
        Instigator: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Instigator",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )

    class OnExplode(BPD_Event):
        Instigator: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="Instigator",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        HitNormal: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitNormal",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )

    class OnHitWater(BPD_Event):
        HitActor: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitActor",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        HitNormal: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitNormal",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )

    class OnTouched(OnHitWater):
        BoneIndex: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="BoneIndex",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )

    class OnHitFlesh(OnTouched): ...

    class OnHitFleshOrArmor(OnTouched): ...

    class OnHitArmor(OnTouched): ...

    class OnHitShields(OnTouched): ...

    class OnHitWall(OnHitWater): ...

    class OnComeToRest(BPD_Event):
        HitNormal: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitNormal",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )

    class OnTookDirectDamage(BPD_Event):
        DamageCauser: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="DamageCauser",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )

    class OnTookRadiusDamage(OnTookDirectDamage): ...

    class OnTookDirectOrRadiusDamage(OnTookDirectDamage): ...

    class OnTimerEvent(BPD_Event):
        SpecializedEventName: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="SpecializedEventName",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )

    class OnCounterEvent(OnTimerEvent): ...

    class OnDamagedEnemy(BPD_Event):
        DamageTaker: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="DamageTaker",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        bWasCrit: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="bWasCrit",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        HealthDamage: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HealthDamage",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        ShieldDamage: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ShieldDamage",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )

    class OnDamagedFriendly(OnDamagedEnemy): ...

    class OnDamagedNeutral(OnDamagedEnemy): ...

    class OnKilledNeutral(BPD_Event):
        KilledObject: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="KilledObject",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )

    class OnKilledFriendly(OnKilledNeutral): ...

    class OnKilledEnemy(OnKilledNeutral): ...

    class _HitEvent(BPD_Event):
        """Base class for hit events, do not use.

        Bunch of hit events have these 3 output variables,
        having them all wrapped up here just makes it cleaner.
        Don't use on it's own.
        """

        HitObject: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitObject",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        HitNormal: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitNormal",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )

    class OnHitDamagableObject(_HitEvent):
        DamageSurfaceType: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="DamageSurfaceType",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=3,
        )
        BoneIndex: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="BoneIndex",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=4,
        )

    class OnHitTheWorld(_HitEvent): ...

    class OnTouchProximity(OnHitDamagableObject): ...

    class OnReflected(BPD_Event):
        HitObject: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitObject",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )
        ReflectedDirection: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="ReflectedDirection",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=1,
        )
        HitLocation: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="HitLocation",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=2,
        )

    class OnHomingTargetChanged(BPD_Event):
        TargetObject: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="TargetObject",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
            connection_index=0,
        )


class Behavior_ModifyTimer:
    class Output:
        TimeRemaining: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="TimeRemaining",
            link_type=EBehaviorVariableLinkType.BVARLINK_Output,
        )


class Behavior_ActivateSkill:
    class Input:
        AdditionalTargetContext: VariableLinkTemplate = partial(
            VariableLinkData,
            property_name="AdditionalTargetContext",
            link_type=EBehaviorVariableLinkType.BVARLINK_Input,
        )
