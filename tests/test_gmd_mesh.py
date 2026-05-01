import unittest
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from yk_gmd_blender.gmdlib.abstract.gmd_mesh import GMDMeshIndices, GMDSkinnedMesh
    from yk_gmd_blender.gmdlib.abstract.gmd_shader import GMDSkinnedVertexBuffer
    HAS_BLENDER_PYTHON = True
except ModuleNotFoundError as ex:
    if ex.name == "mathutils":
        HAS_BLENDER_PYTHON = False
    else:
        raise


class DummyBone:
    def __init__(self, name):
        self.name = name


def make_vertices(bone_data, weight_data):
    return GMDSkinnedVertexBuffer(
        layout=None,
        pos=np.zeros((3, 3), dtype=np.float32),
        weight_data=np.array(weight_data, dtype=np.float32),
        bone_data=np.array(bone_data, dtype=np.uint8),
        normal=None,
        tangent=None,
        unk=None,
        col0=None,
        col1=None,
        uvs=[],
    )


@unittest.skipUnless(HAS_BLENDER_PYTHON, "requires Blender Python mathutils")
class GMDSkinnedMeshTests(unittest.TestCase):
    def test_ignores_255_bone_sentinel_slots(self):
        vertices = make_vertices(
            [
                [0, 1, 255, 0],
                [1, 255, 0, 0],
                [0, 0, 0, 0],
            ],
            [
                [0.55, 0.40, 0.05, 0.0],
                [1.0, 0.25, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ],
        )

        GMDSkinnedMesh(
            empty=False,
            vertices_data=vertices,
            relevant_bones=[DummyBone("bone0"), DummyBone("bone1")],
            triangles=GMDMeshIndices.from_triangles([(0, 1, 2)]),
            attribute_set=None,
        )

        self.assertFalse(np.any(vertices.bone_data == 255))
        self.assertEqual(float(vertices.weight_data[0, 2]), 0.0)
        self.assertEqual(float(vertices.weight_data[1, 1]), 0.0)

    def test_rejects_other_out_of_range_bone_indices(self):
        vertices = make_vertices(
            [
                [0, 2, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            [
                [0.8, 0.2, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ],
        )

        with self.assertRaises(Exception):
            GMDSkinnedMesh(
                empty=False,
                vertices_data=vertices,
                relevant_bones=[DummyBone("bone0"), DummyBone("bone1")],
                triangles=GMDMeshIndices.from_triangles([(0, 1, 2)]),
                attribute_set=None,
            )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
