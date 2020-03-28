bl_info = {
    "name": "Sort vertex groups alphabetically, put vgs with underscore prefix at the end",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy


class UnderscoreVertexGroupSort(bpy.types.Operator):
    bl_idname = 'object.vertex_group_sort_underscore'
    bl_label = "Vertex Group underscore sort"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.vertex_group_sort(sort_type='NAME')
        old_start = obj.vertex_groups.active
        obj.vertex_groups.active_index = 0
        while obj.vertex_groups.active.name.startswith('_'):
            while obj.vertex_groups.active_index < len(obj.vertex_groups) - 1:
                bpy.ops.object.vertex_group_move(direction='DOWN')
            obj.vertex_groups.active_index = 0
        for i in range(len(obj.vertex_groups)):
            if obj.vertex_groups[i] == old_start:
                obj.vertex_groups.active_index = i
        
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(UnderscoreVertexGroupSort.bl_idname)


def register():
    bpy.utils.register_class(UnderscoreVertexGroupSort)
    bpy.types.MESH_MT_vertex_group_context_menu.append(menu_func)


def unregister():
    bpy.utils.unregister_class(UnderscoreVertexGroupSort)
    bpy.types.MESH_MT_vertex_group_context_menu.remove(menu_func)


if __name__ == "__main__":
    register()
    
    bpy.ops.object.vertex_group_sort_underscore()