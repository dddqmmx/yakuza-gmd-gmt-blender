from typing import Iterable, Optional

from bpy.types import Action, ActionGroup, FCurve, ID


try:
    from bpy_extras import anim_utils
except ImportError:
    anim_utils = None


def has_legacy_action_api(action: Action) -> bool:
    return hasattr(action, "fcurves") and hasattr(action, "groups")


def get_action_channelbag(action: Action, datablock: Optional[ID] = None):
    if has_legacy_action_api(action) or anim_utils is None:
        return None

    if datablock:
        anim_data = getattr(datablock, "animation_data", None)
        if anim_data and anim_data.action == action:
            channelbag = anim_utils.animdata_get_channelbag_for_assigned_slot(anim_data)
            if channelbag:
                return channelbag

            slot = anim_data.action_slot
            if slot:
                return anim_utils.action_get_channelbag_for_slot(action, slot)

    for slot in action.slots:
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        if channelbag:
            return channelbag

    return None


def ensure_action_channelbag(action: Action, datablock: Optional[ID] = None):
    if has_legacy_action_api(action) or anim_utils is None:
        return None

    if datablock:
        anim_data = getattr(datablock, "animation_data", None)
        if anim_data is None and hasattr(datablock, "animation_data_create"):
            anim_data = datablock.animation_data_create()

        if anim_data:
            if anim_data.action != action:
                anim_data.action = action

            if anim_data.action_slot:
                return anim_utils.action_ensure_channelbag_for_slot(action, anim_data.action_slot)

            if len(action.slots) == 0:
                action.slots.new(datablock.id_type, datablock.name)
                anim_data.action = action

            if anim_data.action_slot:
                return anim_utils.action_ensure_channelbag_for_slot(action, anim_data.action_slot)

    if len(action.slots) == 0:
        action.slots.new("OBJECT", action.name)

    return anim_utils.action_ensure_channelbag_for_slot(action, action.slots[0])


def new_action_fcurve(
    action: Action,
    data_path: str,
    index: int = 0,
    group_name: str = "",
    datablock: Optional[ID] = None,
) -> FCurve:
    if has_legacy_action_api(action):
        return action.fcurves.new(data_path=data_path, index=index, action_group=group_name)

    if datablock:
        return action.fcurve_ensure_for_datablock(
            datablock,
            data_path,
            index=index,
            group_name=group_name,
        )

    channelbag = ensure_action_channelbag(action)
    return channelbag.fcurves.new(data_path, index=index, group_name=group_name)


def find_action_fcurve(
    action: Optional[Action],
    data_path: str,
    index: int = 0,
    datablock: Optional[ID] = None,
) -> Optional[FCurve]:
    if not action:
        return None

    if has_legacy_action_api(action):
        return action.fcurves.find(data_path, index=index)

    channelbag = get_action_channelbag(action, datablock)
    if not channelbag:
        return None

    return channelbag.fcurves.find(data_path, index=index)


def iter_action_fcurves(action: Optional[Action], datablock: Optional[ID] = None) -> Iterable[FCurve]:
    if not action:
        return []

    if has_legacy_action_api(action):
        return list(action.fcurves)

    channelbag = get_action_channelbag(action, datablock)
    if not channelbag:
        return []

    return list(channelbag.fcurves)


def iter_action_groups(action: Optional[Action], datablock: Optional[ID] = None) -> Iterable[ActionGroup]:
    if not action:
        return []

    if has_legacy_action_api(action):
        return list(action.groups)

    channelbag = get_action_channelbag(action, datablock)
    if not channelbag:
        return []

    return list(channelbag.groups)


def get_action_group(
    action: Optional[Action],
    name: str,
    datablock: Optional[ID] = None,
) -> Optional[ActionGroup]:
    for group in iter_action_groups(action, datablock):
        if group.name == name:
            return group

    return None
