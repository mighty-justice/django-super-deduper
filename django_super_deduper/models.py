from typing import List

from django.db.models import Field, Model


class ModelMeta(object):

    def __init__(self, instance: Model) -> None:
        self.options = instance._meta

    @staticmethod
    def is_related_field(field: Field):
        return (field.one_to_many or field.one_to_one or field.many_to_many) and field.related_model._meta.managed

    @property
    def related_fields(self) -> List[Field]:
        return [f for f in self.options.get_fields() if ModelMeta.is_related_field(f)]

    @property
    def editable_fields(self) -> List[Field]:
        return [f for f in self.options.fields if f.editable]

    @property
    def model_name(self) -> str:
        return self.options.model.__name__
