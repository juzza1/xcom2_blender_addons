bl_info = {
    "name": "Flatten shape keys",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy
    

class FlattenShapeKeys(bpy.types.Operator):
    bl_idname = 'object.shape_key_flatten'
    bl_label = "Flatten shape keys"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        obj.active_shape_key_index = 0
        if obj.active_shape_key:
            obj.show_only_shape_key = False
            bpy.ops.object.shape_key_add(from_mix=True)
            obj.active_shape_key_index = 0
            try:
                while True:
                    bpy.ops.object.shape_key_remove()
            # No more shape keys
            except RuntimeError:
                pass
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(FlattenShapeKeys.bl_idname)


def register():
    bpy.utils.register_class(FlattenShapeKeys)
    bpy.types.MESH_MT_shape_key_context_menu.append(menu_func)


def unregister():
    bpy.utils.unregister_class(FlattenShapeKeys)
    bpy.types.MESH_MT_shape_key_context_menu.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
    bpy.ops.object.shape_key_flatten()