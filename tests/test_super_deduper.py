import pytest

from django_super_deduper.merge import MergedModelInstance
from tests.factories import (
    ArticleFactory,
    NewsAgencyFactory,
    PlaceFactory,
    PublicationFactory,
    ReporterFactory,
    RestaurantFactory,
)


@pytest.mark.django_db
class MergedModelInstanceTest(object):

    def test_merge_basic_model(self):
        primary_object = PlaceFactory.create(address=None)
        alias_object = PlaceFactory.create()

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert merged_object.address == alias_object.address

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

    def test_merge_model_with_o2m_relationship(self):
        primary_object = NewsAgencyFactory.create()
        alias_object = NewsAgencyFactory.create()
        related_object = ReporterFactory.create(news_agency=alias_object)

        merged_object = MergedModelInstance.create(primary_object, [alias_object])

        assert related_object.news_agency != merged_object
        related_object.refresh_from_db()
        assert related_object.news_agency == merged_object

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
