EFFECTS = {}

def register_effect(name):
    def decorator(func):
        EFFECTS[name] = func
        return func
    return decorator

def get_effect(name):
    return EFFECTS.get(name)

def list_effects():
    return list(EFFECTS.keys())