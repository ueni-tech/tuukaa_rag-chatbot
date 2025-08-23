import uuid


def generate_collection_id(prefix: str | None = None) -> str:
    base = uuid.uuid4().hex
    if prefix:
        return f"{prefix}-{base}"
    return base
