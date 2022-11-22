"""Helper functions to inspect FINAM entities."""
from ..data.tools import Info
from ..errors import FinamNoDataError
from ..interfaces import IAdapter, IComponent, IInput, IOutput, ITimeComponent

DEFAULT_INDENT = "  "


def inspect(obj):
    """Prints information about a component, adapter or input/output slot."""
    if isinstance(obj, IComponent):
        return _inspect_component(obj)
    if isinstance(obj, IAdapter):
        return _inspect_slot(obj)
    if isinstance(obj, (IInput, IOutput)):
        return _inspect_slot(obj)
    if isinstance(obj, Info):
        return _inspect_info(obj)
    raise ValueError(
        f"Can only inspect FINAM components, adapters and i/o slots. Got {obj.__class__.__name__}."
    )


def _inspect_component(component, indent=""):
    s = indent + component.name
    if isinstance(component, ITimeComponent):
        s += f"\n{indent}{DEFAULT_INDENT}time: {component.time}"
    if len(component.inputs) > 0:
        s += f"\n{indent}{DEFAULT_INDENT}Inputs"
        for _name, inp in component.inputs.items():
            s += "\n" + _inspect_slot(inp, indent + DEFAULT_INDENT + DEFAULT_INDENT)
    if len(component.outputs) > 0:
        s += f"\n{indent}{DEFAULT_INDENT}Outputs"
        for _name, out in component.outputs.items():
            s += "\n" + _inspect_slot(out, indent + DEFAULT_INDENT + DEFAULT_INDENT)
    return s


def _inspect_adapter(adapter, indent=""):
    s = indent + adapter.name
    return s


def _inspect_slot(slot, indent=""):
    info = None
    try:
        info = slot.info
    except FinamNoDataError:
        pass

    s = indent + slot.name
    if slot.is_static:
        s += " (static)"

    s += f"\n{_inspect_info(info, indent+DEFAULT_INDENT)}"

    return s


def _inspect_info(info, indent=""):
    s = ""
    if info is None:
        s += f"{indent}?"
    else:
        s += f"\n{indent}grid: {info.grid}"
        for k, v in info.meta.items():
            s += f"\n{indent}{k}: {v}"

    return s
