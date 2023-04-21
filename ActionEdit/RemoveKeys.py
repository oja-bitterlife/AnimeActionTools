import bpy
import re


# Listup Selected Bones
# =================================================================================================
class ANIME_POSE_TOOLS_OT_remove_loc_keys(bpy.types.Operator):
    bl_idname = "anime_pose_tools.remove_loc_keys"
    bl_label = "Loc"

    # execute
    def execute(self, context):
        delete_keyframes(context, ["location"])
        return{'FINISHED'}

class ANIME_POSE_TOOLS_OT_remove_rot_keys(bpy.types.Operator):
    bl_idname = "anime_pose_tools.remove_rot_keys"
    bl_label = "Rot"

    # execute
    def execute(self, context):
        delete_keyframes(context, ["rotation_quaternion", "rotation_euler", "rotation_axis_angle"])
        return{'FINISHED'}

class ANIME_POSE_TOOLS_OT_remove_scale_keys(bpy.types.Operator):
    bl_idname = "anime_pose_tools.remove_scale_keys"
    bl_label = "Scale"

    # execute
    def execute(self, context):
        delete_keyframes(context, ["scale"])
        return{'FINISHED'}

class ANIME_POSE_TOOLS_OT_remove_other_keys(bpy.types.Operator):
    bl_idname = "anime_pose_tools.remove_other_keys"
    bl_label = "BBone"

    # execute
    def execute(self, context):
        delete_keyframes(context, ["bbone_curveinx", "bbone_curveoutx", "bbone_curveinz", "bbone_curveoutz", "bbone_rollin", "bbone_rollout", "bbone_scalein", "bbone_scaleout", "bbone_easein", "bbone_easeout"])
        return{'FINISHED'}


# キーフレームを全部削除する
# targets: キーフレームを削除するチャンネルを指定する
def delete_keyframes(context, targets):
    # 現在のActionを取得
    action = context.active_object.animation_data.action
    if not action:
        return  # Actionが未登録(キーも何もない)

    children_dict = {bone.name: bone for bone in context.selected_pose_bones}

    # 子Boneからキーフレームを削除する
    for fcurve in action.fcurves:
        # ボーン名と適用対象の取得
        match = re.search(r'pose.bones\["(.+?)"\].+?([^.]+$)', fcurve.data_path)
        if match:
            bone_name, target = match.groups()

            # 子のBoneだけ処理
            if bone_name in children_dict:
                # キーを削除
                if target in targets:
                    action.fcurves.remove(fcurve)


# UI描画設定
# =================================================================================================
label = "Remove Keys in All Frame"

classes = [
    ANIME_POSE_TOOLS_OT_remove_loc_keys,
    ANIME_POSE_TOOLS_OT_remove_rot_keys,
    ANIME_POSE_TOOLS_OT_remove_scale_keys,
    ANIME_POSE_TOOLS_OT_remove_other_keys,
]

def draw(parent, context, layout):
    if context.mode != "POSE":
        layout.enabled = False

    row = layout.row()
    row.operator("anime_pose_tools.remove_loc_keys")
    row.operator("anime_pose_tools.remove_rot_keys")
    row.operator("anime_pose_tools.remove_scale_keys")
    row.operator("anime_pose_tools.remove_other_keys")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

