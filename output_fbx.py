bl_info = {
    "name": "Export FBXs for Xcom 2",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy

from collections import defaultdict
import os
import os.path
import time


class ExportX2FBX(bpy.types.Operator):
    bl_idname = 'object.export_x2_fbx'
    bl_label = "Export FBXs for Xcom 2"
    bl_options = {'REGISTER', 'UNDO'}


    def export_fbx(self, outname):
        try:
            export_dir = bpy.data.objects['fbx_settings']['output_directory']
        except KeyError:
            export_dir = os.path.join(bpy.path.abspath('//'), 'fbx_out')
        os.makedirs(export_dir, exist_ok=True)
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(export_dir, outname + '.fbx'),
            check_existing=False,
            use_selection=True,
            mesh_smooth_type='FACE',
            add_leaf_bones=False,
            use_tspace=True,
            bake_anim=False
        )


    def exportable_vgs(self, obj):
        for vg in obj.vertex_groups.keys():
            if vg.startswith('_SM_'):
                yield vg
            

    def select_activate(self, obj):
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action='DESELECT')
        except RuntimeError:
            pass
        obj.select_set(True)
        self.context.view_layer.objects.active = obj
        
        
    def copy_obj(self, obj):
        cop = obj.copy()
        cop.data = obj.data.copy()
        self.context.scene.collection.objects.link(cop)
        return cop
    
    
    def sort_materials(self, obj):
        srt = sorted(ms.material.name for ms in obj.material_slots)
        for mn in reversed(srt):
            for i, ms in enumerate(obj.material_slots):
                if ms.material.name == mn:
                    obj.active_material_index = i
            ret = set()
            while 'CANCELLED' not in ret:
                ret = bpy.ops.object.material_slot_move(direction='UP')

    
    def execute(self, context):
        self.context = context
        fbx_components = {}
        selected_objs = [s for s in self.context.selected_editable_objects if self.exportable_vgs(s)]

        # Check if we have unselected items with same vg names, so we dont have to select all
        # dependent objects every time
        dependent_objs = []
        selected_vgs = [vg for s in selected_objs for vg in self.exportable_vgs(s)]
        for obj in selected_objs:
            for coll in obj.users_collection:
                for c_obj in coll.objects:
                    for vg in c_obj.vertex_groups.keys():
                        if vg in selected_vgs:
                            dependent_objs.append(c_obj)
        
        # Automirror any objects with that custom prop set
        mirror_objs = []
        for obj in set(selected_objs + dependent_objs):
            if obj.get('automirror'):
                c = self.copy_obj(obj)
                self.select_activate(c)
                bpy.ops.object.automirror()
                mirror_objs.append(c)
        
        for obj in set(selected_objs + dependent_objs + mirror_objs):
            root_object = None
            for m in obj.modifiers:
                if isinstance(m, bpy.types.ArmatureModifier):
                    root_object = (m.object)
                    break
            if not root_object:
                continue
            
            for vg in self.exportable_vgs(obj):
                copied = self.copy_obj(obj)
                self.select_activate(copied)
                # From my other addon
                bpy.ops.object.modifiers_apply_with_shapekeys()
                # Check if any shape key begins with '_', if so, assume we want to flatten them
                if not copied.data.shape_keys \
                        or any(k.name.startswith('_') for k in copied.data.shape_keys.key_blocks):
                    # Yet another addon
                    bpy.ops.object.shape_key_flatten()
                # another addon
                if 'generate_shape_keys' in copied.data:
                    self.select_activate(copied)
                    bpy.ops.object.shape_key_generate(delete_mix_keys=False)
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.reveal()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group=vg)
                bpy.ops.mesh.select_mode(type="FACE")
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.delete(type='FACE')
                if vg in fbx_components:
                    if fbx_components[vg]['root'] != root_object:
                        self.report({'ERROR'}, 'Object {} armature {} differs from others in {}'.format(
                            obj.name, root_object.name, vg))
                        return {'CANCELLED'}
                    fbx_components[vg]['objects'].append(copied)
                else:
                    fbx_components[vg] = {'objects': [copied], 'root': root_object}

        for i, export_name in enumerate(fbx_components):
            join_objs = fbx_components[export_name]['objects']
            self.select_activate(join_objs[0])
            for obj in join_objs[1:]:
                obj.select_set(True)
            fbx_components[export_name]['root'].hide_set(False)
            fbx_components[export_name]['root'].select_set(True)
            bpy.ops.object.join()
            self.sort_materials(join_objs[0])
            self.export_fbx(export_name.lstrip('_'))
            bpy.data.objects.remove(join_objs[0])
            fbx_components[export_name]['root'].hide_set(True)
        self.report({'INFO'}, 'Exported {} FBXs'.format(len(fbx_components)))
            
        for m in mirror_objs:
            bpy.data.objects.remove(m)
                
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportX2FBX.bl_idname)


def register():
    bpy.utils.register_class(ExportX2FBX)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportX2FBX)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
    bpy.ops.object.export_x2_fbx()