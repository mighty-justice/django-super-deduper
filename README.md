# Django Super Deduper
[![Build status](https://badge.buildkite.com/9895056b294e7f1a8893b9ef75bb743f3933fc3264e23eeeb2.svg)](https://buildkite.com/mighty/django-super-deduper)
[![codecov](https://codecov.io/gh/mighty-justice/django-super-deduper/branch/master/graph/badge.svg)](https://codecov.io/gh/mighty-justice/django-super-deduper)
[![Python version](https://img.shields.io/pypi/pyversions/django-super-deduper.svg)](https://pypi.python.org/pypi/django-super-deduper)

A collection of classes and utilities to aid in de-duping Django model instances.

## Requirements

- Python 3.6
- Django 1.11

## Install

`pip install django-super-deduper`

## Usage

### Merging Duplicate Instances

By default any [empty values](https://github.com/django/django/blob/master/django/core/validators.py#L13) on the primary object will take the value from the duplicates.
Additionally, any related one-to-one, one-to-many, and many-to-many related objects will be updated to reference the primary object.

```python
> from django_super_deduper.merge import MergedModelInstance
> primary_object = Model.objects.create(attr_A=None, attr_B='')
> alias_object_1 = Model.objects.create(attr_A=X)
> alias_object_2 = Model.objects.create(attr_B=Y)
> merged_object = MergedModelInstance.create(primary_object, [alias_object_1, alias_object_2])
> merged_object.attr_A
X
> merged_object.attr_B
Y
```

## Improvements

- Support multiple merging strategies
- Recursive merging of related one-to-one objects

## Logging

This package does have some rudimentary logging for debugging purposes.
Add this snippet to your Django logging settings to enable it:

```python
LOGGING = {
    'loggers': {
        'django_super_deduper': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## References

- https://djangosnippets.org/snippets/2283/
- https://stackoverflow.com/questions/3393378/django-merging-objects
