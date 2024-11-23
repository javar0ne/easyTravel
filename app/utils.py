def is_valid_enum_name(enum_class, name: str) -> bool:
    return name in enum_class.__members__