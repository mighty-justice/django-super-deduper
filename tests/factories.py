from factory import DjangoModelFactory, Faker, SubFactory, post_generation

from tests.models import Place, NewsAgency, Restaurant, Reporter, Article, Publication


class PlaceFactory(DjangoModelFactory):
    address = Faker('street_address')
    name = Faker('company')

    class Meta:
        model = Place


class RestaurantFactory(DjangoModelFactory):
    place = SubFactory(PlaceFactory)
    serves_hot_dogs = Faker('boolean')
    serves_pizza = Faker('boolean')

    class Meta:
        model = Restaurant


class NewsAgencyFactory(DjangoModelFactory):
    website = Faker('url')

    class Meta:
        model = NewsAgency


class ReporterFactory(DjangoModelFactory):
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    news_agency = SubFactory(NewsAgencyFactory)

    class Meta:
        model = Reporter


class PublicationFactory(DjangoModelFactory):
    title = Faker('catch_phrase')

    class Meta:
        model = Publication


class ArticleFactory(DjangoModelFactory):
    headline = Faker('bs')
    pub_date = Faker('date')
    reporter = SubFactory(ReporterFactory)

    class Meta:
        model = Article

    @post_generation
    def number_of_publications(self, create, extracted, **kwargs):
        if not create or extracted is None or extracted < 1:
            return

        self.publications.add(*PublicationFactory.create_batch(extracted))
