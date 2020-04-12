bl_info = {
    "name": "Invert pose into new armature",
    "blender": (2, 80, 0),
    "category": "Object",
    "desc": ("Create new armature with the target armature's pose "
             "as the rest pose, and the target armature's rest pose "
             "as the current pose"),
}
import bpy
import mathutils


class InvertPose(bpy.types.Operator):
    bl_idname = 'object.invert_pose'
    bl_label = "Invert pose into new armature"
    bl_options = {'REGISTER', 'UNDO'}
    

    def main(self):
        obj = self.context.active_object
        self.arm = obj.copy()
        self.arm.data = obj.data.copy()
        for c in obj.users_collection:
            c.objects.link(self.arm)
        self.arm.name = obj.name + '_INVERTED'
        self.context.view_layer.objects.active = self.arm
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply()
        for p in obj.pose.bones:
            scale_inv = mathutils.Vector(1.0 / c for c in p.scale)
            loc_inv = p.location.copy()
            loc_inv.negate()
            rot_inv = p.rotation_quaternion.conjugated()
            self.arm.pose.bones[p.name].scale = scale_inv  
            self.arm.pose.bones[p.name].location = loc_inv  
            self.arm.pose.bones[p.name].rotation_quaternion = rot_inv
        bpy.ops.object.mode_set(mode='OBJECT')
    

    def execute(self, context):
        self.context = context
        self.arm = None
        try:
            self.main()
        except Exception as e:
            if self.arm:
                bpy.data.objects.remove(self.arm)
            raise e
        else:
            return {'FINISHED'}


def register():
    bpy.utils.register_class(InvertPose)


def unregister():
    bpy.utils.unregister_class(InvertPose)


if __name__ == "__main__":
    register()
    
    bpy.ops.object.invert_pose()