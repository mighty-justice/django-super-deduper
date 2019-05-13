import logging
from typing import List, Tuple

from django.core.exceptions import ValidationError
from django.core.serializers import serialize
from django.db.models import Field, Model

from .models import ModelMeta

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class MergedModelInstance(object):

    def __init__(self, primary_object: Model, keep_old=True, merge_field_values=True) -> None:
        self.primary_object = primary_object
        self.keep_old = keep_old
        self.merge_field_values = merge_field_values
        self.model_meta = ModelMeta(primary_object)
        self.modified_related_objects = []  # type: List

    @classmethod
    def _create(
        cls,
        primary_object: Model,
        alias_objects: List[Model],
        keep_old=True,
        merge_field_values=True,
    ) -> 'MergedModelInstance':
        merged_model_instance = cls(primary_object, keep_old=keep_old, merge_field_values=merge_field_values)

        logger.debug(f'Primary object {merged_model_instance.model_meta.model_name}[pk={primary_object.pk}] '
                     f'will be merged with {len(alias_objects)} alias object(s)')
        logger.debug(serialize('json', [primary_object, ]))
        logger.debug(serialize('json', alias_objects))

        for alias_object in alias_objects:
            merged_model_instance.merge(alias_object)

        return merged_model_instance

    @classmethod
    def create(cls, *args, **kwargs) -> Model:
        return cls._create(*args, **kwargs).primary_object

    @classmethod
    def create_with_audit_trail(cls, *args, **kwargs) -> Tuple[Model, List[Model]]:
        instance = cls._create(*args, **kwargs)
        return instance.primary_object, instance.modified_related_objects

    def _handle_o2m_related_field(self, related_field: Field, alias_object: Model):
        reverse_o2m_accessor_name = related_field.get_accessor_name()
        o2m_accessor_name = related_field.field.name

        for obj in getattr(alias_object, reverse_o2m_accessor_name).all():
            try:
                logger.debug(f'Attempting to set o2m field {o2m_accessor_name} on '
                             f'{obj._meta.model.__name__}[pk={obj.pk}] to '
                             f'{self.model_meta.model_name}[pk={self.primary_object.pk}] ...')
                setattr(obj, o2m_accessor_name, self.primary_object)
                obj.validate_unique()
                obj.save()
                logger.debug('success.')
            except ValidationError as e:
                logger.debug(f'failed. {e}')
                if related_field.field.null:
                    logger.debug(f'Setting o2m field {o2m_accessor_name} on '
                                 f'{obj._meta.model.__name__}[pk={obj.pk}] to `None`')
                    setattr(obj, o2m_accessor_name, None)
                    obj.save()
                else:
                    logger.debug(f'Deleting {obj._meta.model.__name__}[pk={obj.pk}]')
                    _pk = obj.pk
                    obj.delete()
                    obj.pk = _pk  # pk is cached and re-assigned to keep the audit trail in tact
            self.modified_related_objects.append(obj)

    def _handle_m2m_related_field(self, related_field: Field, alias_object: Model):
        try:
            m2m_accessor_name = related_field.get_attname()
        except AttributeError:
            # get_attname does not exist for reverse m2m relations
            m2m_accessor_name = related_field.get_accessor_name()

        for obj in getattr(alias_object, m2m_accessor_name).all():
            logger.debug(f'Removing {obj._meta.model.__name__}[pk={obj.pk}] '
                         f'from {self.model_meta.model_name}[pk={alias_object.pk}].{m2m_accessor_name}')
            getattr(alias_object, m2m_accessor_name).remove(obj)
            logger.debug(f'Adding {obj._meta.model.__name__}[pk={obj.pk}] '
                         f'to {self.model_meta.model_name}[pk={self.primary_object.pk}].{m2m_accessor_name}')
            getattr(self.primary_object, m2m_accessor_name).add(obj)
            self.modified_related_objects.append(obj)

    def _handle_o2o_related_field(self, related_field: Field, alias_object: Model):
        if not self.merge_field_values:
            return

        o2o_accessor_name = related_field.name
        primary_o2o_object = getattr(self.primary_object, o2o_accessor_name, None)
        alias_o2o_object = getattr(alias_object, o2o_accessor_name, None)

        if primary_o2o_object is None and alias_o2o_object is not None:
            logger.debug(f'Setting {o2o_accessor_name} on {self.model_meta.model_name}[pk={alias_object.pk}] to None')
            setattr(alias_object, o2o_accessor_name, None)
            alias_object.save()
            logger.debug(f'Setting {o2o_accessor_name} on {self.model_meta.model_name}[pk={self.primary_object.pk}] '
                         f'to {alias_o2o_object._meta.model.__name__}[pk={alias_o2o_object.pk}')
            setattr(self.primary_object, o2o_accessor_name, alias_o2o_object)
            self.modified_related_objects.append(alias_o2o_object)

    def merge(self, alias_object: Model):
        primary_object = self.primary_object

        if not isinstance(alias_object, primary_object.__class__):
            raise TypeError('Only models of the same class can be merged')

        if primary_object.pk == alias_object.pk:
            raise ValueError('Cannot deduplicate an object on itself')

        logger.debug(f'Merging {self.model_meta.model_name}[pk={alias_object.pk}]')
        model_meta = ModelMeta(primary_object)

        for related_field in model_meta.related_fields:
            if related_field.one_to_many:
                self._handle_o2m_related_field(related_field, alias_object)
            elif related_field.one_to_one:
                self._handle_o2o_related_field(related_field, alias_object)
            elif related_field.many_to_many:
                self._handle_m2m_related_field(related_field, alias_object)

        if self.merge_field_values:
            # This step can lead to validation errors if `field` has a `unique or` `unique_together` constraint.
            for field in model_meta.editable_fields:
                primary_value = getattr(primary_object, field.name)
                alias_value = getattr(alias_object, field.name)

                logger.debug(f'Primary {field.name} has value: {primary_value}, '
                             f'Alias {field.name} has value: {alias_value}')
                if primary_value in field.empty_values and alias_value not in field.empty_values:
                    logger.debug(f'Setting primary {field.name} to alias value: {alias_value}')
                    setattr(primary_object, field.name, alias_value)

        if not self.keep_old:
            logger.debug(f'Deleting alias object {self.model_meta.model_name}[pk={alias_object.pk}]')
            alias_object.delete()

        primary_object.save()
