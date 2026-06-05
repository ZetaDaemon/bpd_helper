# ruff: noqa: N801, D101
# Naming matches the UE objects and functions so those warnings can be ignored.
"""Various behavior output links as enums.

Allows for writing more readable behaviors so you dont
have to have magic numbers for the output links.

This is not nessasarily an extensive collection as it is written by hand.
"""

from enum import IntEnum


class Behavior_CompareValues(IntEnum):
    LessThan = 3
    LessThanOrEqual = 0
    Equal = 2
    GreaterThan = 1
    GreaterThanOrEqual = 4


class Behavior_CompareFloat(IntEnum):
    LessThan = 0
    Equal = 1
    GreaterThan = 2


class Behavior_CompareInt(IntEnum):
    LessThan = 0
    Equal = 1
    GreaterThan = 2


class Behavior_CompareObject(IntEnum):
    Same = 0
    Different = 1


class Behavior_CompareBool(IntEnum):
    IsTrue = 0
    IsFalse = 1


class Behavior_Metronome(IntEnum):
    Tick = 1


class Behavior_Gate(IntEnum):
    Open = 0
    Closed = 1


class EDamageSourceSwitchValues(IntEnum):
    Grenade = 1
    Melee = 2
    Rocket = 3
    Skill = 4
    Statuseffect = 5
    RanIntoByVehicle = 6
    RanOverByVehicle = 7
    Crushed = 8
    Fall = 9
    Pistol = 10
    SubMachineGun = 11
    Shotgun = 12
    MachineGun = 13
    Sniper = 14
    CustomCrate = 15


class Behavior_FireShot(IntEnum):
    FiredAllShots = 0
    FiredShot = 1


class Behavior_SpawnProjectile(IntEnum):
    SpawnedAllProjectiles = 0
    SpawnedProjectile = 1


class Behavior_OpinionSwitch(IntEnum):
    Enemy = 0
    Neutral = 1
    Friendly = 2
