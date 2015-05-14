REQUEST = {
    "id": "",
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "Schema a request for creating an offer list",
    "type": "object",
    "required": ["filePath"],
    "properties": {
        "filePath": {"type": "string", "minLength": 1, "maxLength": 255},
    },
    "additionalProperties": False,
}
