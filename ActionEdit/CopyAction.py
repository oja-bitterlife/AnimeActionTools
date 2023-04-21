import bpy, re

# キーフレームの単純コピー
class ANIME_HAIR_TOOLS_OT_copy_action(bpy.types.Operator):
    bl_idname = "anime_hair_tools.copy_action"
    bl_label = "Copy Active To Selected"

    # execute
    def execute(self, context):
        active_bone = context.active_pose_bone

        # ActiveBoneはコピー元なのでそれ以外をリストする
        selected_list = [bone for bone in context.selected_pose_bones if bone != active_bone]

        # コピー先BoneのKeyframeを削除する
        action = context.active_object.animation_data.action
        remove_all_keys_from_children(action, selected_list)

        # active_boneのキーフレームを取得
        for fcurve in action.fcurves:
            # ボーン名と適用対象の取得
            match = re.search(r'pose.bones\["(.+?)"\].+?([^.]+$)', fcurve.data_path)
            if match:
                bone_name, attribute = match.groups()

            # ActiveBoneからコピーする
            if bone_name == active_bone.name:
                # 選択リストのBoneに転送
                for select_bone in selected_list:
                    data_path = 'pose.bones["%s"].%s' % (select_bone.name, attribute)
                    new_fcurve = action.fcurves.new(data_path=data_path, index=fcurve.array_index, action_group=select_bone.name)

                    # keyframeの転送
                    for point in fcurve.keyframe_points:
                        # 転送先Keyframeの追加
                        new_point = new_fcurve.keyframe_points.insert(point.co[0], point.co[1])

                        # co以外の残りのパラメータをコピー
                        copy_keyframe(point, new_point) 

        return {'FINISHED'}


# UI描画設定
# =================================================================================================
label = "Copy Action"
classes = [
    ANIME_HAIR_TOOLS_OT_copy_action,
]
def draw(parent, context, layout):
    if context.mode != "POSE":
        layout.enabled = False

    # Actionを子BoneにCopyする
    layout.operator("anime_hair_tools.copy_action")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.AHT_keyframe_offset = bpy.props.IntProperty(name = "keyframe offset", default=5)
    bpy.types.Scene.AHT_keyframe_damping = bpy.props.FloatProperty(name = "keyframe damping", default=1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
