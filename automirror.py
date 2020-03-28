bl_info = {
    "name": "Automirror",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy
import bmesh


class AutoMirror(bpy.types.Operator):
    bl_idname = 'object.automirror'
    bl_label = "Automirror"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.context = context
        obj = context.active_object

        # Mirror object
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        self.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        for v in bm.verts:
            v.co.y *= -1
        for f in bm.faces:
            bmesh.utils.face_flip(f)
        bmesh.update_edit_mesh(me)
        bpy.ops.object.mode_set(mode="OBJECT")

        old_vgs = [vg.name for vg in obj.vertex_groups]
        for vg in old_vgs:
            # shoulders dont have first letter uppercase, might be others
            if vg == 'rShoulder':
                opposite = 'lShoulder'
            elif vg == 'lShoulder':
                opposite = 'rShoulder'
            elif vg.startswith('L') and len(vg) >= 2 and vg[1].isupper():
                opposite = 'R' + vg[1:]
            elif vg.startswith('R') and len(vg) >= 2 and vg[1].isupper():
                opposite = 'L' + vg[1:]
            elif vg.startswith('_SM_') and 'Left' in vg:
                opposite = vg.replace('Left', 'Right')
            elif vg.startswith('_SM_') and 'Right' in vg:
                opposite = vg.replace('Right', 'Left')
            else:
                continue
            #print('{}: renaming {} to {}'.format(obj.name, vg, opposite))
            obj.vertex_groups[vg].name = opposite
            
        # Apply automirror to material prop magic
        for k in obj.keys():
            if k.startswith('mat_'):
                repl = None
                if '_Left_' in k:
                    repl = k.replace('_Left_', '_Right_')
                elif '_Right_' in k:
                    repl = k.replace('_Right_', '_Left_')
                    print('we here boys')
                if repl:
                    print('setting {} to {} for {}'.format(repl, obj[k], obj.name))
                    obj[repl] = obj[k]
                else:
                    print('couldnt replace {}'.format(k))
        
        print("{}'s keys: {}".format(obj.name, obj.keys()))
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AutoMirror)


def unregister():
    bpy.utils.unregister_class(AutoMirror)
    

if __name__ == "__main__":
    register()
    
    #bpy.ops.object.automirror()