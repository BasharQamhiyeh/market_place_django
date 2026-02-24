# marketplace/documents.py
import os

from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer, token_filter

from .models import Listing, Item, Request, Category, City


# ============================================================
# Detect environment (Disable elasticsearch on Render)
# ============================================================

IS_RENDER = os.environ.get("RENDER", "") == "true"

if IS_RENDER:
    registry._active = False

    class ListingDocument:
        pass

else:
    # ============================================================
    # Index Definition
    # ============================================================

    listing_index = Index("listings")
    listing_index.settings(
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

    edge_ngram_filter = token_filter(
        "edge_ngram_filter",
        type="edge_ngram",
        min_gram=2,
        max_gram=20
    )

    edge_ngram_analyzer = analyzer(
        "edge_ngram_analyzer",
        tokenizer="standard",
        filter=["lowercase", edge_ngram_filter]
    )

    # ============================================================
    # Unified ListingDocument (ITEM + REQUEST)
    # ============================================================

    @registry.register_document
    class ListingDocument(Document):

        category = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        category_parent = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        city = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        attributes = fields.ObjectField(
            properties={
                "name": fields.TextField(analyzer=edge_ngram_analyzer),
                "value": fields.TextField(analyzer=edge_ngram_analyzer),
            },
            multi=True
        )

        price = fields.FloatField()
        condition = fields.TextField()
        budget = fields.FloatField()
        condition_preference = fields.TextField()

        class Index:
            name = "listings"

        class Django:
            model = Listing
            fields = [
                "title",
                "description",
                "type",
                "created_at",
            ]

        def get_queryset(self):
            return (
                super()
                .get_queryset()
                .select_related(
                    "category",
                    "category__parent",
                    "city",
                    "item",
                    "request",
                )
                .prefetch_related(
                    "item__attribute_values",
                    "request__attribute_values",
                )
            )

        def prepare_category(self, instance):
            if not instance.category:
                return None
            return {"name": instance.category.name}

        def prepare_category_parent(self, instance):
            if not instance.category or not instance.category.parent:
                return None
            return {"name": instance.category.parent.name}

        def prepare_city(self, instance):
            if not instance.city:
                return None
            return {"name": instance.city.name}

        def prepare_attributes(self, instance):
            attrs = []

            if hasattr(instance, "item") and instance.item:
                for av in instance.item.attribute_values.all():
                    attrs.append({
                        "name": av.attribute.name,
                        "value": av.value,
                    })

            if hasattr(instance, "request") and instance.request:
                for av in instance.request.attribute_values.all():
                    attrs.append({
                        "name": av.attribute.name,
                        "value": av.value or "",
                    })

            return attrs

        def prepare_price(self, instance):
            if hasattr(instance, "item") and instance.item:
                return float(instance.item.price)
            return None

        def prepare_condition(self, instance):
            if hasattr(instance, "item") and instance.item:
                return instance.item.condition
            return None

        def prepare_budget(self, instance):
            if hasattr(instance, "request") and instance.request and instance.request.budget is not None:
                return float(instance.request.budget)
            return None

        def prepare_condition_preference(self, instance):
            if hasattr(instance, "request") and instance.request:
                return instance.request.condition_preference
            return None