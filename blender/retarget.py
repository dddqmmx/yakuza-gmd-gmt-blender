import re
from typing import Set

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator

from .action_compat import iter_action_fcurves


BONE_DATA_PATH_RE = re.compile(r'pose\.bones\["([^"]+)"\]')


def armature_items(self, context):
    active = context.active_object
    items = []

    if active and active.type == "ARMATURE":
        items.append((active.name, active.name, ""))

    active_name = active.name if active else None
    for armature in bpy.data.objects:
        if armature.type == "ARMATURE" and armature.name != active_name:
            items.append((armature.name, armature.name, ""))

    return items


def action_items(self, context):
    items = []

    source = bpy.data.objects.get(getattr(self, "source_armature_name", ""))
    if source and source.animation_data and source.animation_data.action:
        action = source.animation_data.action
        items.append((action.name, action.name, "Source armature active action"))

    for action in bpy.data.actions:
        if not any(item[0] == action.name for item in items):
            items.append((action.name, action.name, ""))

    return items


def action_bone_names(action, datablock=None) -> Set[str]:
    names = set()
    for fcurve in iter_action_fcurves(action, datablock):
        match = BONE_DATA_PATH_RE.search(fcurve.data_path)
        if match:
            names.add(match.group(1))

    return names


class RetargetYakuzaAction(Operator):
    """Retarget a Yakuza animation action onto another armature by matching bone names"""

    bl_idname = "anim.yakuza_retarget_action"
    bl_label = "Retarget Yakuza Animation"
    bl_options = {"REGISTER", "UNDO"}

    source_armature_name: EnumProperty(
        name="Source Armature",
        description="Armature that owns or matches the source action",
        items=armature_items,
    )

    target_armature_name: EnumProperty(
        name="Target Armature",
        description="Armature to receive a copy of the source action",
        items=armature_items,
    )

    action_name: EnumProperty(
        name="Source Action",
        description="Action to copy onto the target armature",
        items=action_items,
    )

    new_action_name: StringProperty(
        name="New Action Name",
        description="Optional name for the copied target action",
        default="",
    )

    replace_target_action: BoolProperty(
        name="Replace Target Action",
        description="Assign the copied action as the target armature's active action",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        layout.prop(self, "source_armature_name")
        layout.prop(self, "target_armature_name")
        layout.prop(self, "action_name")
        layout.prop(self, "new_action_name")
        layout.prop(self, "replace_target_action")

    def execute(self, context):
        source = bpy.data.objects.get(self.source_armature_name)
        target = bpy.data.objects.get(self.target_armature_name)
        action = bpy.data.actions.get(self.action_name)

        if not source or source.type != "ARMATURE":
            self.report({"ERROR"}, "Source armature is invalid")
            return {"CANCELLED"}

        if not target or target.type != "ARMATURE":
            self.report({"ERROR"}, "Target armature is invalid")
            return {"CANCELLED"}

        if source == target:
            self.report({"ERROR"}, "Source and target armatures must be different")
            return {"CANCELLED"}

        if not action:
            self.report({"ERROR"}, "Source action is invalid")
            return {"CANCELLED"}

        target_action = action.copy()
        target_action.name = self.new_action_name.strip() or f"{action.name}[retargeted]"

        target.animation_data_create()
        if self.replace_target_action:
            target.animation_data.action = target_action

        bpy.context.view_layer.objects.active = target
        target.select_set(True)

        source_bones = action_bone_names(action, source)
        target_bones = {bone.name for bone in target.pose.bones}
        matched = source_bones & target_bones
        missing = source_bones - target_bones

        if missing:
            sample = ", ".join(sorted(missing)[:5])
            suffix = "" if len(missing) <= 5 else f", +{len(missing) - 5}"
            self.report(
                {"WARNING"},
                f"Retargeted {target_action.name}: matched {len(matched)} bone(s), missing {len(missing)} ({sample}{suffix})",
            )
        else:
            self.report({"INFO"}, f"Retargeted {target_action.name}: matched {len(matched)} bone(s)")

        return {"FINISHED"}


def menu_func_retarget(self, context):
    self.layout.operator(RetargetYakuzaAction.bl_idname, text="Retarget Yakuza Animation")
