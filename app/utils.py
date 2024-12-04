def is_valid_enum_name(enum_class, name: str) -> bool:
    return name in enum_class.__members__

def encode_city_name(name: str):
    return name.lower().replace(' ', '_')