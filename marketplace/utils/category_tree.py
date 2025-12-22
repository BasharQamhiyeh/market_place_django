def build_category_tree(categories, lang="ar"):
    """
    Recursively build a full JSON-serializable category tree.
    [
        {
            "id": 1,
            "name": "الكترونيات",
            "children": [
                {
                    "id": 7,
                    "name": "لابتوبات",
                    "children": [...]
                }
            ]
        }
    ]
    """

    def serialize(cat):
        name = cat.name_ar if lang == "ar" else cat.name_en
        return {
            "id": cat.id,
            "name": name,
            "child_label": cat.child_label or "",
            "children": [serialize(c) for c in cat.subcategories.all()]
        }

    return [serialize(c) for c in categories]



def get_selected_category_path(category):
    if not category:
        return []

    path = []
    current = category
    while current:
        path.append(current.id)
        current = current.parent

    return list(reversed(path))