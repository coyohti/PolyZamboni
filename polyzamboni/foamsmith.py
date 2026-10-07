"""Distortion-tolerant flattening helpers for EVA foam patterns."""

import bpy
import numpy as np
from bpy.types import Object


FOAMSMITH_UV_LAYER_NAME = "PolyZamboni Foamsmith"


def _set_active_uv_layer(mesh, layer_name):
    previous_active_index = mesh.uv_layers.active_index if mesh.uv_layers.active else None
    uv_layer = mesh.uv_layers.get(layer_name)
    if uv_layer is None:
        uv_layer = mesh.uv_layers.new(name=layer_name)
    mesh.uv_layers.active_index = list(mesh.uv_layers).index(uv_layer)
    return uv_layer, previous_active_index


def _restore_mesh_selection(mesh, vertex_selection, edge_selection, face_selection):
    for vertex, selected in zip(mesh.vertices, vertex_selection):
        vertex.select = selected
    for edge, selected in zip(mesh.edges, edge_selection):
        edge.select = selected
    for face, selected in zip(mesh.polygons, face_selection):
        face.select = selected


def unwrap_object_from_seams(obj : Object):
    """Unwrap all faces along marked seams and return exact per-face vertex coordinates."""
    if obj.type != "MESH":
        raise TypeError("Foamsmith patterns can only be generated from mesh objects")

    mesh = obj.data
    original_mode = obj.mode
    if original_mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    vertex_selection = [vertex.select for vertex in mesh.vertices]
    edge_selection = [edge.select for edge in mesh.edges]
    face_selection = [face.select for face in mesh.polygons]
    uv_layer, previous_active_index = _set_active_uv_layer(mesh, FOAMSMITH_UV_LAYER_NAME)

    try:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        result = bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001, correct_aspect=True)
        if result != {"FINISHED"}:
            raise RuntimeError("Blender could not unwrap the marked foam panels")
        bpy.ops.object.mode_set(mode="OBJECT")
        uv_layer = mesh.uv_layers.get(FOAMSMITH_UV_LAYER_NAME)
        if uv_layer is None:
            raise RuntimeError("Blender did not create the Foamsmith UV layer")

        # Blender packs UVs into normalized space. Restore model-space scale by
        # preserving the median 3D edge length across the flattened pattern.
        uv_to_model_ratios = []
        for polygon in mesh.polygons:
            loop_indices = list(polygon.loop_indices)
            for position, loop_index in enumerate(loop_indices):
                next_loop_index = loop_indices[(position + 1) % len(loop_indices)]
                loop = mesh.loops[loop_index]
                next_loop = mesh.loops[next_loop_index]
                length_3d = (mesh.vertices[next_loop.vertex_index].co - mesh.vertices[loop.vertex_index].co).length
                length_2d = (uv_layer.data[next_loop_index].uv - uv_layer.data[loop_index].uv).length
                if length_3d > 1e-12 and length_2d > 1e-12:
                    uv_to_model_ratios.append(length_2d / length_3d)
        if not uv_to_model_ratios:
            raise RuntimeError("The mesh did not produce any usable foam pattern edges")
        coordinate_scale = 1.0 / float(np.median(uv_to_model_ratios))

        facewise_vertex_coordinates = {}
        for polygon in mesh.polygons:
            vertex_coordinates = {}
            for loop_index in polygon.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                vertex_coordinates[vertex_index] = coordinate_scale * np.asarray(uv_layer.data[loop_index].uv, dtype=np.float64)
            facewise_vertex_coordinates[polygon.index] = vertex_coordinates
        return facewise_vertex_coordinates
    finally:
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        _restore_mesh_selection(mesh, vertex_selection, edge_selection, face_selection)
        if previous_active_index is not None and previous_active_index < len(mesh.uv_layers):
            mesh.uv_layers.active_index = previous_active_index
        if original_mode == "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
