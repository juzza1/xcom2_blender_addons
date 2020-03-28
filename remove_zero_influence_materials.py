bl_info = {
    "name": "Remove material slots with no faces assigned",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy


class RemoveZeroInfluenceMaterials(bpy.types.Operator):
    bl_idname = 'object.material_slot_remove_zero_influence'
    bl_label = "Remove material slots with no faces assigned"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        self.context = context
        obj = context.active_object
        # Remove slots with no material
        for ms in range(len(obj.material_slots) - 1, -1, -1):
            obj.active_material_index = ms
            if not obj.active_material:
                bpy.ops.object.material_slot_remove()
                
        if not obj.material_slots:
            return {'FINISHED'}
        
        seen = {p.material_index for p in obj.data.polygons}
        for ms in range(len(obj.material_slots) - 1, -1, -1):
            obj.active_material_index = ms
            if ms not in seen:
                bpy.ops.object.material_slot_remove()
     
        return {'FINISHED'} 


def menu_func(self, context):
    self.layout.operator(RemoveZeroInfluenceMaterials.bl_idname)


def register():
    bpy.utils.register_class(RemoveZeroInfluenceMaterials)
    bpy.types.MATERIAL_MT_context_menu.append(menu_func)


def unregister():
    bpy.utils.unregister_class(RemoveZeroInfluenceMaterials)
    bpy.types.MATERIAL_MT_context_menu.remove(menu_func)


if __name__ == "__main__":
    register()
    
    bpy.ops.object.material_slot_remove_zero_influence()