# marketplace/documents.py
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from django.utils import translation
from elasticsearch_dsl import analyzer, token_filter

from .models import Item

# -----------------------------------
# Index config
# -----------------------------------
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

# Reusable analyzer
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

    # ✅ Localized category indexed
    category = fields.ObjectField(properties={
        'name': fields.TextField(analyzer=edge_ngram_analyzer)
    })

    # ✅ Indexed attributes
    attributes = fields.ObjectField(properties={
        'name': fields.TextField(analyzer=edge_ngram_analyzer),
        'value': fields.TextField(analyzer=edge_ngram_analyzer)
    }, multi=True)

    # ✅ Explicit condition field
    condition = fields.TextField(analyzer=edge_ngram_analyzer)

    class Index:
        name = 'items'

    class Django:
        model = Item
        fields = [
            'title',
            'description',
            'price',
            # DO NOT repeat condition here!
            'created_at',
        ]
        settings = {
            'analysis': {
                'analyzer': {
                    'edge_ngram_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'edge_ngram_filter']
                    }
                }
            }
        }

    # Optimize queries
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category")
            .prefetch_related("attribute_values")
        )

    def get_indexing_queryset(self):
        return self.get_queryset().iterator(chunk_size=200)

    def prepare_category(self, instance):
        lang = translation.get_language()
        return {
            "name": instance.category.name_ar if lang == "ar" else instance.category.name_en
        }

    def prepare_attributes(self, instance):
        lang = translation.get_language()
        return [
            {
                "name": av.attribute.name_ar if lang == "ar" else av.attribute.name_en,
                "value": av.value,
            }
            for av in instance.attribute_values.all()
        ]
