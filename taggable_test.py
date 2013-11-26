# -*- coding: utf-8 -*-

import unittest
from taggable import *


class TestCase(unittest.TestCase):
    TEST_DATABASE_NAME = 'test_db'

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)

        self.mongo_client = connect(self.TEST_DATABASE_NAME)
        self.db = self.mongo_client[self.TEST_DATABASE_NAME]
        create_document_tag_refs_document_cls_index()

    def setUp(self):
        super(TestCase, self).setUp()

        for collection_name in self.db.collection_names():
            if not collection_name.startswith("system."):
                self.db.drop_collection(collection_name)

        recreate_indexes()


class TestTaggable(TestCase):
    def setUp(self):
        super(TestTaggable, self).setUp()

    def test_allowed_tags_can_be_specified_using_classes(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale')
        men_shoes = MenClothing(name='Shoes')

        self.assertTrue(summer_sale.can_add_document(men_shoes))

    def test_allowed_tags_can_be_specified_using_strings(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = ['Sale']

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale')
        men_shoes = MenClothing(name='Shoes')

        self.assertTrue(summer_sale.can_add_document(men_shoes))

    def test_allowed_documents_can_be_specified_using_classes(self):
        class MenClothing(Document, TaggableDocument):
            allowed_tags = ['Sale']

            name = StringField(required=True)

        class Sale(Tag):
            allowed_documents = [MenClothing]


        summer_sale = Sale(name='Summer Sale')
        men_shoes = MenClothing(name='Shoes')

        self.assertTrue(men_shoes.can_add_tag(summer_sale))

    def test_allowed_documents_can_be_specified_using_strings(self):
        class MenClothing(Document, TaggableDocument):
            allowed_tags = ['Sale']

            name = StringField(required=True)

        class Sale(Tag):
            allowed_documents = ['MenClothing']


        summer_sale = Sale(name='Summer Sale')
        men_shoes = MenClothing(name='Shoes')

        self.assertTrue(men_shoes.can_add_tag(summer_sale))

    def test_add_tag_works(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        pants = MenClothing(name='Pants').save()

        men_shoes.add_tag(summer_sale)
        pants.add_tag(summer_sale)

        self.assertEqual(set(summer_sale.documents_by_type(MenClothing)), set([men_shoes, pants]))

    def test_add_document_works(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        pants = MenClothing(name='Pants').save()

        summer_sale.add_document(men_shoes)
        summer_sale.add_document(pants)

        self.assertEqual(set(summer_sale.documents_by_type(MenClothing)), set([men_shoes, pants]))

    def test_only_taggable_documents_can_be_added_to_tags(self):
        class Sale(Tag):
            pass

        class NonTaggableMenClothing(Document):
            name = StringField(required=True)

        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = NonTaggableMenClothing(name='Shoes').save()

        with self.assertRaises(TypeError):
            summer_sale.add_document(men_shoes)

    def test_only_tags_can_be_added_to_taggable_documents(self):
        class MenClothing(Document, TaggableDocument):
            name = StringField(required=True)

        class NonTagSale(Document):
            name = StringField(required=True)

        men_shoes = MenClothing(name='Shoes').save()
        summer_sale = NonTagSale(name='Summer Sale').save()

        with self.assertRaises(TypeError):
            men_shoes.add_tag(summer_sale)

    def test_only_allowed_documents_can_be_added_to_tags_using_default_syntax(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            name = StringField(required=True)

            meta = { 'allow_inheritance': True }

        class YoungMenClothing(MenClothing):
            pass

        class WomenClothing(Document, TaggableDocument):
            name = StringField(required=True)

        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        snickers = YoungMenClothing(name='Snickers').save()
        dress = WomenClothing(name='Dress').save()

        summer_sale.add_document(men_shoes)
        summer_sale.add_document(snickers)

        with self.assertRaises(TypeError):
            summer_sale.add_document(dress)

    def test_only_allowed_documents_can_be_added_to_tags_using_alternative_syntax(self):
        class Sale(Tag):
            allowed_documents = { 'only': ['MenClothing'] }

        class MenClothing(Document, TaggableDocument):
            name = StringField(required=True)

            meta = { 'allow_inheritance': True }

        class YoungMenClothing(MenClothing):
            pass

        class WomenClothing(Document, TaggableDocument):
            name = StringField(required=True)

        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        snickers = YoungMenClothing(name='Snickers').save()
        dress = WomenClothing(name='Dress').save()

        summer_sale.add_document(men_shoes)
        summer_sale.add_document(snickers)

        with self.assertRaises(TypeError):
            summer_sale.add_document(dress)

    def test_forbidden_documents_cannot_be_added_to_tags(self):
        class Sale(Tag):
            allowed_documents = { 'except': ['MenClothing'] }

        class MenClothing(Document, TaggableDocument):
            name = StringField(required=True)

            meta = { 'allow_inheritance': True }

        class YoungMenClothing(MenClothing):
            pass

        class WomenClothing(Document, TaggableDocument):
            name = StringField(required=True)

        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        snickers = YoungMenClothing(name='Snickers').save()
        dress = WomenClothing(name='Dress').save()

        summer_sale.add_document(dress)

        with self.assertRaises(TypeError):
            summer_sale.add_document(men_shoes)

        with self.assertRaises(TypeError):
            summer_sale.add_document(snickers)

    def test_only_allowed_tags_can_be_added_to_documents_using_default_syntax(self):
        class MenClothing(Document, TaggableDocument):
            allowed_tags = ['Sale']

            name = StringField(required=True)

        class Sale(Tag):
            pass

        class NewCollection(Tag):
            pass

        men_shoes = MenClothing(name='Shoes').save()
        summer_sale = Sale(name='Summer Sale').save()
        new_winter_collection = NewCollection(name='New Winter Collection')

        men_shoes.add_tag(summer_sale)

        with self.assertRaises(TypeError):
            men_shoes.add_tag(new_winter_collection)

    def test_only_allowed_tags_can_be_added_to_documents_using_alternative_syntax(self):
        class MenClothing(Document, TaggableDocument):
            allowed_tags = { 'only': ['Sale'] }

            name = StringField(required=True)

        class Sale(Tag):
            pass

        class NewCollection(Tag):
            pass

        men_shoes = MenClothing(name='Shoes').save()
        summer_sale = Sale(name='Summer Sale').save()
        new_winter_collection = NewCollection(name='New Winter Collection')

        men_shoes.add_tag(summer_sale)

        with self.assertRaises(TypeError):
            men_shoes.add_tag(new_winter_collection)

    def test_forbidden_tags_cannot_be_added_to_documents(self):
        class MenClothing(Document, TaggableDocument):
            allowed_tags = { 'except': ['Sale'] }

            name = StringField(required=True)

        class Sale(Tag):
            pass

        class EndOfCollectionSale(Sale):
            pass

        class NewCollection(Tag):
            pass

        men_shoes = MenClothing(name='Shoes').save()
        summer_sale = Sale(name='Summer Sale').save()
        snow_shoes_sale = EndOfCollectionSale(name='Snow Shoes Summer Sale').save()
        new_winter_collection = NewCollection(name='New Winter Collection').save()

        men_shoes.add_tag(new_winter_collection)

        with self.assertRaises(TypeError):
            men_shoes.add_tag(summer_sale)

        with self.assertRaises(TypeError):
            men_shoes.add_tag(snow_shoes_sale)

    def test_checks_tag_limits_on_add(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [(Sale, 1)]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        winter_sale = Sale(name='Winter Sale').save()
        men_shoes = MenClothing(name='Shoes').save()

        men_shoes.add_tag(summer_sale)

        with self.assertRaises(ValueError):
            men_shoes.add_tag(winter_sale)

    def test_checks_document_limits_on_add(self):
        class Sale(Tag):
            allowed_documents = [('MenClothing', 1)]

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()
        pants = MenClothing(name='Pants').save()

        summer_sale.add_document(men_shoes)

        with self.assertRaises(ValueError):
            summer_sale.add_document(pants)

    def test_cannot_add_tag_to_same_document_twice(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()

        men_shoes.add_tag(summer_sale)

        with self.assertRaises(NotUniqueError):
            men_shoes.add_tag(summer_sale)

    def test_cannot_add_document_to_same_tag_twice(self):
        class Sale(Tag):
            allowed_documents = ['MenClothing']

        class MenClothing(Document, TaggableDocument):
            allowed_tags = [Sale]

            name = StringField(required=True)


        summer_sale = Sale(name='Summer Sale').save()
        men_shoes = MenClothing(name='Shoes').save()

        summer_sale.add_document(men_shoes)

        with self.assertRaises(NotUniqueError):
            summer_sale.add_document(men_shoes)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTaggable)
    unittest.TextTestRunner(verbosity=2).run(suite)
