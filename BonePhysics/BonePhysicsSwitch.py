import bpy
from . import BonePhysicsUtil

# Enable/Disable Cloth
# =================================================================================================
class ANIME_POSE_TOOLS_OT_enable_cloth_modifire(bpy.types.Operator):
    bl_idname = "anime_pose_tools.enable_cloth_modifire"
    bl_label = "Enable Cloth"

    # execute
    def execute(self, context):
        # 選択中オブジェクトのClothを有効に
        for obj in context.selected_objects:
            if obj.type == "MESH":
                obj.modifiers["Cloth"].show_viewport = True
                obj.modifiers["Cloth"].show_render = True
        return {'FINISHED'}

class ANIME_POSE_TOOLS_OT_disable_cloth_modifire(bpy.types.Operator):
    bl_idname = "anime_pose_tools.disable_cloth_modifire"
    bl_label = "Disable Cloth"

    # execute
    def execute(self, context):
        # 選択中オブジェクトのClothを無効に
        for obj in context.selected_objects:
            if obj.type == "MESH":
                obj.modifiers["Cloth"].show_viewport = False
                obj.modifiers["Cloth"].show_render = False
        return {'FINISHED'}


# Enable/Disable Cloth IK
# =================================================================================================
class ANIME_POSE_TOOLS_OT_select_cloth_ik(bpy.types.Operator):
    bl_idname = "anime_pose_tools.select_cloth_ik"
    bl_label = "Select APT_IK Bones"

    # execute
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active

        # 選択中ポーズボーンのAPT_IKを有効に
        for pose_bone in armature.pose.bones:
            for constraint in pose_bone.constraints:
                if constraint.name == BonePhysicsUtil.BONE_IK_PREFIX:
                    pose_bone.bone.select = True

        return {'FINISHED'}


class ANIME_POSE_TOOLS_OT_enable_cloth_ik(bpy.types.Operator):
    bl_idname = "anime_pose_tools.enable_cloth_ik"
    bl_label = "Enable IK"

    # execute
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active

        # 選択中ポーズボーンのAPT_IKを有効に
        for pose_bone in armature.pose.bones:
            if pose_bone.bone.select:
                for constraint in pose_bone.constraints:
                    if constraint.name == BonePhysicsUtil.BONE_IK_PREFIX:
                        constraint.enabled = True
        return {'FINISHED'}


class ANIME_POSE_TOOLS_OT_disable_cloth_ik(bpy.types.Operator):
    bl_idname = "anime_pose_tools.disable_cloth_ik"
    bl_label = "Disable IK"

    # execute
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        # 選択中ポーズボーンのAPT_IKを無効に
        for pose_bone in armature.pose.bones:
            if pose_bone.bone.select:
                for constraint in pose_bone.constraints:
                    if constraint.name == BonePhysicsUtil.BONE_IK_PREFIX:
                        constraint.enabled = False
        return {'FINISHED'}


# UI描画設定
# =================================================================================================
label = "Switch"
classes = [
    ANIME_POSE_TOOLS_OT_enable_cloth_modifire,
    ANIME_POSE_TOOLS_OT_disable_cloth_modifire,
    ANIME_POSE_TOOLS_OT_select_cloth_ik,
    ANIME_POSE_TOOLS_OT_enable_cloth_ik,
    ANIME_POSE_TOOLS_OT_disable_cloth_ik,
]

def draw(parent, context, layout):
    layout.label(text="IK Enable/Disable:")

    box = layout.box()
    box.enabled = context.mode == "POSE"
    box.operator("anime_pose_tools.select_cloth_ik")
    row = box.row()
    row.operator("anime_pose_tools.enable_cloth_ik")
    row.operator("anime_pose_tools.disable_cloth_ik")

    layout.label(text="Cloth Enable/Disable:")

    box = layout.box()
    box.enabled = context.mode == "OBJECT" and bpy.context.view_layer.objects.active.type == "MESH"
    row = box.row()
    row.operator("anime_pose_tools.enable_cloth_modifire")
    row.operator("anime_pose_tools.disable_cloth_modifire")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.work_collection = bpy.props.StringProperty(name="Work Collection Name", default=BonePhysicsUtil.DEFAULT_WORK_COLLECTION)
    bpy.types.Scene.collision_box_width = bpy.props.FloatProperty(name="Collision Box Width", min=0, max=1, default=0.25)
    bpy.types.Scene.collision_box_height = bpy.props.FloatProperty(name="Collision Box Height", min=0, max=1, default=0.5)
    bpy.types.Scene.ik_target_mesh = bpy.props.PointerProperty(type=bpy.types.Object)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
