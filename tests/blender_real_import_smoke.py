import importlib.util
import os
import sys
import unittest
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "yakuza_gmd_gmt_blender"
ENV_PATH = ROOT / ".env"


def load_dotenv(path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv(ENV_PATH)


def env_path(name):
    value = os.environ.get(name)
    return Path(value) if value else None


GMD_PATH = env_path("YAKUZA_TEST_GMD_PATH")
GMT_PATH = env_path("YAKUZA_TEST_GMT_PATH")


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


@unittest.skipUnless(
    GMD_PATH and GMD_PATH.exists() and GMT_PATH and GMT_PATH.exists(),
    "real import fixture files are not available",
)
class RealImportSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addon = load_addon_package()

    def setUp(self):
        reset_scene()
        self.addon.register()

    def tearDown(self):
        self.addon.unregister()
        reset_scene()

    def test_imports_kiryu_gmd_and_run_gmt(self):
        gmd_result = bpy.ops.import_scene.gmd_skinned(
            filepath=str(GMD_PATH),
            strict=False,
            stop_on_fail=True,
            import_materials=True,
            fuse_vertices=True,
            custom_split_normals=True,
            game_enum="AUTODETECT",
            import_hierarchy=True,
            import_objects=True,
        )
        self.assertEqual(gmd_result, {"FINISHED"})

        armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
        self.assertGreater(len(armatures), 0)
        armature = armatures[0]
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)

        gmt_result = bpy.ops.import_scene.gmt(
            filepath=str(GMT_PATH),
            directory=str(GMT_PATH.parent),
            files=[{"name": GMT_PATH.name}],
            armature_name=armature.name,
            merge_vector_curves=True,
            is_auth=False,
        )
        self.assertEqual(gmt_result, {"FINISHED"})
        self.assertIsNotNone(armature.animation_data)
        self.assertIsNotNone(armature.animation_data.action)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
