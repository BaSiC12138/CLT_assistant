from __future__ import annotations

from .models import InterfaceMode, ModuleSpec


MODULE_SPECS: tuple[ModuleSpec, ...] = (
    ModuleSpec(1.25, 320, 160, 256, 128, "320接口"),
    ModuleSpec(1.25, 400, 300, 320, 240, "320接口"),
    ModuleSpec(1.5, 320, 160, 213, 107, "320接口"),
    ModuleSpec(1.53, 320, 160, 208, 104, "320接口"),
    ModuleSpec(1.56, 400, 300, 256, 192, "320接口"),
    ModuleSpec(1.667, 320, 160, 192, 96, "320接口"),
    ModuleSpec(1.86, 320, 160, 172, 86),
    ModuleSpec(2.0, 320, 160, 160, 80),
    ModuleSpec(2.5, 320, 160, 128, 64),
    ModuleSpec(2.5, 160, 160, 64, 64),
    ModuleSpec(3.0, 192, 192, 64, 64),
    ModuleSpec(3.076, 320, 160, 104, 52),
    ModuleSpec(3.91, 320, 160, 82, 41),
    ModuleSpec(4.0, 320, 160, 80, 40),
    ModuleSpec(4.81, 320, 160, 67, 33),
    ModuleSpec(5.0, 320, 160, 64, 32),
    ModuleSpec(6.0, 192, 192, 32, 32),
    ModuleSpec(8.0, 256, 128, 32, 16),
    ModuleSpec(10.0, 320, 160, 32, 16),
)

RECEIVER_MODELS: tuple[str, ...] = (
    "自动",
    "K5+",
    "K8",
    "K10",
)


PITCH_EPSILON = 0.006
DEFAULT_PITCH_VALUE = 1.86
DEFAULT_PITCH = str(DEFAULT_PITCH_VALUE)
DEFAULT_MODULE_SIZE = "320x160"
DEFAULT_MODULE_PIXELS = "172x86"
DEFAULT_SCREEN_MODULES = "12x12"
DEFAULT_SCREEN_SIZE = "3.84x1.92"
DEFAULT_SCREEN_PIXELS = "2064x1032"
DEFAULT_CABINET_PIXELS = "344x258"
DEFAULT_SCREEN_CABINETS = "6x4"
DEFAULT_CABINET_MODEL = "自动"


def matching_modules(pitch: float) -> tuple[ModuleSpec, ...]:
    return tuple(
        spec for spec in MODULE_SPECS if abs(spec.pitch - pitch) <= PITCH_EPSILON
    )


def receiver_for(interface: InterfaceMode, module: ModuleSpec) -> str:
    if interface is InterfaceMode.HUB320:
        return "E320" if module.pitch == 1.25 else "E80"
    if interface is InterfaceMode.HUB75:
        return "5A-75E"
    if module.interface == "320接口":
        return "E320" if module.pitch == 1.25 else "E80"
    return "5A-75E"
