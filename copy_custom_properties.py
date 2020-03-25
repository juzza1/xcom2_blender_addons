bl_info = {
    "name": "Copy custom properties",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy


class CopyCustomProperties(bpy.types.Operator):
    bl_idname = 'object.custom_properties_copy'
    bl_label = "Copy custom properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.context = context
        ob_sel = self.context.selected_editable_objects
        ob_act = self.context.object

        for ob in ob_sel:
            if ob == ob_act:
                continue
            for p in ob_act.keys():
                print('copy {} from {} to {}'.format(p, ob_act.name, ob.name))
                ob[p] = ob_act[p]
        if len(ob_sel) > 1:
            count = len(ob_act.keys())
        else:
            count = 0
        self.report({'INFO'}, 'Copied {} key{}'.format(count, '' if count == 1 else 's'))
        return {'FINISHED'}


def register():
    bpy.utils.register_class(CopyCustomProperties)


def unregister():
    bpy.utils.unregister_class(CopyCustomProperties)
    

if __name__ == "__main__":
    register()
    
    bpy.ops.object.custom_properties_copy()