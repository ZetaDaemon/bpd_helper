from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from enum import IntEnum

import bpd_helper


class EDirectionRelativeToParent(IntEnum):
    """GearboxFramework.BehaviorHelpers:EDirectionRelativeToParent."""

    DIRECTION_Default = 0
    DIRECTION_ParentOrientation = 1
    DIRECTION_InverseParentOrientation = 2
    DIRECTION_ParentVelocity = 3
    DIRECTION_InverseParentVelocity = 4
    DIRECTION_Random = 5
    DIRECTION_RandomUpwards = 6
    DIRECTION_RandomDownwards = 7
    DIRECTION_RandomOnHorizontalPlane = 8
    DIRECTION_StraightUp = 9
    DIRECTION_StraightDown = 10
    DIRECTION_StraightTowardTarget = 11
    DIRECTION_ParentAimDirection = 12
    DIRECTION_InverseParentAimDirection = 13
    DIRECTION_InverseTearOffMomentum = 14
    DIRECTION_MAX = 15


class EBinaryMathOperation(IntEnum):
    """WillowGame.Behavior_SimpleMath:EBinaryMathOperation."""

    BINARYMATH_Add = 0
    BINARYMATH_Sub = 1
    BINARYMATH_Mul = 2
    BINARYMATH_Div = 3
    BINARYMATH_Pow = 4
    BINARYMATH_Rand = 5
    BINARYMATH_Avg = 6
    BINARYMATH_Min = 7
    BINARYMATH_Maximum = 8
    BINARYMATH_NoChange = 9
    BINARYMATH_MAX = 10


@dataclass
class VariableValue(ABC):
    def resolve(
        self,
        sequence: bpd_helper.BehaviorSequence,
        /,
    ) -> dict[str, int | float | bool | str]:
        result = {}
        for f in fields(self):
            if (fval := getattr(self, f.name)) == f.default:
                continue
            if isinstance(fval, VariableValue):
                fval = fval.resolve(sequence)
            result[f.name] = fval
        return result


@dataclass
class SubarrayData(VariableValue):
    """Wrapped GearboxFramework.BehaviorProviderDefinition:SubarrayData."""

    variables: list[int | bpd_helper.BpdVariable] = field(default_factory=list)
    _array_index_and_length: int | None = field(default=None, init=False)

    def resolve(self, sequence: bpd_helper.BehaviorSequence, /) -> dict:
        if self._array_index_and_length is None:
            self._array_index_and_length = sequence.lookup_variables_idx_len(self.variables)
        return {"ArrayIndexAndLength": self._array_index_and_length}


@dataclass
class Vector(VariableValue):
    """Wrapped Core.Object:Vector."""

    Pitch: float = 0
    Yaw: float = 0
    Roll: float = 0


@dataclass
class Rotator(VariableValue):
    """Wrapped Core.Object:Rotator."""

    X: float = 0
    Y: float = 0
    Z: float = 0


@dataclass
class AttributeInitializationData(VariableValue):
    """Wrapped Engine.AttributeInitializationDefinition:AttributeInitializationData."""

    BaseValueConstant: float = 0
    BaseValueAttribute: str = "None"
    InitializationDefinition: str = "None"
    BaseValueScaleConstant: float = 0


@dataclass
class BVVector(VariableValue):
    Value: Vector | None = field(default=None)


@dataclass
class BVAttributeData(VariableValue):
    ContextVariable: SubarrayData | None = field(default=None)
    Value: AttributeInitializationData | None = field(default=None)


@dataclass
class BVDirectionVectorData(VariableValue):
    Direction: EDirectionRelativeToParent = EDirectionRelativeToParent.DIRECTION_Default
    ParentVariable: SubarrayData | None = field(default=None)
    DefaultDirection: Vector | None = field(default=None)
    DefaultDirectionVariable: SubarrayData | None = field(default=None)
    AdditionalRotation: Rotator | None = field(default=None)
    DefaultConeAroundDirection: float = 0
    ConeVariable: SubarrayData | None = field(default=None)


@dataclass
class BVAttachmentLocationData(VariableValue):
    SourceVariable: SubarrayData | None = field(default=None)
    bDefaultToSourceLocation: bool = False
    DefaultLocation: Vector | None = field(default=None)
    DefaultLocationVariable: SubarrayData | None = field(default=None)


@dataclass
class BVInstanceData(VariableValue):
    ContextVariable: SubarrayData | None = field(default=None)
    InstanceDataName: str = "None"


@dataclass
class BVBinaryMathData(VariableValue):
    OperandA: SubarrayData | None = field(default=None)
    OperandB: SubarrayData | None = field(default=None)
    Operation: EBinaryMathOperation = EBinaryMathOperation.BINARYMATH_Add


@dataclass
class BVUnaryMathData(VariableValue):
    Operand: SubarrayData | None = field(default=None)
    Operation: int = 0


@dataclass
class BVFlagData(VariableValue):
    ContextVariable: SubarrayData | None = field(default=None)
    FlagDef: str = "None"


type BehaviorVariableDataValue = (
    int
    | float
    | bool
    | str
    | BVVector
    | BVAttributeData
    | BVDirectionVectorData
    | BVAttachmentLocationData
    | BVInstanceData
    | BVBinaryMathData
    | BVUnaryMathData
    | BVFlagData
    | None
)
