import bpy

# 回転系のKeyframeを子ボーンにコピーする
class ANIME_HAIR_TOOLS_OT_copy_rotation_keys(bpy.types.Operator):
    bl_idname = "anime_hair_tools.copy_rotation_keys"
    bl_label = "Copy Rotation Keys"

    # execute
    def execute(self, context):
        # 選択中のボーン一つ一つを親にして処理
        for target_bone in context.selected_pose_bones:
            self.copy_rotation_keys(target_bone, context.scene.AHT_keyframe_offset, context.scene.AHT_keyframe_damping)
        return {'FINISHED'}

    # target_bone以下のボーンにKeyframeをコピーする
    def copy_rotation_keys(self, target_bone, keyframe_offset, keyframe_damping):
        # gather children
        children_list = pose_bone_gather_children(target_bone)

        # 現在のActionを取得
        action = bpy.context.active_object.animation_data.action

        # 一旦子Boneからキーを削除する
        remove_all_keys_from_children(action, children_list)

        # target_boneのキーフレームを取得
        keyframes = {}
        for fcurve in action.fcurves:
            # ボーン名と適用対象の取得
            match = re.search(r'pose.bones\["(.+?)"\].+?([^.]+$)', fcurve.data_path)
            if match:
                bone_name, attribute = match.groups()

            # ActiveBoneだけ処理
            if bone_name == target_bone.name:
                # 回転だけコピー
                if attribute != "rotation_quaternion" and attribute != "rotation_euler" and attribute != "rotation_axis_angle":
                    continue
                keyframes["%s:%d" % (attribute, fcurve.array_index)] = fcurve.keyframe_points

        # 子Boneにkeyframeを突っ込む
        for child_bone in children_list:
            parent_distance = calc_parent_distance(target_bone, child_bone)
            # 通常ありえないはずだけど、親まで到達できなかった
            if parent_distance <= 0:
                print("error: parent not found!")
                continue

            # keyframeの転送開始
            for keyname in keyframes:
                # まずは突っ込み先のFCurveを作成
                attribute, index = keyname.split(":")
                index = int(index)
                data_path = 'pose.bones["%s"].%s' % (child_bone.name, attribute)
                new_fcurve = action.fcurves.new(data_path=data_path, index=index, action_group=child_bone.name)

                # keyframe_pointsのコピー
                for point in keyframes[keyname]:
                    # 変化
                    offset = parent_distance * keyframe_offset
                    damping = pow(keyframe_damping, parent_distance)

                    # quaternionのときはwだけ操作する
                    if attribute == "rotation_quaternion":
                        if index != 0:
                            damping = 1
                        else:
                            damping = 1.0 / damping  # wには逆数を使う

                    # Keyframeの追加
                    new_point = new_fcurve.keyframe_points.insert(point.co[0]+offset, point.co[1]*damping)

                    # co以外の残りのパラメータをコピー
                    copy_keyframe(point, new_point) 


# 子ボーンのキーフレームを削除する。スッキリさせて再出発用
class ANIME_HAIR_TOOLS_OT_remove_children_keys(bpy.types.Operator):
    bl_idname = "anime_hair_tools.remove_children_keys"
    bl_label = "Remove Children Keys"

    # execute
    def execute(self, context):
        # 選択中のボーン一つ一つを親にして処理
        for target_bone in context.selected_pose_bones:
            self.remove_children_keys(target_bone)
        return {'FINISHED'}

    # target_boneの子boneにあるKeyframeを削除する
    def remove_children_keys(self, target_bone):
        # gather children
        children_list = pose_bone_gather_children(target_bone)

        # 現在のActionを取得
        action = bpy.context.active_object.animation_data.action

        # 子Boneからキーを削除する
        remove_all_keys_from_children(action, children_list)


# UI描画設定
# =================================================================================================
label = "Propagate Action To Children"
classes = [
    ANIME_HAIR_TOOLS_OT_copy_rotation_keys,
    ANIME_HAIR_TOOLS_OT_remove_children_keys,
]

def draw(parent, context, layout):
    if context.mode != "POSE":
        layout.enabled = False

    # Actionを子BoneにCopyする
    box = layout.box()
    box.prop(context.scene, "AHT_keyframe_offset", text="Keyframe Offset")
    box.prop(context.scene, "AHT_keyframe_damping", text="Keyframe Damping")
    box.operator("anime_hair_tools.copy_rotation_keys")
    box.operator("anime_hair_tools.remove_children_keys")

    layout.label(text="Copy Action:")
    layout.operator("anime_hair_tools.copy_action")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.AHT_keyframe_offset = bpy.props.IntProperty(name = "keyframe offset", default=5)
    bpy.types.Scene.AHT_keyframe_damping = bpy.props.FloatProperty(name = "keyframe damping", default=1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)