bl_info = {
    "name": "Export FBXs for Xcom 2",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy

import atexit
from collections import defaultdict
import os
import os.path
from pprint import pprint
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
            object_types={'ARMATURE', 'MESH'},
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
        self.copies_to_be_deleted.append(cop)
        cop.data = obj.data.copy()
        for c in obj.users_collection:
            c.objects.link(cop)
        return cop
    
    
    def sort_materials(self, obj):
        for mat_name in sorted(obj.material_slots.keys(), reverse=True):
            for i, ms in enumerate(obj.material_slots):
                if ms.material.name == mat_name:
                    obj.active_material_index = i
            ret = set()
            while 'CANCELLED' not in ret:
                ret = bpy.ops.object.material_slot_move(direction='UP')
                
                
    def mirror_copy(self, obj):
        c = self.copy_obj(obj)
        self.select_activate(c)
        bpy.ops.object.modifiers_apply_with_shapekeys()
        bpy.ops.object.automirror()
        return c
    

    def add_unselected(self, objects):
        fbx_objs = {}
        for obj in objects:
            dep_objs = {}
            for coll in obj.users_collection:
                for c_obj in (co for co in coll.objects if co != obj):
                    for cvg in c_obj.vertex_groups.keys():
                        if cvg not in dep_objs:
                            dep_objs[cvg] = set()
                        dep_objs[cvg].add(c_obj)
            for vg in self.exportable_vgs(obj):
                if vg not in fbx_objs:
                    fbx_objs[vg] = set()
                fbx_objs[vg].add(obj)
                if vg in dep_objs:
                    fbx_objs[vg] |= dep_objs[vg]
        return fbx_objs


    def get_join_objs(self, vg_name, objs):
        join_objs = []
        root_object = None
        for obj in objs:
            copied = self.copy_obj(obj)
            self.select_activate(copied)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.reveal()
            bpy.ops.object.mode_set(mode="OBJECT")
            # From my other addon
            bpy.ops.object.modifiers_apply_with_shapekeys()
            for m in copied.modifiers:
                if isinstance(m, bpy.types.ArmatureModifier):
                    if not root_object:
                        root_object = (m.object)
                    elif m.object == root_object:
                        break
                    else:
                        emsg = '{} has wrong armature, wanted: {}'.format(obj, root_object)
                        self.report({'ERROR'}, emsg)
                        raise Exception(emsg)
            if not root_object:
                emsg = '{} does not have an armature'.format(obj)
                self.report({'ERROR'}, emsg)
                raise Exception(emsg)
            # From my other addon
            bpy.ops.object.modifiers_apply_with_shapekeys()
            # Check if any shape key begins with '_', if so, assume we want to flatten them
            if copied.data.shape_keys and any(k.name.startswith('_') for k in copied.data.shape_keys.key_blocks):
                # Yet another addon
                bpy.ops.object.shape_key_flatten()
            # another addon
            if 'generate_shape_keys' in copied.data:
                self.select_activate(copied)
                bpy.ops.object.shape_key_generate(delete_mix_keys=True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group=vg_name)
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='FACE')
            
            # Run some cleanups
            self.select_activate(copied)
            bpy.ops.object.material_slot_remove_zero_influence()
            self.select_activate(copied)
            bpy.ops.object.vertex_group_remove_zero_weight_groups()
            
            join_objs.append(copied)
            
        return join_objs, root_object
    
    
    def cleanup(self):
        for obj in self.copies_to_be_deleted:
            try:
                bpy.data.objects.remove(obj)
            except ReferenceError:
                pass

    
    def main(self):
        self.copies_to_be_deleted = []
        atexit.register(self.cleanup)
        
        selected = self.context.selected_editable_objects
        
        # First, make any automirrors
        # This is a bit inefficient, but do it to simplify the codeuntil it becomes a problem
        selected_mirrors = []
        all_objs = {c_obj for obj in selected for coll in obj.users_collection for c_obj in coll.objects}
        for obj in all_objs:
            if obj.get('automirror'):
                c = self.mirror_copy(obj)
                if obj in selected:
                    selected_mirrors.append(c)

        fbx_objs = self.add_unselected(selected + selected_mirrors)
        
        print(fbx_objs.keys())
        for export_vg in fbx_objs:
            join_objs, root_object = self.get_join_objs(export_vg, fbx_objs[export_vg])
            
            # More magic, change material name if we have custom prop to avoid multiple material slots in ue
            for obj in join_objs:
                for k in (k for k in obj.keys() if k.startswith('mat_')):
                    affected_vg = k[4:]
                    if affected_vg == export_vg:
                        orig, new = obj[k].split('->')
                        obj.material_slots[orig].material = bpy.data.materials[new]
                    
            # Join all belonging to this export vg
            self.select_activate(join_objs[0])
            for obj in join_objs[1:]:
                obj.select_set(True)
            bpy.ops.object.join()
            self.sort_materials(join_objs[0])
            root_object.hide_set(False)
            root_object.select_set(True)
            self.export_fbx(export_vg.lstrip('_'))
            root_object.hide_set(True)

        self.report({'INFO'}, 'Exported {} FBXs'.format(len(fbx_objs)))
        

    def execute(self, context):
        self.context = context
        try:
            self.main()
        except Exception as e:
            raise e
        else:
            return {'FINISHED'}
        finally:
            self.cleanup()


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