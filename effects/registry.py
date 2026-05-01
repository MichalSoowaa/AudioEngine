from core.enums import ProcessingMode

EFFECTS = {}

def register_effect(name, mode=ProcessingMode.PARALLEL, overlap=0, preprocess=None):
    def decorator(func):
        EFFECTS[name] = {
            "func": func,
            "mode": mode, # parallel, overlap, none
            "overlap": overlap,
            "preprocess": preprocess
        }
        return func
    return decorator

def get_effect(name):
    return EFFECTS.get(name)

def list_effects():
    return list(EFFECTS.keys())