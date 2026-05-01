import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import bpy
from mathutils import Quaternion


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "yakuza_gmd_gmt_blender"


def load_addon_package():
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            del sys.modules[name]

    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    return module


def reset_scene():
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)

    for camera in list(bpy.data.cameras):
        bpy.data.cameras.remove(camera)

    for armature in list(bpy.data.armatures):
        bpy.data.armatures.remove(armature)


def add_fcurve(action, group_name, data_path, index, frames, values, datablock):
    from yakuza_gmd_gmt_blender.blender.action_compat import new_action_fcurve

    fcurve = new_action_fcurve(action, data_path, index, group_name, datablock)
    fcurve.keyframe_points.add(len(frames))
    fcurve.keyframe_points.foreach_set(
        "co",
        [component for co in zip(frames, values) for component in co],
    )
    fcurve.update()
    return fcurve


def make_armature_with_center_bone():
    bpy.ops.object.armature_add(enter_editmode=True)
    armature = bpy.context.object
    armature.name = "TestArmature"
    armature.data.name = "TestArmatureData"

    bone = armature.data.edit_bones[0]
    bone.name = "center_c_n"
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 1.0, 0.0)

    bpy.ops.object.mode_set(mode="POSE")
    armature.pose.bones["center_c_n"].rotation_mode = "QUATERNION"
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    armature.animation_data_create()
    return armature


def make_gmt_action(armature):
    action = bpy.data.actions.new(name="test_anim[roundtrip]")
    armature.animation_data.action = action
    group_name = "center_c_n"
    frames = [0.0, 10.0]

    for index, values in enumerate(([0.0, 1.25], [0.0, 0.5], [0.0, -0.25])):
        add_fcurve(
            action,
            group_name,
            'pose.bones["center_c_n"].location',
            index,
            frames,
            values,
            armature,
        )

    rotations = [
        Quaternion((1.0, 0.0, 0.0, 0.0)),
        Quaternion((0.9238795, 0.0, 0.3826834, 0.0)),
    ]
    for index, values in enumerate(zip(*[tuple(rotation) for rotation in rotations])):
        add_fcurve(
            action,
            group_name,
            'pose.bones["center_c_n"].rotation_quaternion',
            index,
            frames,
            list(values),
            armature,
        )

    return action


def make_camera_action(camera):
    camera.rotation_mode = "QUATERNION"
    camera.animation_data_create()
    action = bpy.data.actions.new(name="camera_anim")
    camera.animation_data.action = action
    frames = [0.0, 8.0]

    for index, values in enumerate(([0.0, 1.0], [0.0, -2.0], [3.0, 4.5])):
        add_fcurve(action, "Camera", "location", index, frames, values, camera)

    rotations = [
        Quaternion((1.0, 0.0, 0.0, 0.0)),
        Quaternion((0.9659258, 0.0, 0.2588190, 0.0)),
    ]
    for index, values in enumerate(zip(*[tuple(rotation) for rotation in rotations])):
        add_fcurve(action, "Camera", "rotation_quaternion", index, frames, list(values), camera)

    return action


class Blender51SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addon = load_addon_package()

    def setUp(self):
        reset_scene()

    def tearDown(self):
        reset_scene()

    def test_make_annotations_handles_missing_annotations_on_python_313(self):
        from yakuza_gmd_gmt_blender import addon_updater_ops

        class DummyOperator:
            enabled = bpy.props.BoolProperty(default=True)

        addon_updater_ops.make_annotations(DummyOperator)

        self.assertIn("enabled", DummyOperator.__annotations__)
        self.assertFalse(hasattr(DummyOperator, "enabled"))

    def test_addon_registers_and_unregisters_in_blender_51(self):
        self.addon.register()
        try:
            self.assertTrue(hasattr(bpy.types.Scene, "pattern_types"))
            self.assertTrue(hasattr(bpy.types.PoseBone, "pat1_left_hand"))
            self.assertTrue(hasattr(bpy.types.PoseBone, "pat1_right_hand"))
            self.assertTrue(hasattr(bpy.types.Material, "yakuza_data"))
            self.assertTrue(hasattr(bpy.types.Image, "yakuza_data"))
            self.assertTrue(hasattr(bpy.types.Object, "yakuza_hierarchy_node_data"))
            self.assertTrue(hasattr(bpy.types.Object, "yakuza_file_root_data"))
            self.assertTrue(hasattr(bpy.types.Bone, "yakuza_hierarchy_node_data"))
            bpy.ops.import_scene.gmt.get_rna_type()
            bpy.ops.export_scene.gmt.get_rna_type()
            bpy.ops.import_scene.gmd_skinned.get_rna_type()
            bpy.ops.import_scene.gmd_unskinned.get_rna_type()
            bpy.ops.import_scene.gmd_animation_skinned.get_rna_type()
            bpy.ops.import_scene.gmd_animation_unskinned.get_rna_type()
            bpy.ops.export_scene.gmd_skinned.get_rna_type()
            bpy.ops.export_scene.gmd_unskinned.get_rna_type()
        finally:
            self.addon.unregister()

        self.assertFalse(hasattr(bpy.types.Scene, "pattern_types"))
        self.assertFalse(hasattr(bpy.types.PoseBone, "pat1_left_hand"))
        self.assertFalse(hasattr(bpy.types.PoseBone, "pat1_right_hand"))
        self.assertFalse(hasattr(bpy.types.Material, "yakuza_data"))
        self.assertFalse(hasattr(bpy.types.Image, "yakuza_data"))
        self.assertFalse(hasattr(bpy.types.Object, "yakuza_hierarchy_node_data"))
        self.assertFalse(hasattr(bpy.types.Object, "yakuza_file_root_data"))
        self.assertFalse(hasattr(bpy.types.Bone, "yakuza_hierarchy_node_data"))

    def test_gmt_export_import_round_trip(self):
        from yakuza_gmd_gmt_blender.blender.exporter import GMTExporter
        from yakuza_gmd_gmt_blender.blender.importer import GMTImporter
        from yakuza_gmd_gmt_blender.gmt_lib.gmt.gmt_reader import read_gmt

        armature = make_armature_with_center_bone()
        action = make_gmt_action(armature)

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "roundtrip.gmt"
            GMTExporter(
                bpy.context,
                str(filepath),
                {
                    "action_name": action.name,
                    "gmt_anm_name": "test_anim",
                    "gmt_game": "YAKUZA5",
                    "gmt_file_name": "roundtrip",
                    "split_vector_curves": False,
                    "is_auth": False,
                },
            ).export()

            self.assertGreater(filepath.stat().st_size, 0)
            parsed = read_gmt(str(filepath))
            self.assertEqual(parsed.name, "roundtrip")
            self.assertEqual(parsed.animation.name, "test_anim")
            self.assertIn("center_c_n", parsed.animation.bones)

            armature.animation_data.action = None
            bpy.data.actions.remove(action)
            GMTImporter(
                bpy.context,
                str(filepath),
                {"merge_vector_curves": False, "is_auth": False},
            ).read()

        imported_action = armature.animation_data.action
        from yakuza_gmd_gmt_blender.blender.action_compat import find_action_fcurve

        self.assertEqual(imported_action.name, "test_anim[roundtrip]")
        self.assertIsNotNone(
            find_action_fcurve(
                imported_action,
                'pose.bones["center_c_n"].location',
                index=0,
                datablock=armature,
            )
        )
        self.assertIsNotNone(
            find_action_fcurve(
                imported_action,
                'pose.bones["center_c_n"].rotation_quaternion',
                index=0,
                datablock=armature,
            )
        )

    def test_cmt_export_import_round_trip(self):
        from yakuza_gmd_gmt_blender.blender.exporter import CMTExporter
        from yakuza_gmd_gmt_blender.blender.importer import CMTImporter
        from yakuza_gmd_gmt_blender.gmt_lib.gmt.gmt_reader import read_cmt

        camera_data = bpy.data.cameras.new(name="Camera")
        camera = bpy.data.objects.new("Camera", camera_data)
        bpy.context.scene.collection.objects.link(camera)
        bpy.context.scene.camera = camera
        bpy.context.view_layer.objects.active = camera
        camera.select_set(True)
        action = make_camera_action(camera)

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "roundtrip.cmt"
            CMTExporter(
                bpy.context,
                str(filepath),
                {
                    "action_name": action.name,
                    "armature_name": camera.name,
                    "cmt_game": "YAKUZA5",
                    "use_camera_keyframes": True,
                },
            ).export()

            self.assertGreater(filepath.stat().st_size, 0)
            parsed = read_cmt(str(filepath))
            self.assertEqual(len(parsed.animation.frames), 9)

            camera.animation_data.action = None
            bpy.data.actions.remove(action)
            CMTImporter(bpy.context, str(filepath), {}).read()

        imported_action = camera.animation_data.action
        from yakuza_gmd_gmt_blender.blender.action_compat import find_action_fcurve

        self.assertEqual(imported_action.name, "roundtrip.cmt")
        self.assertIsNotNone(find_action_fcurve(imported_action, "location", index=0, datablock=camera))
        self.assertIsNotNone(find_action_fcurve(imported_action, "rotation_quaternion", index=0, datablock=camera))
        self.assertIsNotNone(find_action_fcurve(imported_action, "data.lens", index=0, datablock=camera))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
