"""Utility methods for objects"""

from oslo_versionedobjects import fields


BaseEnumField = fields.BaseEnumField
BooleanField = fields.BooleanField
DateTimeField = fields.DateTimeField
Enum = fields.Enum
FloatField = fields.FloatField
IntegerField = fields.IntegerField
ListOfStringsField = fields.ListOfStringsField
NonNegativeFloatField = fields.NonNegativeFloatField
NonNegativeIntegerField = fields.NonNegativeIntegerField
ObjectField = fields.ObjectField
StringField = fields.StringField
UnspecifiedDefault = fields.UnspecifiedDefault


class UUIDField(fields.UUIDField):
    def coerce(self, obj, attr, value):
        if value is None or value == "":
            return self._null(obj, attr)
        else:
            return self._type.coerce(obj, attr, value)


class Numeric(fields.FieldType):
    @staticmethod
    def coerce(obj, attr, value):
        if value is None:
            return value
        f_value = float(value)
        return f_value if not f_value.is_integer() else value


class NumericField(fields.AutoTypedField):
    AUTO_TYPE = Numeric()
