from core.audio import Audio
from core.enums import ProcessingMode
import inspect

from core.preprocess import EffectContext

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

INFRASTRUCTURE_PARAMS = {"audio", "frames", "context"}

def get_effect_params(name):
    effect = EFFECTS.get(name)

    if not effect:
        return {}

    func = effect["func"]

    sig = inspect.signature(func)
    params = {}

    for param in sig.parameters.values():

        if param.name in INFRASTRUCTURE_PARAMS:
            continue

        if param.annotation is Audio:
            continue

        if (param.annotation is not inspect.Parameter.empty
        and inspect.isclass(param.annotation)
        and issubclass(param.annotation, EffectContext)):
            continue

        if isinstance(param.default, EffectContext):
            continue

        default = None

        if param.default is not inspect.Parameter.empty:
            default = param.default

        params[param.name] = {
            "default": default,
            "has_default": param.default is not inspect.Parameter.empty,
            "type": (
                param.annotation
                if param.annotation is not inspect.Parameter.empty
                else (type(default) if default is not None else str)
            )
        }

    return params