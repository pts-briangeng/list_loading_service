REQUEST = {
    "id": "",
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "Schema a request for appending to an offer list",
    "type": "object",
    "required": ["filePath"],
    "properties": {
        "filePath": {"type": "string", "minLength": 1, "maxLength": 255}
    },
    "additionalProperties": False,
}
