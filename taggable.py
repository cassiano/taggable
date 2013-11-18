from mongoengine import *
from mongoengine.base import get_document
import inspect


def klass(class_object_or_name):
    if inspect.isclass(class_object_or_name):
        return class_object_or_name

    if not isinstance(class_object_or_name, basestring):
        raise TypeError("'%s' must be either a class or a string." % class_object_or_name)

    try:
        return get_document(class_object_or_name)
    except KeyError:
        raise NameError("name '%s' is not defined." % class_object_or_name)


def mongodb_compound_class_name(cls):
    """ For a class Year with the following hierarchy: Year < Tag < Document < BaseDocument <
    TaggableDocument < object, returns "Tag.Year", which is how MongoDB stores this class' name
    in DBRef's "_cls" field. """

    ancestors = [ancestor.__name__ for ancestor in inspect.getmro(cls)]
    document_class_index = ancestors.index('Document')

    return '.'.join(ancestors[:document_class_index][::-1])


def extract_class(class_type_or_name_or_tuple):
    if isinstance(class_type_or_name_or_tuple, tuple):
        cls = class_type_or_name_or_tuple[0]
    else:
        cls = class_type_or_name_or_tuple

    return klass(cls)


def extract_max_refs(class_type_or_name_or_tuple):
    if isinstance(class_type_or_name_or_tuple, tuple) and len(class_type_or_name_or_tuple) > 1:
        max_refs = class_type_or_name_or_tuple[1]
    else:
        max_refs = -1       # -1 = no maximum limit

    return max_refs


def find(f, seq):
  """Returns first item in sequence where f(item) == True."""

  for item in seq:
    if f(item):
      return item


def create_document_tag_refs_document_cls_index():
    DocumentTagRefs._get_collection().ensure_index('document._cls')


class TaggableDocument(object):
    allowed_tag_types = ['Tag']

    def tags(self):
        refs = DocumentTagRefs.objects(document=self)

        return [ref.tag for ref in refs]

    def tags_by_type(self, tag_type):
        return [tag for tag in self.tags() if isinstance(tag, klass(tag_type))]

    def add_tag(self, tag):
        if not isinstance(tag, Tag):
            raise TypeError("Invalid type %s. Only tags are allowed in document '%s'." %
                (type(tag).__name__, self))

        if self.can_add_tag(tag):
            return tag.add_document(self)

    def can_add_tag(self, tag):
        match = self._check_if_tag_allowed(tag)

        if match:
            self._check_if_maximum_tag_limit_reached(match)

        return True

    def _check_if_tag_allowed(self, tag):
        def find_match(tag_types, error_when_missing=True):
            match = find(lambda tag_type: isinstance(tag, extract_class(tag_type)), tag_types)

            if (error_when_missing and not match) or (not error_when_missing and match):
                raise TypeError("Tags of type '%s' are not allowed in document '%s'." %
                    (type(tag).__name__, self))

            return match

        match = None

        if isinstance(self.allowed_tag_types, dict):
            if not (set(self.allowed_tag_types) & set(['only', 'except'])):
                raise ValueError("allowed_tag_types dict must contain 'only' and/or 'except' keys.")

            if 'only' in self.allowed_tag_types:
                match = find_match(self.allowed_tag_types['only'])

            if 'except' in self.allowed_tag_types:
                find_match(self.allowed_tag_types['except'], False)

        elif isinstance(self.allowed_tag_types, list):
            match = find_match(self.allowed_tag_types)
        else:
            raise TypeError("allowed_tag_types must be either a dict or a list.")

        return match

    def _check_if_maximum_tag_limit_reached(self, matched_tag):
        max_tags_allowed = extract_max_refs(matched_tag)

        if max_tags_allowed != -1:
            tag_type = extract_class(matched_tag)

            # Check if the number of current tags of the matched type already associated
            # with this document has reached the allowed maximum.
            if len(self.tags_by_type(tag_type)) == max_tags_allowed:
                raise ValueError("Maximum number (%d) of tags of type '%s' exceeded in "
                    "document '%s'." % (max_tags_allowed, tag_type.__name__, self))


class DocumentTagRefs(Document):
    document = GenericReferenceField()
    tag = ReferenceField('Tag')

    meta = {
        'indexes': [
            { 'fields': ['document', 'tag'], 'unique': True },
            'tag'
        ]
    }

class Tag(Document, TaggableDocument):
    allowed_document_types = [TaggableDocument]

    name = StringField(max_length=120, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': [
            { 'fields': ['name'], 'unique': True }
        ]
    }

    def documents(self):
        refs = DocumentTagRefs.objects(tag=self)

        return [ref.document for ref in refs]

    def documents_by_type(self, document_type):
        refs = DocumentTagRefs.objects(
            __raw__={
                'document._cls': mongodb_compound_class_name(klass(document_type)), 'tag': self.id
            }
        )

        return [ref.document for ref in refs]

    def add_document(self, document):
        if not isinstance(document, TaggableDocument):
            raise TypeError("Invalid type %s. Only taggable documents are allowed in tag '%s'." %
                (type(document).__name__, self))

        if self.can_add_document(document):
            return DocumentTagRefs(document=document, tag=self).save()

    def can_add_document(self, document):
        match = self._check_if_document_allowed(document)

        if match:
            self._check_if_maximum_document_limit_reached(match)

        return True

    def _check_if_document_allowed(self, document):
        def find_match(document_types, error_when_missing=True):
            match = find(lambda document_type: isinstance(document, extract_class(document_type)),
                         document_types)

            if (error_when_missing and not match) or (not error_when_missing and match):
                raise TypeError("Documents of type '%s' are not allowed in tag '%s'." %
                    (type(document).__name__, self))

            return match

        match = None

        if isinstance(self.allowed_document_types, dict):
            if not (set(self.allowed_document_types) & set(['only', 'except'])):
                raise ValueError("allowed_document_types dict must contain 'only' and/or "
                    "'except' keys.")

            if 'only' in self.allowed_document_types:
                match = find_match(self.allowed_document_types['only'])

            if 'except' in self.allowed_document_types:
                find_match(self.allowed_document_types['except'], False)

        elif isinstance(self.allowed_document_types, list):
            match = find_match(self.allowed_document_types)
        else:
            raise TypeError("allowed_document_types must be either a dict or a list.")

        return match

    def _check_if_maximum_document_limit_reached(self, matched_document):
        max_documents_allowed = extract_max_refs(matched_document)

        if max_documents_allowed != -1:
            document_type = extract_class(matched_document)

            # Check if the number of current documents of the matched type already associated
            # with this tag has reached the allowed maximum.
            if len(self.documents_by_type(document_type)) == max_documents_allowed:
                raise ValueError("Maximum number (%d) of documents of type '%s' exceeded in "
                    "tag '%s'." % (max_documents_allowed, document_type.__name__, self))

    def __repr__(self):
        return self.name
