bl_info = {
    "name": "Generate shape keys from rules",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy


def reset_shape_keys(obj):
    obj.show_only_shape_key = False
    obj.active_shape_key_index = 0
    while obj.active_shape_key:
        obj.active_shape_key.value = 0
        obj.active_shape_key_index += 1
    obj.active_shape_key_index = 0


def make_shape_keys(obj, rules, delete_mixers=False):
    mix_keys = rules['mix_keys']
    reset_shape_keys(obj)
    for shape_key_name in rules['generated_shape_keys']:
        if shape_key_name in obj.data.shape_keys.key_blocks:
            continue
        mix_values = rules['generated_shape_keys'][shape_key_name]
        for i, v in enumerate(mix_values):
            try:
                print("setting key {} to {}".format(mix_keys[i], v))
                obj.data.shape_keys.key_blocks[mix_keys[i]].value = v
            except IndexError:
                pass
        print('creating new mix {}'.format(shape_key_name))
        obj.shape_key_add(name=shape_key_name, from_mix=True)
        reset_shape_keys(obj)
    if delete_mixers:
        for k in mix_keys:
            obj.shape_key_remove(obj.data.shape_keys.key_blocks[k])


class GenerateShapeKeys(bpy.types.Operator):
    bl_idname = 'object.shape_key_generate'
    bl_label = "Generate shape keys from rules"
    bl_options = {'REGISTER', 'UNDO'}
    
    delete_mix_keys = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        obj = context.active_object
        data = {}
        exec(bpy.data.texts['morphs'].as_string(), data)
        morphs = (data['morphs'])
        # Get dict key from custom props
        rule_key = obj.data['generate_shape_keys']
        make_shape_keys(obj, morphs[rule_key], self.delete_mix_keys)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(GenerateShapeKeys)


def unregister():
    bpy.utils.unregister_class(GenerateShapeKeys)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
    #bpy.ops.object.shape_key_generate()