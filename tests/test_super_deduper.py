import pytest

from django_super_deduper.merge import MergedModelInstance
from django_super_deduper.models import ModelMeta
from tests.factories import (
    ArticleFactory,
    EarningsReportFactory,
    NewsAgencyFactory,
    PlaceFactory,
    PublicationFactory,
    ReporterFactory,
    RestaurantFactory,
    WaiterFactory,
)


@pytest.mark.django_db
class MergedModelInstanceTest(object):

    def test_merge_basic_model(self):
        primary_object = PlaceFactory.create(address=None)
        alias_object = PlaceFactory.create()

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.address == alias_object.address

    def test_dedupe_basic_model_no_merge(self):
        primary_object = PlaceFactory.create(address=None)
        alias_object = PlaceFactory.create()

        merged_object = MergedModelInstance.create(primary_object, [alias_object], merge_field_values=False)

        assert merged_object.address == primary_object.address

    def test_merge_model_with_multi_table_inheritance(self):
        primary_object = NewsAgencyFactory.create(address=None, website=None)
        alias_object = NewsAgencyFactory.create()

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.address == alias_object.address
        assert merged_object.website == alias_object.website

    def test_merge_model_with_o2o_relationship(self):
        primary_object = RestaurantFactory.create(place=None, serves_hot_dogs=True, serves_pizza=False)
        alias_object = RestaurantFactory.create(serves_hot_dogs=False, serves_pizza=True)
        alias_address = alias_object.place.address
        alias_name = alias_object.place.name

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.place.address == alias_address
        assert merged_object.place.name == alias_name
        assert merged_object.serves_hot_dogs and not merged_object.serves_pizza

    def test_dedupe_model_with_o2o_relationship_no_merge(self):
        primary_object = RestaurantFactory.create(place=None, serves_hot_dogs=True, serves_pizza=False)
        alias_object = RestaurantFactory.create(serves_hot_dogs=False, serves_pizza=True)

        merged_object = MergedModelInstance.create(primary_object, [alias_object], merge_field_values=False)

        assert not merged_object.place
        assert merged_object.serves_hot_dogs and not merged_object.serves_pizza

    def test_merge_model_with_o2m_relationship(self):
        primary_object = NewsAgencyFactory.create()
        alias_object = NewsAgencyFactory.create()
        related_object = ReporterFactory.create(news_agency=alias_object)

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert related_object.news_agency != merged_object
        related_object.refresh_from_db()
        assert related_object.news_agency == merged_object

    def test_merge_model_with_o2m_relationship_and_unique_validation_set_null(self):
        primary_object, alias_object = RestaurantFactory.create_batch(2)
        waiter = WaiterFactory(restaurant=primary_object)
        duplicate_waiter = WaiterFactory(name=waiter.name, restaurant=alias_object)

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        waiter.refresh_from_db()
        assert waiter.restaurant == merged_object

        duplicate_waiter.refresh_from_db()
        assert duplicate_waiter.restaurant is None

    def test_merge_model_with_o2m_relationship_and_unique_validation_delete(self):
        primary_object, alias_object = RestaurantFactory.create_batch(2)
        report = EarningsReportFactory(restaurant=primary_object)
        other_report = EarningsReportFactory(date=report.date, restaurant=alias_object)

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        report.refresh_from_db()
        assert report.restaurant == merged_object

        with pytest.raises(EarningsReportFactory._meta.model.DoesNotExist):
            other_report.refresh_from_db()

    def test_merge_model_with_m2m_relationship(self):
        primary_object = ArticleFactory.create(reporter=None)
        related_object = ReporterFactory.create()
        alias_object = ArticleFactory.create(number_of_publications=3, reporter=related_object)

        assert primary_object.reporter is None
        assert primary_object.publications.count() == 0

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.reporter == related_object
        assert merged_object.publications.count() == 3

    def test_merge_model_with_reverse_m2m_relationsip(self):
        primary_object = PublicationFactory.create()
        alias_object = PublicationFactory.create(number_of_articles=3)

        assert primary_object.article_set.count() == 0

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.article_set.count() == 3

    def test_merge_different_models(self):
        primary_object = ArticleFactory.create()
        alias_object = ReporterFactory.create()

        with pytest.raises(TypeError):
            MergedModelInstance.create(primary_object, [alias_object])

    def test_merge_deletes_alias_objects(self):
        primary_object = PlaceFactory.create(address=None)
        alias_object = PlaceFactory.create()

        assert primary_object.address is None
        assert PlaceFactory._meta.model.objects.filter(pk=alias_object.pk).exists()

        merged_object = MergedModelInstance.create(primary_object, [alias_object], keep_old=False)

        assert merged_object.address == alias_object.address
        assert not PlaceFactory._meta.model.objects.filter(pk=alias_object.pk).exists()

    def test_prevent_self_merge(self):
        primary_object = PlaceFactory.create(address=None)
        alias_object = primary_object

        with pytest.raises(ValueError):
            MergedModelInstance.create(primary_object, [alias_object])

    def test_o2o_merge_with_audit_trail(self):
        primary_object = RestaurantFactory.create(place=None, serves_hot_dogs=True, serves_pizza=False)
        alias_objects = RestaurantFactory.create_batch(3)
        related_object = set([alias_objects[0].place])

        _, audit_trail = MergedModelInstance.create_with_audit_trail(primary_object, alias_objects)

        assert set(audit_trail) == related_object

    def test_o2m_merge_with_audit_trail(self):
        primary_object = NewsAgencyFactory.create()
        alias_object = NewsAgencyFactory.create()
        related_objects = set(ReporterFactory.create_batch(3, news_agency=alias_object))

        _, audit_trail = MergedModelInstance.create_with_audit_trail(primary_object, [alias_object])

        assert set(audit_trail) == related_objects

    def test_m2m_merge_with_audit_trail(self):
        primary_object = ArticleFactory.create(reporter=None)
        related_object = ReporterFactory.create()
        alias_object = ArticleFactory.create(number_of_publications=3, reporter=related_object)
        related_objects = set(alias_object.publications.all())

        _, audit_trail = MergedModelInstance.create_with_audit_trail(primary_object, [alias_object])

        assert set(audit_trail) == related_objects

    def test_reverse_m2m_merge_with_audit_trail(self):
        primary_object = PublicationFactory.create()
        alias_object = PublicationFactory.create(number_of_articles=3)
        related_objects = set(alias_object.article_set.all())

        _, audit_trail = MergedModelInstance.create_with_audit_trail(primary_object, [alias_object])

        assert set(audit_trail) == related_objects


@pytest.mark.django_db
class ModelMetaTest(object):

    def test_unmanaged_related_fields(self):
        instance = RestaurantFactory()

        model_meta = ModelMeta(instance)

        for field in model_meta.related_fields:
            assert field.related_model._meta.managed
