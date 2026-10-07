import bpy
import numpy as np
from bpy.types import Mesh
from .drawing import update_all_polyzamboni_drawings, hide_all_drawings, update_all_page_layout_drawings, hide_pages
from bpy.app.handlers import persistent


from .operators_backend import set_glue_flaps_enabled, update_all_flap_geometry

class CallbackGlobals():
    _refresh_page_layout_in_modal_operator = False

def redraw_all(*args):
    context = bpy.context
    if context.screen is None:
        return None

    update_all_drawings_callback(None, context)
    return None

dummy_owner = object()

def subscribe_to_active_object():
    bpy.msgbus.clear_by_owner(dummy_owner)
    subscribe_to = bpy.types.LayerObjects, "active"
    bpy.msgbus.subscribe_rna(
        key = subscribe_to,
        owner = dummy_owner,
        args = tuple(),
        notify = redraw_all,
        )

@persistent
def pre_load_handler(dummy):
    hide_all_drawings()
    hide_pages()

@persistent
def post_load_handler(dummy):
    subscribe_to_active_object()
    if not bpy.app.timers.is_registered(redraw_all):
        bpy.app.timers.register(redraw_all, first_interval=0.0)

def update_all_drawings_callback(self, context : bpy.types.Context):
    if context.screen is None:
        return
    if np.any([area.type == "VIEW_3D" for area in context.screen.areas]):
        update_all_polyzamboni_drawings(self, context)
    if np.any([area.type == "IMAGE_EDITOR" for area in context.screen.areas]):
        if context.window_manager.polyzamboni_in_page_edit_mode:
            CallbackGlobals._refresh_page_layout_in_modal_operator = True
        else:
            update_all_page_layout_drawings(self, context)

def update_glueflap_geometry_callback(self, context : bpy.types.Context):
    ao = context.active_object
    if ao is not None and ao.type == 'MESH':
        active_mesh : Mesh = ao.data
        zamboni_props  = active_mesh.polyzamboni_general_mesh_props
        if zamboni_props.has_attached_paper_model:
            update_all_flap_geometry(active_mesh)
            update_all_drawings_callback(self, context)

def update_glueflap_enabled_callback(self, context : bpy.types.Context):
    ao = context.active_object
    if ao is not None and ao.type == 'MESH':
        active_mesh : Mesh = ao.data
        zamboni_props = active_mesh.polyzamboni_general_mesh_props
        if zamboni_props.has_attached_paper_model:
            set_glue_flaps_enabled(active_mesh, zamboni_props.glue_flaps_enabled)
            update_all_drawings_callback(self, context)
    
@persistent
def redraw_3D_view_callback(dummy):
    update_all_polyzamboni_drawings(None, bpy.context)

def register():
    handler_pairs = (
        (bpy.app.handlers.load_post, post_load_handler),
        (bpy.app.handlers.load_pre, pre_load_handler),
        (bpy.app.handlers.undo_post, redraw_3D_view_callback),
    )
    for handlers, handler in handler_pairs:
        if handler not in handlers:
            handlers.append(handler)
    subscribe_to_active_object()

def unregister():
    bpy.msgbus.clear_by_owner(dummy_owner)
    handler_pairs = (
        (bpy.app.handlers.load_post, post_load_handler),
        (bpy.app.handlers.load_pre, pre_load_handler),
        (bpy.app.handlers.undo_post, redraw_3D_view_callback),
    )
    for handlers, handler in handler_pairs:
        if handler in handlers:
            handlers.remove(handler)
