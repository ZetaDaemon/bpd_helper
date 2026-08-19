from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from enum import IntEnum

import bpd_helper


class EBinaryMathOperation:
    class EBoolResult(IntEnum):
        BoolBool_XNOR = 2
        BoolBool_AND = 3
        BoolBool_OR = 4
        BoolBool_XOR = 5
        FloatFloat_Equal = 6
        FloatFloat_Less = 7
        FloatFloat_LessEqual = 8
        FloatFloat_Greater = 9
        FloatFloat_GreaterEqual = 10
        FloatFloat_NotEqual = 11
        IntInt_Equal = 12
        IntInt_Less = 13
        IntInt_LessEqual = 14
        IntInt_Greater = 15
        IntInt_GreaterEqual = 16
        IntInt_NotEqual = 17
        ObjectObject_Equal = 18
        ObjectObject_NotEqual = 19

    class EIntResult(IntEnum):
        IntInt_Add = 1000002
        IntInt_Subtract = 1000003
        IntInt_Mult = 1000004
        IntInt_Divide = 1000005
        IntInt_Power = 1000006
        IntInt_RandomRange = 1000007
        IntInt_Average = 1000008
        IntInt_Min = 1000009
        IntInt_Max = 1000010

    class EFloatResult(IntEnum):
        FloatFloat_Add = 2000002
        FloatFloat_Subtract = 2000003
        FloatFloat_Mult = 2000004
        FloatFloat_Divide = 2000005
        FloatFloat_Power = 2000006
        FloatFloat_RandomRange = 2000007
        FloatFloat_Average = 2000008
        FloatFloat_Min = 2000009
        FloatFloat_Max = 2000010
        VectorVector_Dot = 2000011
        VectorVector_Distance = 2000012

    class EVectorResult(IntEnum):
        VectorVector_Add = 3000002
        VectorVector_Subtract = 3000003
        VectorVector_Divide = 3000004
        VectorVector_Multiply = 3000005
        VectorVector_Project = 3000006
        VectorVector_Cross = 3000007
        VectorVector_NormalizeDifference = 3000008
        VectorVector_Rotate = 3000009


class EUnaryMathOperation:
    class EBoolOperation(IntEnum):
        IsTruthy = 1
        IsFalsey = 2
        ToFloat = 1000001
        ToInt = 2000001
        ToVector = 3000001

    class EIntOperation(IntEnum):
        IsTruthy = 1
        IsFalsey = 2
        ToFloat = 1000001
        Value = 2000001
        Negate = 2000006
        Abs = 2000007
        ToVector = 3000001

    class EFloatOperation(IntEnum):
        IsTruthy = 1
        Negate = 1000002
        Abs = 1000003
        Cos = 1000008
        Sin = 1000009
        Tan = 1000010
        IntRound = 2000001
        IntRoundDown = 2000002
        IntRoundUp = 2000003
        IntRoundAlt = 2000004
        IntTruncate = 2000005
        ToVector = 3000001

    class EVectorOperation(IntEnum):
        IsTruthy = 1
        Magnitude = 1000001
        X = 1000004
        Y = 1000005
        Z = 1000006
        MagnitudeAlt = 1000007
        MagnitudeIntRound = 2000001
        MagnitudeIntRoundDown = 2000002
        MagnitudeIntRoundUp = 2000003
        MagnitudeIntRoundAlt = 2000004
        MagnitudeIntTruncate = 2000005
        Negate = 3000002
        Normalize = 3000003
        Abs = 3000004

    class EObjectOperation(IntEnum):
        IsTruthy = 1
        ToFloat = 1000001
        """Calls ObjToFloat.

        If the object is not a PrimitiveComponent, it returns 0.0
        Otherwise:
            max(Scale3D.X, Scale3D.Y, Scale3D.Z) * Scale
        """

        IsValidInt = 2000001
        VectorIfValid = 3000001
        """If valid returns a vector of all 1's, otherwise it's all 0's."""


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

    @classmethod
    def new_of_self(cls):
        return cls()

    def copy(self):
        val = self.new_of_self()
        for f in fields(self):
            fval = getattr(self, f.name)
            if isinstance(fval, VariableValue):
                fval = fval.copy()
            setattr(val, f.name, fval)
        return val


@dataclass
class SubarrayData(VariableValue):
    """Wrapped GearboxFramework.BehaviorProviderDefinition:SubarrayData."""

    variables: list[int | bpd_helper.BpdVariable] = field(default_factory=list)
    _array_index_and_length: int | None = field(default=None, init=False)

    def resolve(self, sequence: bpd_helper.BehaviorSequence, /) -> dict:
        if self._array_index_and_length is None:
            self._array_index_and_length = sequence.lookup_variables_idx_len(self.variables)
        return {"ArrayIndexAndLength": self._array_index_and_length}

    def copy(self):
        return SubarrayData(
            [x.copy() if isinstance(x, bpd_helper.BpdVariable) else x for x in self.variables],
        )


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
    Operation: int = 0


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
