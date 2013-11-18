# -*- coding: utf-8 -*-

import unittest
from taggable import *


class TestCase(unittest.TestCase):
    TEST_DATABASE_NAME = 'test_db'

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)

        self.db = connect(self.TEST_DATABASE_NAME)

        create_document_tag_refs_document_cls_index()

    def setUp(self):
        super(TestCase, self).setUp()

        self.db.drop_database(self.TEST_DATABASE_NAME)


class TestTaggable(TestCase):
    def setUp(self):
        super(TestTaggable, self).setUp()

    def test_allowed_tag_types_can_be_specified_using_classes(self):
        class State(Tag):
            allowed_document_types = ['City']

        class City(Document, TaggableDocument):
            allowed_tag_types = [State]

            name = StringField(required=True)


        sp = State(name='SP')
        campinas = City(name='Campinas')

        self.assertTrue(sp.can_add_document(campinas))

    def test_allowed_tag_types_can_be_specified_using_strings(self):
        class State(Tag):
            allowed_document_types = ['City']

        class City(Document, TaggableDocument):
            allowed_tag_types = ['State']

            name = StringField(required=True)


        sp = State(name='SP')
        campinas = City(name='Campinas')

        self.assertTrue(sp.can_add_document(campinas))

    def test_allowed_document_types_can_be_specified_using_classes(self):
        class City(Document, TaggableDocument):
            allowed_tag_types = ['State']

            name = StringField(required=True)

        class State(Tag):
            allowed_document_types = [City]


        sp = State(name='SP')
        campinas = City(name='Campinas')

        self.assertTrue(campinas.can_add_tag(sp))

    def test_allowed_document_types_can_be_specified_using_strings(self):
        class City(Document, TaggableDocument):
            allowed_tag_types = ['State']

            name = StringField(required=True)

        class State(Tag):
            allowed_document_types = ['City']


        sp = State(name='SP')
        campinas = City(name='Campinas')

        self.assertTrue(campinas.can_add_tag(sp))

    def test_add_tag_works(self):
        class State(Tag):
            allowed_document_types = ['City']

        class City(Document, TaggableDocument):
            allowed_tag_types = [State]

            name = StringField(required=True)


        sp = State(name='SP').save()
        campinas = City(name='Campinas').save()
        itatiba = City(name='Itatiba').save()

        campinas.add_tag(sp)
        itatiba.add_tag(sp)

        self.assertEqual(set(sp.documents_by_type(City)), set([campinas, itatiba]))

    def test_add_document_works(self):
        class State(Tag):
            allowed_document_types = ['City']

        class City(Document, TaggableDocument):
            allowed_tag_types = [State]

            name = StringField(required=True)


        sp = State(name='SP').save()
        campinas = City(name='Campinas').save()
        itatiba = City(name='Itatiba').save()

        sp.add_document(campinas)
        sp.add_document(itatiba)

        self.assertEqual(set(sp.documents_by_type(City)), set([campinas, itatiba]))

    def test_checks_tag_limits_on_add(self):
        class State(Tag):
            allowed_document_types = ['City']

        class City(Document, TaggableDocument):
            allowed_tag_types = [(State, 1)]

            name = StringField(required=True)


        sp = State(name='SP').save()
        rj = State(name='RJ').save()
        campinas = City(name='Campinas').save()

        campinas.add_tag(sp)

        with self.assertRaises(ValueError):
            campinas.add_tag(rj)

    def test_checks_document_limits_on_add(self):
        class State(Tag):
            allowed_document_types = [('City', 1)]

        class City(Document, TaggableDocument):
            allowed_tag_types = [State]

            name = StringField(required=True)


        sp = State(name='SP').save()
        campinas = City(name='Campinas').save()
        itatiba = City(name='Itatiba').save()

        sp.add_document(campinas)

        with self.assertRaises(ValueError):
            sp.add_document(itatiba)

    def test_only_taggable_documents_can_be_added_to_tags(self):
        class State(Tag):
            pass

        class NonTaggableCity(Document):
            name = StringField(required=True)

        sp = State(name='SP').save()
        campinas = NonTaggableCity(name='Campinas').save()

        with self.assertRaises(TypeError):
            sp.add_document(campinas)

    def test_only_tags_can_be_added_to_taggable_documents(self):
        class City(Document, TaggableDocument):
            pass

        class NonTagState(Document):
            name = StringField(required=True)

        campinas = City(name='Campinas').save()
        sp = NonTagState(name='SP').save()

        with self.assertRaises(TypeError):
            campinas.add_tag(sp)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTaggable)
    unittest.TextTestRunner(verbosity=2).run(suite)
