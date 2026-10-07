bl_info = {
    "name": "PolyZamboni",
    "author": "Anton Florey",
    "version": (1,3,1),
    "blender": (5,1,0),
    "location": "View3D",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"
}

if "bpy" in locals():
    import importlib
    importlib.reload(locals()["ui"])
    importlib.reload(locals()["operators"])
    importlib.reload(locals()["properties"])
    importlib.reload(locals()["drawing"])
    importlib.reload(locals()["callbacks"])
else:
    import bpy
    from .polyzamboni import properties
    from .polyzamboni import drawing
    from .polyzamboni import operators
    from .polyzamboni import ui
    from .polyzamboni import callbacks

def register():
    properties.register()
    operators.register()
    ui.register()
    callbacks.register()

def unregister():
    callbacks.unregister()
    drawing.hide_all_drawings()
    drawing.hide_pages()
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
