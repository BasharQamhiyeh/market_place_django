# marketplace/documents.py
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from django.utils import translation
from elasticsearch_dsl import analyzer, token_filter

from .models import Item

# Index configuration
item_index = Index('items')
item_index.settings(
    number_of_shards=1,
    number_of_replicas=0,
    analysis={
        "filter": {
            "edge_ngram_filter": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 20
            }
        },
        "analyzer": {
            "edge_ngram_analyzer": {
                "tokenizer": "standard",
                "filter": ["lowercase", "edge_ngram_filter"]
            }
        }
    }
)

# Edge N-gram Analyzer
edge_ngram_filter = token_filter(
    'edge_ngram_filter',
    type='edge_ngram',
    min_gram=2,
    max_gram=20
)

edge_ngram_analyzer = analyzer(
    'edge_ngram_analyzer',
    tokenizer='standard',
    filter=['lowercase', edge_ngram_filter]
)


@registry.register_document
class ItemDocument(Document):

    # category indexing
    category = fields.ObjectField(properties={
        'name': fields.TextField(analyzer=edge_ngram_analyzer)
    })

    # photos
    photos = fields.ObjectField(properties={
        'image': fields.TextField()
    }, multi=True)

    # attributes indexing
    attributes = fields.ObjectField(properties={
        'name': fields.TextField(analyzer=edge_ngram_analyzer),
        'value': fields.TextField(analyzer=edge_ngram_analyzer)
    }, multi=True)

    class Index:
        name = 'items'

    class Django:
        model = Item
        fields = [
            'title',
            'description',
            'price',
        ]
        # analyzer override
        settings = {
            'analysis': {
                'analyzer': {
                    'edge_ngram_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'edge_ngram_filter']
                    }
                },
                'filter': {
                    'edge_ngram_filter': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 20
                    }
                }
            }
        }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('category')
            .prefetch_related(
                'photos',
                'attribute_values',
            )
        )

    def get_indexing_queryset(self):
        return self.get_queryset().iterator(chunk_size=200)

    def prepare_category(self, instance):
        lang = translation.get_language()
        return {
            'name': instance.category.name_ar if lang == 'ar' else instance.category.name_en
        }

    def prepare_photos(self, instance):
        return [{'image': p.image.url} for p in instance.photos.all()]

    def prepare_attributes(self, instance):
        lang = translation.get_language()
        return [
            {
                'name': av.attribute.name_ar if lang == 'ar' else av.attribute.name_en,
                'value': av.value
            }
            for av in instance.attribute_values.all()
        ]
