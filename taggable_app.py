from taggable import *


class Unit(Tag):
    allowed_tag_types = { 'only': [('Organization', 1)] }

    address = StringField(required=True)


class Year(Tag):
    allowed_tag_types = []


class Class(Tag):
    allowed_tag_types = [(Year, 1), (Unit, 1)]


class Organization(Tag):
    allowed_document_types = { 'only': [Unit] }     # An organization is a collection of units.
    allowed_tag_types = []                          # Collecting organizations is not allowed.

    address = StringField(required=True)


class Student(Document, TaggableDocument):
    allowed_tag_types = [Class]

    name = StringField(required=True)

    def __repr__(self):
        return self.name


if __name__ == '__main__':
    connect('tag_spike')

    # Since MongoEngine doesn't seem to allow this particular index in the meta definition (see
    # DocumentTagRefs class definition above), create it directly in PyMongo.
    create_document_tag_refs_document_cls_index()

    cassiano = Student(name='Cassiano D`Andrea').save()
    mackenzie = Organization(name='Mackenzie', address='Av. Tiradentes, 11  Sao Paulo-SP').save()
    mackenzie_sp = Unit(name='Mackenzie SP', address='Av. 23 de Maio, 22  Sao Paulo-SP').save()
    mackenzie_cps = Unit(name='Mackenzie Campinas', address='Av. Brasil, 33  Campinas-SP').save()
    terceiro_ano = Year(name='3rd grade').save()
    turma_a_mackenzie_cps = Class(name='A').save()

    mackenzie_cps.add_tag(mackenzie)            # We may add the tag to the document.
    mackenzie.add_document(mackenzie_sp)        # Or do it the other way around.
    turma_a_mackenzie_cps.add_tag(terceiro_ano)
    turma_a_mackenzie_cps.add_tag(mackenzie_cps)
    cassiano.add_tag(turma_a_mackenzie_cps)

    for student in Student.objects:
        class_tag = cassiano.tags_by_type(Class)[0]
        print "%s belongs to class '%s'" % (student.name, class_tag.name)

        year_tag = class_tag.tags_by_type(Year)[0]
        print "is in %s" % year_tag.name

        unit_tag = class_tag.tags_by_type(Unit)[0]
        print "and studies in %s, located in %s" % (unit_tag.name, unit_tag.address)

    for organization in Organization.objects:
        print "%s's units:" % organization.name
        print ', '.join([unit.name for unit in organization.documents_by_type(Unit)])
