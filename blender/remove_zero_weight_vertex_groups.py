bl_info = {
    "name": "Remove zero-weight vertex groups",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy


class RemoveZeroWeightVertexGroups(bpy.types.Operator):
    bl_idname = 'object.vertex_group_remove_zero_weight_groups'
    bl_label = "Remove zero-weight vertex groups"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        def survey(obj):
            max_weights = {}
            for vg in obj.vertex_groups:
                max_weights[vg.index] = 0

            for v in obj.data.vertices:
                for vg in v.groups:
                    vg_i = vg.group
                    w = obj.vertex_groups[vg_i].weight(v.index)
                    if (vg_i not in max_weights or w > max_weights[vg_i]):
                        max_weights[vg_i] = w
            return max_weights

        obj = context.active_object
        maxWeight = survey(obj)
        # Remove groups in inverse order to prevent removal changing indices
        for vg_i in sorted(maxWeight.keys(), reverse=True):
            if maxWeight[vg_i] <= 0:
                #print("delete vertex group {}".format(obj.vertex_groups[vg_i].name))
                obj.vertex_groups.remove(obj.vertex_groups[vg_i]) # actually remove the group
     
        return {'FINISHED'} 


def menu_func(self, context):
    self.layout.operator(RemoveZeroWeightVertexGroups.bl_idname)


def register():
    bpy.utils.register_class(RemoveZeroWeightVertexGroups)
    bpy.types.MESH_MT_vertex_group_context_menu.append(menu_func)


def unregister():
    bpy.utils.unregister_class(RemoveZeroWeightVertexGroups)
    bpy.types.MESH_MT_vertex_group_context_menu.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()