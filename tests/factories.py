from datetime import date

from factory import DjangoModelFactory, Faker, SubFactory, fuzzy, post_generation

from tests.models import Article, EarningsReport, NewsAgency, Place, Publication, Reporter, Restaurant, Waiter


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


class WaiterFactory(DjangoModelFactory):
    restaurant = SubFactory(RestaurantFactory)
    name = Faker('name')

    class Meta:
        model = Waiter


class EarningsReportFactory(DjangoModelFactory):
    restaurant = SubFactory(RestaurantFactory)
    date = fuzzy.FuzzyDate(date(2000, 1, 1))
    amount = fuzzy.FuzzyDecimal(0, 10000)

    class Meta:
        model = EarningsReport


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

    @post_generation
    def number_of_articles(self, create, extracted, **kwargs):
        if not create or extracted is None or extracted < 1:
            return

        self.article_set.add(*ArticleFactory.create_batch(extracted))


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
