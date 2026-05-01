import sys

import bpy

from . import addon_updater_ops
from .addon_updater_prefs import GMTUpdaterPreferences
from . import yk_gmd_blender as _yk_gmd_blender

sys.modules.setdefault("yk_gmd_blender", _yk_gmd_blender)

# Include the bl_info at the top level always
bl_info = {
    "name": "Yakuza GMD/GMT File Import/Export",
    "author": "SutandoTsukai181, Samuel Stark (TheTurboTurnip)",
    "version": (2, 0, 0),
    "blender": (3, 2, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Yakuza GMT animation, CMT camera, and GMD model files",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Import-Export",
}


classes = (
    GMTUpdaterPreferences,
)


def register():
    addon_updater_ops.register(bl_info)

    for c in classes:
        bpy.utils.register_class(c)

    # Check for update as soon as the updater is loaded
    # If auto check is enabled and the conditions are met, will
    # display a pop up once the user clicks anywhere in the scene
    addon_updater_ops.check_for_update_background()

    from .blender.addon import register_addon

    register_addon()
    _yk_gmd_blender.register()


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    addon_updater_ops.unregister()

    from .blender.addon import unregister_addon

    _yk_gmd_blender.unregister()
    unregister_addon()
