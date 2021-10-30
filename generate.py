import datetime
import math
import os
import random
import uuid
from os.path import join

import bpy

primitive_constructors = [
    bpy.ops.mesh.primitive_cube_add,
    bpy.ops.mesh.primitive_uv_sphere_add,
    bpy.ops.mesh.primitive_cylinder_add,
    bpy.ops.mesh.primitive_cone_add,
    bpy.ops.mesh.primitive_torus_add,
]

dpi = 2 * math.pi


def generate(save_dir: str, items: int):
    labels = []
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    for ctor in random.choices(primitive_constructors, k=items):
        ctor()
        bpy.context.active_object.select_set(True)
        transform_seed = datetime.datetime.now().microsecond % 100
        bpy.ops.object.randomize_transform(
            random_seed=transform_seed,
            loc=(10, 10, 10),
            rot=(dpi, dpi, dpi),
            scale=(10, 10, 10),
        )
        uid = uuid.uuid4()
        bpy.ops.export_mesh.stl(
            filepath=os.path.join(save_dir, f"{uid}.stl"),
        )
        labels.append((uid, bpy.context.active_object.name))
        bpy.ops.object.delete()

    with open(join(save_dir, "labels.csv"), "w+") as file:
        file.write("model,type\n")
        for model_name, model_type in labels:
            file.write(f"{model_name},{model_type}\n")


if __name__ == "__main__":
    generate("./data/models", 10_000)
