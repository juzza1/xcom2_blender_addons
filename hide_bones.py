bl_info = {
    "name": "Hide ungrouped bones",
    "blender": (2, 80, 0),
    "category": "Object",
    "desc": ("Create new armature with the target armature's pose "
             "as the rest pose, and the target armature's rest pose "
             "as the current pose"),
}
import bpy
import mathutils


class HideUngroupedBones(bpy.types.Operator):
    bl_idname = 'object.bone_hide_ungrouped'
    bl_label = "Hide ungrouped bones"
    bl_options = {'REGISTER', 'UNDO'}
    

    def execute(self, context):
        self.context = context
        
        seen = set()
        for obj in self.context.selected_objects:
            for v in obj.data.vertices:
                for vg in v.groups:
                    seen.add(obj.vertex_groups[vg.group].name)

        for obj in self.context.selected_objects:
            arm = obj.find_armature()
            if not arm:
                continue
            for b in arm.data.bones:
                if b.name not in seen:
                    b.hide = True

        return {'FINISHED'}


def register():
    bpy.utils.register_class(HideUngroupedBones)


def unregister():
    bpy.utils.unregister_class(HideUngroupedBones)


if __name__ == "__main__":
    register()
    
    bpy.ops.object.bone_hide_ungrouped()