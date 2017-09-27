# Django Super Deduper
[![Build status](https://badge.buildkite.com/9895056b294e7f1a8893b9ef75bb743f3933fc3264e23eeeb2.svg)](https://buildkite.com/mighty/django-super-deduper)
[![codecov](https://codecov.io/gh/mighty-justice/django-super-deduper/branch/master/graph/badge.svg)](https://codecov.io/gh/mighty-justice/django-super-deduper)

A collection of classes and utilities to aid in de-duping Django model instances.

## Install

`pip install https://github.com/mighty-justice/django-super-deduper/archive/master.zip`

## Usage

### Merging Duplicate Instances

By default any empty fields on the primary object will take the value from the duplicates.

```
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

## Logging

This package does have some rudimentary logging for debugging purposes.
Add this snippet to your Django logging settings to enable it:

```
LOGGING = {
    'loggers': {
        'django_super_deduper': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```
