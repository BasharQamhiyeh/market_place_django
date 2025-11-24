# marketplace/documents.py
import os
from django.utils import translation

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

    # Dummy class to prevent import errors
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

    # Shared Analyzer
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

        # ---------- category ----------
        category = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        # ---------- parent category ----------
        category_parent = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        # ---------- city ----------
        city = fields.ObjectField(properties={
            "name": fields.TextField(analyzer=edge_ngram_analyzer),
        })

        # ---------- universal attributes ----------
        attributes = fields.ObjectField(
            properties={
                "name": fields.TextField(analyzer=edge_ngram_analyzer),
                "value": fields.TextField(analyzer=edge_ngram_analyzer),
            },
            multi=True
        )

        # ---------- Item fields ----------
        price = fields.FloatField()
        condition = fields.TextField()

        # ---------- Request fields ----------
        budget = fields.FloatField()
        condition_preference = fields.TextField()

        class Index:
            name = "listings"

        class Django:
            model = Listing
            fields = [
                "title",
                "description",
                "type",        # item / request
                "created_at",
            ]

        # ========================================================
        # Optimized queryset
        # ========================================================
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

        # ========================================================
        # CATEGORY FIELD
        # ========================================================
        def prepare_category(self, instance):
            if not instance.category:
                return None
            lang = translation.get_language()
            return {
                "name": instance.category.name_ar if lang == "ar" else instance.category.name_en
            }

        def prepare_category_parent(self, instance):
            if not instance.category or not instance.category.parent:
                return None
            lang = translation.get_language()
            parent = instance.category.parent
            return {
                "name": parent.name_ar if lang == "ar" else parent.name_en
            }

        # ========================================================
        # CITY FIELD
        # ========================================================
        def prepare_city(self, instance):
            if not instance.city:
                return None
            lang = translation.get_language()
            return {
                "name": instance.city.name_ar if lang == "ar" else instance.city.name_en
            }

        # ========================================================
        # UNIVERSAL ATTRIBUTES (ITEM or REQUEST)
        # ========================================================
        def prepare_attributes(self, instance):
            lang = translation.get_language()
            attrs = []

            # === Item attributes ===
            if hasattr(instance, "item") and instance.item:
                for av in instance.item.attribute_values.all():
                    attrs.append({
                        "name": av.attribute.name_ar if lang == "ar" else av.attribute.name_en,
                        "value": av.value,
                    })

            # === Request attributes ===
            if hasattr(instance, "request") and instance.request:
                for av in instance.request.attribute_values.all():
                    attrs.append({
                        "name": av.attribute.name_ar if lang == "ar" else av.attribute.name_en,
                        "value": av.value or "",
                    })

            return attrs

        # ========================================================
        # ITEM FIELD PREPARERS
        # ========================================================
        def prepare_price(self, instance):
            if hasattr(instance, "item") and instance.item:
                return float(instance.item.price)
            return None

        def prepare_condition(self, instance):
            if hasattr(instance, "item") and instance.item:
                return instance.item.condition
            return None

        # ========================================================
        # REQUEST FIELD PREPARERS
        # ========================================================
        def prepare_budget(self, instance):
            if hasattr(instance, "request") and instance.request and instance.request.budget is not None:
                return float(instance.request.budget)
            return None

        def prepare_condition_preference(self, instance):
            if hasattr(instance, "request") and instance.request:
                return instance.request.condition_preference
            return None
