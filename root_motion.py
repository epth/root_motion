import bpy
import json
import re
from mathutils import Matrix, Vector, Euler
class Name_Normalize_Rule_Item(bpy.types.PropertyGroup):

    previous_string : bpy.props.StringProperty(name="Previous String")
    replace_string:bpy.props.StringProperty(name="Replace String")
    rename_is_all:bpy.props.BoolProperty(name="Rename All Bones")
    enable:bpy.props.BoolProperty(name="Enable")
    index:bpy.props.IntProperty(name="index")

class BoneRenameData(bpy.types.PropertyGroup):
    
    rename_rules=bpy.props.CollectionProperty(type=Name_Normalize_Rule_Item,name='Rename Rules')
    file=bpy.props.StringProperty(name='FilePath',subtype='FILE_PATH')
        
class RootMotionData(bpy.types.PropertyGroup):
        
    def _update_action(self,context):
        bpy.context.active_object.animation_data.action=self.action
    
    hip = bpy.props.StringProperty(name="Hip Bone")
    root_add_name = bpy.props.StringProperty(name="Root Bone Add Name")
    root = bpy.props.StringProperty(name="Root Bone")
    #action=bpy.props.StringProperty(name="Action",set=_set_action,get=_get_action)
    action=bpy.props.PointerProperty(name="Action",type=bpy.types.Action,update=_update_action)
    is_all_action=bpy.props.BoolProperty(name="Root ALL Action")
    is_xyz=bpy.props.BoolProperty(name="XYZ",description='If selected,root motion will contain xyz translation,If not selected,only contain xy translaion')
    scale_origin=bpy.props.FloatVectorProperty(name="Origin Scale",default=(1,1,1))
    scale_target=bpy.props.FloatVectorProperty(name="Target Scale",default=(1,1,1))
    



class Root_motion_add_root_bone(bpy.types.Operator):
    bl_idname = "rootmotion.add_root"
    bl_label = "Add Root Motion Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        root_add_name=context.scene.rm_data.root_add_name
        if root_add_name:
            return valid_armature(context) and (root_add_name not in context.active_object.pose.bones)
        else:
            return valid_armature(context) and ("root.motion" not in context.active_object.pose.bones)
        return False

    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        root_add_name=context.scene.rm_data.root_add_name
        if root_add_name:
            bpy.ops.armature.bone_primitive_add(name=root_add_name)
        else:
            bpy.ops.armature.bone_primitive_add(name='root.motion')
            root_add_name='root.motion'

        context.scene.rm_data.root=root_add_name
        bpy.ops.object.mode_set(mode = 'OBJECT')
        return {'FINISHED'}
    
class Root_motion_read_origin(bpy.types.Operator):
    bl_idname = "rootmotion.read_origin"
    bl_label = "Read Original Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    bl_description="Click once and Store origin scale of Armature,default scale value is (1,1,1),so if never click,[Apply RotScale] won't change scale of the armature"

    @classmethod
    def poll(cls, context):
        return valid_armature(context)

    def execute(self, context):
        #init data
        obj = context.object
        
        context.scene.rm_data.scale_origin=obj.scale
        return {'FINISHED'}
    
    
class Root_motion_apply_rotscale(bpy.types.Operator):
    bl_idname = "rootmotion.apply_rotscale"
    bl_label = "Apply Rotation&Scale"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return valid_armature(context) and context.scene.rm_data.hip and ( context.scene.rm_data.action or context.scene.rm_data.is_all_action)

    def execute(self, context):
        obj = context.object
        
        hip_str=context.scene.rm_data.hip
        hip=obj.pose.bones.get(hip_str)
        
        root_str=context.scene.rm_data.root
        root=obj.pose.bones.get(root_str)
        
        action=context.scene.rm_data.action
        scale_origin=context.scene.rm_data.scale_origin
        scale_target=context.scene.rm_data.scale_target
        
        is_all_action=context.scene.rm_data.is_all_action
        #scale_origin=Vector((0.01,0.01,0.01))
        #scale_target=Vector((1,1,1))
        
        if is_all_action:
            for item_action in bpy.data.actions:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                
                # fix all bones translation for appling scale
                for bone in obj.pose.bones:
                    bone_fc_array=get_curve_loc(item_action,bone)
                    for fc in bone_fc_array:
                        scale_rate=scale_origin[fc.array_index]/scale_target[fc.array_index]
                        for point in fc.keyframe_points:
                            bone_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y*scale_rate)

#                hip_fc_array=get_curve_loc(item_action,hip)
#                
#                for fc in hip_fc_array:
#                    scale_rate=scale_origin[fc.array_index]/scale_target[fc.array_index]
#                    for point in fc.keyframe_points:
#                        hip_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y*scale_rate)
        else:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

            # fix all bones translation for appling scale
            for bone in obj.pose.bones:
                bone_fc_array=get_curve_loc(action,bone)
                for fc in bone_fc_array:
                    scale_rate=scale_origin[fc.array_index]/scale_target[fc.array_index]
                    for point in fc.keyframe_points:
                        bone_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y*scale_rate)
            
#            hip_fc_array=get_curve_loc(action,hip)
#            
#            for fc in hip_fc_array:
#                scale_rate=scale_origin[fc.array_index]/scale_target[fc.array_index]
#                for point in fc.keyframe_points:
#                    hip_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y*scale_rate)
        return {'FINISHED'}
    
def select_object(name):
    print('select_object ',name)
    ob = bpy.context.scene.objects[name]       # Get the object
    bpy.ops.object.select_all(action='DESELECT') # Deselect all objects
    bpy.context.view_layer.objects.active = ob   # Make the cube the active object 
    ob.select_set(True)                          # Select the cube

def get_curve_loc(action,bone):
    bone_loc_path=bone.path_from_id('location')
    bone_fc_array=[fc for fc in action.fcurves if fc.data_path == bone_loc_path]
    return bone_fc_array

class Root_motion_opt(bpy.types.Operator):
    bl_idname = "rootmotion.root_motion"
    bl_label = "Root Motion"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return valid_armature(context) and context.scene.rm_data.hip and context.scene.rm_data.root and ( context.scene.rm_data.action or context.scene.rm_data.is_all_action)
    
    def execute(self, context):
        #ob=C.object
        #action=ob.animation_data.action
        #bone=obj.pose.bones.get('CC_Base_Hip')
        #bp=bone.path_from_id('rotation_quaternion')
        #fc = action.fcurves.find(bp, index=3)
        self.func_new(context)
        return {'FINISHED'}
    
    def func_new(self,context):
        #init data
        obj = context.object
        scene=context.scene
        
        hip_str=context.scene.rm_data.hip
        hip=obj.pose.bones.get(hip_str)
        
        root_str=context.scene.rm_data.root
        root=obj.pose.bones.get(root_str)
        
        action=context.scene.rm_data.action
        is_all_action=context.scene.rm_data.is_all_action
        is_xyz=context.scene.rm_data.is_xyz
        ignore=1
        
        if is_all_action:
            for item_action in bpy.data.actions:
                #root bone insert a keyframe
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode="POSE")
                #scene.frame_set(1) # 1 for keyframe start with
                obj.animation_data.action=item_action
                root.keyframe_insert(data_path='location')
                
                
                hip_loc_path=hip.path_from_id('location')
                hip_fc_array=[fc for fc in item_action.fcurves if fc.data_path == hip_loc_path]
                
                root_loc_path=root.path_from_id('location')
                root_fc_array=[fc for fc in item_action.fcurves if fc.data_path == root_loc_path]
                
                
                for fc in hip_fc_array:
                    if not is_xyz and fc.array_index==ignore:
                        hip_fc_array[fc.array_index].mute=False
                        root_fc_array[fc.array_index].mute=True
                        continue
                    hip_fc_array[fc.array_index].mute=True
                    root_fc_array[fc.array_index].mute=False
                    for point in fc.keyframe_points:
                        root_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y)
            
                    
        else:
            #root bone insert a keyframe
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode="POSE")
            #scene.frame_set(1) # 1 for keyframe start with
            obj.animation_data.action=action
            root.keyframe_insert(data_path='location')
                     
            
            hip_loc_path=hip.path_from_id('location')
            hip_fc_array=[fc for fc in action.fcurves if fc.data_path == hip_loc_path]
            
            root_loc_path=root.path_from_id('location')
            root_fc_array=[fc for fc in action.fcurves if fc.data_path == root_loc_path]
            
            for fc in hip_fc_array:
                if not is_xyz and fc.array_index==ignore:
                    hip_fc_array[fc.array_index].mute=False
                    root_fc_array[fc.array_index].mute=True
                    continue
                hip_fc_array[fc.array_index].mute=True
                root_fc_array[fc.array_index].mute=False
                for point in fc.keyframe_points:
                    root_fc_array[fc.array_index].keyframe_points.insert(point.co.x,point.co.y)
            #if not is_xyz:
                #root_fc_array[ignore].mute=True
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        obj.data.edit_bones[hip_str].parent=obj.data.edit_bones[root_str]
        bpy.ops.object.mode_set(mode = 'OBJECT')
                
        return {'FINISHED'}
    
    def func_old(self,context):
        obj = context.object
        scene=context.scene
        hip_str=context.scene.rm_data.hip
        root_str=context.scene.rm_data.root
        hip=obj.pose.bones.get(hip_str)
        root=obj.pose.bones.get(root_str)
        action=context.scene.rm_data.action
        is_all_action=context.scene.rm_data.is_all_action
        is_xyz=context.scene.rm_data.is_xyz
        
        bpy.data.objects.get(obj.name).select_set(state=True)
        if is_all_action:
            for item_action in bpy.data.actions:
                
                bpy.ops.object.mode_set(mode = 'EDIT')
                obj.data.edit_bones[hip_str].parent=None
                bpy.ops.object.mode_set(mode = 'OBJECT')
                
                obj.animation_data.action=item_action
                cl=root.constraints.new('COPY_LOCATION')
                cl.target=obj
                cl.subtarget=context.scene.rm_data.hip
                cl.use_z=False
                
                helper1_name=''
                helper2_name=''
                if is_xyz:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
                    helper1_name=bpy.context.active_object.name
                    helper1=bpy.data.objects[helper1_name]
                    cl=helper1.constraints.new('COPY_LOCATION')
                    cl.target=obj
                    cl.subtarget=context.scene.rm_data.hip
                    select_object(obj.name)
                    bpy.context.scene.frame_set(1)
                    bpy.ops.object.mode_set(mode = 'POSE')
                    if context.selected_pose_bones_from_active_object:
                        for bone in context.selected_pose_bones_from_active_object:
                            bone.bone.select=False
                    root.bone.select=True
                    bpy.ops.view3d.snap_cursor_to_selected()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
                    helper2_name=bpy.context.active_object.name
                    helper2=bpy.data.objects[helper2_name]
                    select_object(helper1_name)
                    helper2.select_set(True)
                    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                    
                    select_object(obj.name)
                    bpy.ops.object.mode_set(mode = 'POSE')
                    cl=root.constraints.new('COPY_LOCATION')
                    cl.target=helper2
                    cl.use_x=False
                    cl.use_y=False
                
                range=get_keyframe_range(item_action)
                
                root.bone.select=True
                if context.selected_pose_bones_from_active_object:
                    for bone in context.selected_pose_bones_from_active_object:
                        bone.bone.select=False
                root.bone.select=True
                bpy.ops.nla.bake(frame_start=range[0], frame_end=range[1], visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, only_selected=True,bake_types={'POSE'})
                
                if is_xyz:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    select_object(helper1_name)
                    bpy.ops.object.delete(use_global=False)
                    select_object(helper2_name)
                    bpy.ops.object.delete(use_global=False)
                
                select_object(obj.name)
                bpy.ops.object.mode_set(mode = 'POSE')
                cl=hip.constraints.new('LIMIT_LOCATION')
                cl.use_min_x=True
                cl.use_max_x=True
                cl.use_min_y=True
                cl.use_max_y=True
                if is_xyz:
                    cl.min_x=hip.location[0]
                    cl.max_x=hip.location[0]
                    cl.min_y=hip.location[1]
                    cl.max_y=hip.location[1]
                    cl.use_min_z=True
                    cl.min_z=hip.location[2]
                    cl.use_max_z=True
                    cl.max_z=hip.location[2]
                    cl.owner_space='LOCAL'
                
                if context.selected_pose_bones_from_active_object:
                    for bone in context.selected_pose_bones_from_active_object:
                        bone.bone.select=False
                hip.bone.select=True
                bpy.ops.nla.bake(frame_start=range[0], frame_end=range[1], visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, only_selected=True,bake_types={'POSE'})

                bpy.ops.object.mode_set(mode = 'EDIT')
                obj.data.edit_bones[hip_str].parent=obj.data.edit_bones[root_str]
                bpy.ops.object.mode_set(mode = 'OBJECT')
                
        else:
            
            bpy.ops.object.mode_set(mode = 'EDIT')
            obj.data.edit_bones[hip_str].parent=None
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
            item_action=bpy.data.actions.get(action)
            obj.animation_data.action=item_action
            
            cl=root.constraints.new('COPY_LOCATION')
            cl.target=obj
            cl.subtarget=context.scene.rm_data.hip
            cl.use_z=False
            
            helper1_name=''
            helper2_name=''
            if is_xyz:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
                    helper1_name=bpy.context.active_object.name
                    helper1=bpy.data.objects[helper1_name]
                    cl=helper1.constraints.new('COPY_LOCATION')
                    cl.target=obj
                    cl.subtarget=context.scene.rm_data.hip
                    select_object(obj.name)
                    bpy.context.scene.frame_set(1)
                    bpy.ops.object.mode_set(mode = 'POSE')
                    if context.selected_pose_bones_from_active_object:
                        for bone in context.selected_pose_bones_from_active_object:
                            bone.bone.select=False
                    root.bone.select=True
                    bpy.ops.view3d.snap_cursor_to_selected()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
                    helper2_name=bpy.context.active_object.name
                    helper2=bpy.data.objects[helper2_name]
                    select_object(helper1_name)
                    helper2.select_set(True)
                    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                    
                    select_object(obj.name)
                    bpy.ops.object.mode_set(mode = 'POSE')
                    cl=root.constraints.new('COPY_LOCATION')
                    cl.target=helper2
                    cl.use_x=False
                    cl.use_y=False
            
            range=get_keyframe_range(item_action)
            if context.selected_pose_bones_from_active_object:
                for bone in context.selected_pose_bones_from_active_object:
                    bone.bone.select=False
            root.bone.select=True
            bpy.ops.nla.bake(frame_start=range[0], frame_end=range[1], visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, only_selected=True,bake_types={'POSE'})
            
            if is_xyz:
                bpy.ops.object.mode_set(mode = 'OBJECT')
                select_object(helper1_name)
                bpy.ops.object.delete(use_global=False)
                select_object(helper2_name)
                bpy.ops.object.delete(use_global=False)
            
            select_object(obj.name)
            bpy.ops.object.mode_set(mode = 'POSE')
            cl=hip.constraints.new('LIMIT_LOCATION')
            cl.use_min_x=True
#            cl.min_x=hip.location[0]
            cl.use_max_x=True
#            cl.max_x=hip.location[0]
            cl.use_min_y=True
#            cl.min_y=hip.location[1]
            cl.use_max_y=True
#            cl.max_y=hip.location[1]
            if is_xyz:
                cl.min_x=hip.location[0]
                cl.max_x=hip.location[0]
                cl.min_y=hip.location[1]
                cl.max_y=hip.location[1]
                cl.use_min_z=True
                cl.min_z=hip.location[2]
                cl.use_max_z=True
                cl.max_z=hip.location[2]
                cl.owner_space='LOCAL'
            
            if context.selected_pose_bones_from_active_object:
                for bone in context.selected_pose_bones_from_active_object:
                    bone.bone.select=False
            hip.bone.select=True
            bpy.ops.nla.bake(frame_start=range[0], frame_end=range[1], visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, only_selected=True,bake_types={'POSE'})

            bpy.ops.object.mode_set(mode = 'EDIT')
            obj.data.edit_bones[hip_str].parent=obj.data.edit_bones[root_str]
        bpy.ops.object.mode_set(mode = 'OBJECT')
        return {'FINISHED'}
    
class ANIM_root_bone_add_constraints(bpy.types.Operator):
    bl_idname = "anim.root_bone_add_constraints"
    bl_label = "Root add Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return valid_armature(context)

    def execute(self, context):
        obj = context.object
        scene=context.scene
        hip=obj.pose.bones.get(context.scene.rm_data.hip)
        root=obj.pose.bones.get(context.scene.rm_data.root)
        cl=root.constraints.new('COPY_LOCATION')
        cl.target=obj
        cl.subtarget=context.scene.rm_data.hip
        cl.use_z=False

        return {'FINISHED'}


def ShowMessageBox(message = "", title = "Message", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)



class Bone_rename_rules_load(bpy.types.Operator):
    bl_idname = "bonerename.rules_load"
    bl_label = "Import"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        rename_rules=context.scene.rb_data.rename_rules
        
        
        data = load()
        if isinstance(data,dict):
            for key in data:
                newrule=rename_rules.add()
                newrule.previous_string=data[key]['previous_string']
                newrule.replace_string=data[key]['replace_string']
                newrule.rename_is_all=data[key]['rename_is_all']
                newrule.enable=data[key]['enable']
                newrule.index=len(rename_rules)
        return {'FINISHED'}
    
class Bone_rename_rules_save(bpy.types.Operator):
    bl_idname = "bonerename.rules_save"
    bl_label = "Export"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        json_data={}
        rename_rules=context.scene.rb_data.rename_rules
        
        for index,rule in enumerate(rename_rules):
            json_data.update({index:{}})
            json_data[index]["previous_string"]=rule.previous_string
            json_data[index]["replace_string"]=rule.replace_string
            json_data[index]["rename_is_all"]=rule.rename_is_all
            json_data[index]["enable"]=rule.enable
            
#            data = json.loads(str(json_data))
            store(json_data)
        return {'FINISHED'}

class Bone_rename_rules_insert(bpy.types.Operator):
    bl_idname = "bonerename.rules_insert"
    bl_label = "Insert"
    bl_options = {'REGISTER', 'UNDO'}
    
    prop_index=bpy.props.IntProperty(name="index")
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        rename_rules=context.scene.rb_data.rename_rules
        
        newrule=rename_rules.add()
        newrule.enable=True
        newrule.rename_is_all=True
        print(len(rename_rules)-1,self.prop_index+1)
        rename_rules.move(len(rename_rules)-1,self.prop_index+1)
        return {'FINISHED'}
    
class Bone_rename_rules_add(bpy.types.Operator):
    bl_idname = "bonerename.rules_add"
    bl_label = "Add"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        rename_rules=context.scene.rb_data.rename_rules
        newrule=rename_rules.add()
        newrule.enable=True
        newrule.rename_is_all=True
        return {'FINISHED'}

class Bone_rename_rules_delete(bpy.types.Operator):
    bl_idname = "bonerename.rules_delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}
    
    prop_index=bpy.props.IntProperty(name="index")
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        context.scene.rb_data.rename_rules.remove(self.prop_index)
        return {'FINISHED'}
    
class Bone_rename_replace(bpy.types.Operator):
    bl_idname = "bonerename.replace"
    bl_label = "Replace Name"
    bl_options = {'REGISTER', 'UNDO'}
    
    prop_index=bpy.props.IntProperty(name="index")
    prop_is_oneshot=bpy.props.BoolProperty(name="is_oneshot")
    @classmethod
    def poll(cls, context):
        return valid_armature(context)
    def execute(self, context):
        obj=context.object
        if self.prop_is_oneshot:
            previous_string=context.scene.rb_data.rename_rules[self.prop_index].previous_string
            rename_is_all=context.scene.rb_data.rename_rules[self.prop_index].rename_is_all
            replace_string=context.scene.rb_data.rename_rules[self.prop_index].replace_string
            if rename_is_all:
                for bone in obj.data.bones:
                    name_tmp=bone.name
#                    if -1!=name_tmp.lower().find(previous_string.lower()):
#                        bone.name=name_tmp.lower().replace(previous_string.lower(),replace_string)
                    bone.name=re.sub(previous_string,replace_string,name_tmp,flags=re.I)
                pass
            else:
                if bpy.context.object.data.bones.active:
                    name_tmp=obj.data.bones.active.name
        #            if name_tmp.find(previous_string):
#                    obj.data.bones.active.name=name_tmp.lower().replace(previous_string.lower(),replace_string)
                    obj.data.bones.active.name=re.sub(previous_string,replace_string,name_tmp,flags=re.I)
                else:
                    ShowMessageBox("Didn\'t Select a bone in Pose Mode") 

        else:
            for rule in context.scene.rb_data.rename_rules:
                enable=rule.enable
                if not enable:
                    continue
                
                previous_string=rule.previous_string
                rename_is_all=rule.rename_is_all
                replace_string=rule.replace_string
                if rename_is_all:
                    for bone in obj.data.bones:
                        name_tmp=bone.name
#                        if -1!=name_tmp.lower().find(previous_string.lower()):
#                            bone.name=name_tmp.lower().replace(previous_string.lower(),replace_string)
                        bone.name=re.sub(previous_string,replace_string,name_tmp,flags=re.I)
                    pass
                else:
                    if bpy.context.object.data.bones.active:
                        name_tmp=obj.data.bones.active.name
            #            if name_tmp.find(previous_string):
#                        obj.data.bones.active.name=name_tmp.lower().replace(previous_string.lower(),replace_string)
                        obj.data.bones.active.name=re.sub(previous_string,replace_string,name_tmp,flags=re.I)
                    else:
                        ShowMessageBox("Didn\'t Select a bone in Pose Mode") 

        return {'FINISHED'}

# save data to json file
def store(data):
    rename_rulesfile=bpy.context.scene.rb_data.file
    with open(rename_rulesfile, 'w') as fw:
        
        # json_str = json.dumps(data)
        # fw.write(json_str)
        
        json.dump(data,fw)
def load():
    rename_rulesfile=bpy.context.scene.rb_data.file
    with open(rename_rulesfile,'r') as f:
        data = json.load(f)
        return data

#Panel rename
class RootMotion_PT_Bone_rename_panel(bpy.types.Panel):
    bl_label = "Bone Rename"
    bl_category = "Root_Motion"
    bl_idname = "ROOTMOTION_PT_BONE_RENAME_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    def draw(self, context):
        layout = self.layout
        obj = context.object
        rename_rules=context.scene.rb_data.rename_rules
        rename_rulesfile=context.scene.rb_data.file
        
        if not obj or obj.type != 'ARMATURE':
            row =layout.row()
            row.label(text="Select armature with bones first!", icon='ARMATURE_DATA')
            return
        row = layout.row()
        row.label(text="Active armature is: " + obj.name,icon='ARMATURE_DATA')
        layout.separator()
        
        row = layout.row()
        row.prop(context.scene.rb_data,'file',text='Data')
        
        row = layout.row(align=True)
        row.operator("bonerename.rules_load",text='Import/Load')
        row.operator("bonerename.rules_save",text='Export/Save')
        #########################3
        
        row = layout.row()
        row.label(text='Name Normalize Rules:')
        
        row = layout.row()
        row.operator("bonerename.rules_add")
        layout.separator()
        
        row = layout.row(align=True)
        opt=row.operator("bonerename.replace",text='Apply Rule List')
        opt.prop_is_oneshot=False
        
        layout.separator()
        layout.separator()
        
        for index,item in enumerate(rename_rules):
            row = layout.row(align=True)
            row.scale_x =0.4
            row.label(text='Find String')
            row.scale_x =0.6
            row.prop(item, "previous_string", text='')
            
            row = layout.row(align=True)
            row.scale_x =0.4
            row.label(text='Replace String')
            row.scale_x =0.6
            row.prop(item, "replace_string", text='')
            
            row = layout.row(align=True)
            row.prop(item, "enable",text='Enable')
            row.prop(item, "rename_is_all",text='All bones')
            row.scale_x =0.3
            opt=row.operator("bonerename.replace",text='y')
            opt.prop_is_oneshot=True
            opt.prop_index=index
            opt=row.operator("bonerename.rules_insert",text='+')
            opt.prop_index=index
            opt=row.operator("bonerename.rules_delete",text='-')
            opt.prop_index=index
            
            
            
            
            layout.separator()
            layout.separator()
        
        row = layout.row(align=True)
        opt=row.operator("bonerename.replace",text='Apply Rule List')
        opt.prop_is_oneshot=False
        

        

class RootMotion_PT_Root_motion_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Root Motion"
    bl_category = "Root_Motion"
    bl_idname = "ROOTMOTION_PT_ROOT_MOTION_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj or obj.type != 'ARMATURE':
            row =layout.row()
            row.label(text="Select armature with bones first!", icon='ARMATURE_DATA')
            return
#        if not obj.animation_data.action:
#            row =layout.row()
#            row.label(text="please select an action", icon='WORLD_DATA')
#            return

#        col = layout.column(align=True)
#        row = col.row(align=True)
#        row.label(text="H", icon='WORLD_DATA')
#        row.label(text="He", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active armature is: " + obj.name,icon='ARMATURE_DATA')
        layout.separator()
        
        row = layout.row()
        row.operator("rootmotion.read_origin",text="Read Original Data")
        row =layout.row()
        row.prop(context.scene.rm_data, "scale_origin", text="Origin Scale")
        row =layout.row()
        row.prop(context.scene.rm_data, "scale_target", text="Target Scale")
        layout.separator()

        row =layout.row()
        row.label(text="Add Root Motion Bone With Name:")
        row =layout.row()
        row.prop(context.scene.rm_data, "root_add_name", text="")
        
       
        row =layout.row()
        row.operator("rootmotion.add_root",text="Add Root Motion Bone")

        layout.separator()
        layout.separator()

        row =layout.row()
        row.prop_search(context.scene.rm_data, "hip", obj.pose, "bones", text="Hip")

        row =layout.row()
        row.prop_search(context.scene.rm_data, "root", obj.pose, "bones", text="Root")
        
        row =layout.row()
        row.prop_search(context.scene.rm_data, "action", bpy.data, "actions", text="Action")
        row.prop(context.scene.rm_data,"is_xyz",text="XYZ")
        row.prop(context.scene.rm_data,"is_all_action",text="ALL")
        
        row = layout.row()
        row.operator("rootmotion.apply_rotscale",text="Apply RotScale")
        row = layout.row()
        row.operator("rootmotion.root_motion",text='Root Motion Make')
def get_keyframe_range(action):
    if action:
        return action.frame_range
    else:
        print ("no actions")
def get_keyframe_range_all():
    if bpy.data.actions:

        # get all actions
        action_list = [action.frame_range for action in bpy.data.actions]

        # sort, remove doubles and create a set
        keys = (sorted(set([item for sublist in action_list for item in sublist])))

    else:
        print ("no actions")

def valid_armature(context):
    skel = context.active_object
    if skel and skel.type == 'ARMATURE':
        if len(skel.pose.bones):
                return skel
    return None

celpec_classes=[
    Name_Normalize_Rule_Item,
    BoneRenameData,
    RootMotionData,
    Bone_rename_rules_delete,
    Bone_rename_rules_add,
    Bone_rename_rules_insert,
    Bone_rename_rules_load,
    Bone_rename_rules_save,
    Bone_rename_replace,
    Root_motion_read_origin,
    RootMotion_PT_Bone_rename_panel,
    RootMotion_PT_Root_motion_panel,
    Root_motion_add_root_bone,
    Root_motion_apply_rotscale,
    Root_motion_opt
    ]
def register():
    for item in celpec_classes:
        bpy.utils.register_class(item)

    bpy.types.Scene.rm_data = bpy.props.PointerProperty(type=RootMotionData)
    bpy.types.Scene.rb_data = bpy.props.PointerProperty(type=BoneRenameData)


def unregister():
#    del bpy.types.Scene.rb_data
#    del bpy.types.Scene.rm_data
    
    for item in [i for i in reversed(celpec_classes)]:
        bpy.utils.unregister_class(item)

if __name__ == "__main__":
    register()
