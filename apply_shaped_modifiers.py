bl_info = {
    "name": "Apply modifiers to objects with shape keys",
    "blender": (2, 80, 0),
    "category": "Object",
}
import bpy

def apply_modifiers(obj):
    # some magic, assume we dont want to apply last armature modifier (for fbx export)
    last_arm = None
    if obj.modifiers and isinstance(obj.modifiers[-1], bpy.types.ArmatureModifier):
        last_arm = obj.modifiers[-1]
    for m in (m for m in obj.modifiers if m != last_arm):
        print('applying {} to {}'.format(m, obj))
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        # Bad (disabled?) modifier, just nuke it
        except RuntimeError:
            bpy.ops.object.modifier_remove(modifier=m.name)


class ApplyShapedModifiers(bpy.types.Operator):
    bl_idname = 'object.modifiers_apply_with_shapekeys'
    bl_label = "Apply modifiers with shape keys"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):

        obj = context.active_object
        # Test if we don't have shape keys
        if not obj.data.shape_keys:
            apply_modifiers(obj)
            return {'FINISHED'}

        copied = obj.copy()
        copied.data = obj.data.copy()
        for c in bpy.data.collections:
            if obj.name in c.all_objects:
                bpy.data.collections[c.name].objects.link(copied)
                break
        else:
            context.scene.collection.objects.link(copied)

        def inner(target, source):
            context.view_layer.objects.active = target
            target.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=True)
            apply_modifiers(target)
            # Relies on base shape key being the first one, and all others
            # being relative to it
            source.select_set(True)
            source.active_shape_key_index = 0
            while source.active_shape_key:
                # Copies key from source to target object
                bpy.ops.object.shape_key_transfer()
                # If we copy to target without keys, a new base key is created, remove this and
                # consider the first copied key as base instead
                if source.active_shape_key_index == 0:
                    target.active_shape_key_index = 0
                    bpy.ops.object.shape_key_remove()
                    target.active_shape_key_index = 0
                    target.active_shape_key.name = source.active_shape_key.name
                target.active_shape_key_index = source.active_shape_key_index
                target.active_shape_key.slider_min = source.active_shape_key.slider_min
                target.active_shape_key.slider_max = source.active_shape_key.slider_max
                target.active_shape_key.value = source.active_shape_key.value
                source.active_shape_key_index += 1

        inner(copied, obj)
        inner(obj, copied)

        bpy.ops.object.select_all(action='DESELECT')
        copied.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}
    

def menu_func(self, context):
    self.layout.operator(ApplyShapedModifiers.bl_idname)


def register():
    bpy.utils.register_class(ApplyShapedModifiers)
    #bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ApplyShapedModifiers)
    #bpy.types.VIEW3D_MT_object.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
    bpy.ops.object.modifiers_apply_with_shapekeys()