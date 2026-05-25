from pyasn1.type import univ, namedtype, constraint, char

# -------------------------------------------------
# Sensor Type (constraint)
# -------------------------------------------------
class SensorType(char.UTF8String):
    subtypeSpec = constraint.ConstraintsUnion(
        constraint.SingleValueConstraint("Temperature", "Pressure")
    )

# -------------------------------------------------
# Values = SEQUENCE OF REAL
# -------------------------------------------------
class Values(univ.SequenceOf):
    componentType = univ.Real()

# -------------------------------------------------
# Main structure
# -------------------------------------------------
class TimeSeries(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("SensorID", univ.Integer()),
        namedtype.NamedType("Type", SensorType()),
        namedtype.NamedType("Values", Values())
    )