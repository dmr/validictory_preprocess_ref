from __future__ import unicode_literals


def dict_walk(node, action, match='$ref'):
    if len(node.keys()) == 1 and match in node:
        return action(node[match])
    else:
        newdict = {}
        for key, value in node.items():
            if isinstance(value, dict):
                value = dict_walk(node=value, action=action, match=match)
            if isinstance(value, list):
                value = [
                    dict_walk(node=entry, action=action, match=match)
                    if isinstance(entry, dict) else entry
                    for entry in value
                ]
            newdict[key] = value
        return newdict


def get_ref_path_for_ref_url(url):
    if not url.startswith('#/'):
        raise ValueError('Only local references allowed')
    return url.lstrip('#/').split('/')


def get_ref_definition(schema, matched_value):
    ref_path = get_ref_path_for_ref_url(matched_value)
    # traverse path down or raise exception
    found_definition = schema
    for component in ref_path:
        found_definition = found_definition[component]
    return found_definition


def validictory_preprocess_ref(schema):
    return dict_walk(
        node=schema,
        action=lambda matched_value: get_ref_definition(schema, matched_value=matched_value)
    )


def test_validictory_preprocess_ref():
    schema_w_ref = {
        "id": "http://some.site.somewhere/entry-schema#",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "schema for an fstab entry",
        "type": "object",
        "required": ["storage"],
        "properties": {
            "storage": {
                "type": "object",
                "oneOf": [
                    {"$ref": "#/definitions/diskDevice"},
                    {"$ref": "#/definitions/diskUUID"}
                ]
            },
            "other_property": {"$ref": "#/definitions/diskUUID"}
        },
        "definitions": {
            "diskDevice": {"type": "string"},
            "diskUUID": {"type": "integer"}
        }
    }

    preprocecced_schema = validictory_preprocess_ref(schema_w_ref)

    assert set(schema_w_ref.keys()) == set(preprocecced_schema.keys())
    assert preprocecced_schema['properties']['storage']['oneOf'] == [
        {"type": "string"}, {"type": "integer"}
    ]
    assert preprocecced_schema['properties']['other_property'] == {"type": "integer"}

    try:
        validictory_preprocess_ref({
            "other_property1": {"$ref": "/definitions/diskUUID"}
        })
        raise Exception('Exception should have been raised')
    except ValueError:
        pass

    try:
        validictory_preprocess_ref({
            "other_property2": {"$ref": "http://example.com/diskUUID"}
        })
        raise Exception('Exception should have been raised')
    except ValueError:
        pass


if __name__ == '__main__':
    test_validictory_preprocess_ref()
