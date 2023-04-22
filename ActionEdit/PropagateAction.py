import bpy, re, mathutils
from . import CopyUtil

# 回転系のKeyframeを子ボーンにコピーする
class ANIME_HAIR_TOOLS_OT_copy_rotation_keys(bpy.types.Operator):
    bl_idname = "anime_hair_tools.copy_rotation_keys"
    bl_label = "Propagate Rotation"

    # execute
    def execute(self, context):
        # 選択中のボーン一つ一つを親にして処理
        for target_bone in context.selected_pose_bones:
            self.copy_rotation_keys(context, target_bone)
        return {'FINISHED'}

    # target_bone以下のボーンにKeyframeをコピーする
    def copy_rotation_keys(self, context, target_bone):
        # gather children
        children_list = CopyUtil.pose_bone_gather_children(target_bone)

        # 現在のActionを取得
        action = bpy.context.active_object.animation_data.action

        # 一旦子Boneからキーを削除する
        CopyUtil.remove_all_keys_from_children(action, children_list)

        # target_boneのキーフレームを取得
        keyframe_rots = {}
        for fcurve in action.fcurves:
            # ボーン名と適用対象の取得
            match = re.search(r'pose.bones\["(.+?)"\].+?([^.]+$)', fcurve.data_path)
            if match:
                bone_name, attribute = match.groups()

            # ActiveBoneだけ処理
            if bone_name == target_bone.name:
                # 回転だけコピー(モードと一致するもののみ)
                if target_bone.rotation_mode == "QUATERNION":
                    if attribute != "rotation_quaternion":
                        continue
                elif target_bone.rotation_mode == "AXIS_ANGLE":
                    if attribute != "rotation_axis_angle":
                        continue
                else:
                    if attribute != "rotation_euler":
                        continue

                # 回転情報の回収
                for i, point in enumerate(fcurve.keyframe_points):
                    point_key = "p_%d" % i
                    if point_key not in keyframe_rots:
                        if attribute == "rotation_quaternion":
                            keyframe_rots[point_key] = [point.co[0], 0, 0, 0, 0]  # w, x, y, z
                        elif attribute == "rotation_axis_angle":
                            keyframe_rots[point_key] = [point.co[0], 0, 0, 0, 0]  # w, (x, y, z)
                        else:  # rotation_euler
                            keyframe_rots[point_key] = [point.co[0], 0, 0, 0]  # x, y, z
    
                    keyframe_rots[point_key][fcurve.array_index+1] = point.co[1]

        # 子Boneにkeyframeを突っ込む
        for child_bone in children_list:
            parent_distance = CopyUtil.calc_parent_distance(target_bone, child_bone)
            # 通常ありえないはずだけど、親まで到達できなかった
            if parent_distance <= 0:
                print("error: parent not found!")
                continue

            # 回転モードを合わせる
            child_bone.rotation_mode = target_bone.rotation_mode

            # まずは突っ込み先のFCurveを作成
            if target_bone.rotation_mode == "QUATERNION":
                data_path = 'pose.bones["%s"].%s' % (child_bone.name, "rotation_quaternion")
                new_fcurves = [action.fcurves.new(data_path=data_path, index=i, action_group=child_bone.name) for i in range(4)]
            elif target_bone.rotation_mode == "AXIS_ANGLE":
                data_path = 'pose.bones["%s"].%s' % (child_bone.name, "rotation_axis_angle")
                new_fcurves = [action.fcurves.new(data_path=data_path, index=i, action_group=child_bone.name) for i in range(4)]
            else:
                data_path = 'pose.bones["%s"].%s' % (child_bone.name, "rotation_euler")
                new_fcurves = [action.fcurves.new(data_path=data_path, index=i, action_group=child_bone.name) for i in range(3)]

            # keyframeの転送開始
            for point_rot in keyframe_rots.values():
                # 線形
                frame_no = point_rot[0] + int(context.scene.AHT_propagate_offset * parent_distance)
                ratio = max(0, 1 - (context.scene.AHT_propagate_damping * parent_distance))

                # quaternionは一旦axis_angleに変えて計算
                if target_bone.rotation_mode == "QUATERNION":
                    axis, angle = mathutils.Quaternion((point_rot[1], point_rot[2], point_rot[3], point_rot[4])).to_axis_angle()
                    q = mathutils.Quaternion(axis, angle*ratio)
                    new_fcurves[0].keyframe_points.insert(frame_no, q.w)
                    new_fcurves[1].keyframe_points.insert(frame_no, q.x)
                    new_fcurves[2].keyframe_points.insert(frame_no, q.y)
                    new_fcurves[3].keyframe_points.insert(frame_no, q.z)
                elif target_bone.rotation_mode == "AXIS_ANGLE":
                    new_fcurves[0].keyframe_points.insert(frame_no, point_rot[1] * ratio)
                    new_fcurves[1].keyframe_points.insert(frame_no, point_rot[2])
                    new_fcurves[2].keyframe_points.insert(frame_no, point_rot[3])
                    new_fcurves[3].keyframe_points.insert(frame_no, point_rot[4])
                else:
                    new_fcurves[0].keyframe_points.insert(frame_no, point_rot[1] * ratio)
                    new_fcurves[1].keyframe_points.insert(frame_no, point_rot[2] * ratio)
                    new_fcurves[2].keyframe_points.insert(frame_no, point_rot[3] * ratio)


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
        children_list = CopyUtil.pose_bone_gather_children(target_bone)

        # 現在のActionを取得
        action = bpy.context.active_object.animation_data.action

        # 子Boneからキーを削除する
        CopyUtil.remove_all_keys_from_children(action, children_list)


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
    setting_box = layout.box()
    setting_box.prop(context.scene, "AHT_propagate_type", text="Type")
    setting_box.prop(context.scene, "AHT_propagate_offset", text="Offset")
    setting_box.prop(context.scene, "AHT_propagate_damping", text="Damping")
    button_box = layout.box()
    button_box.operator("anime_hair_tools.copy_rotation_keys")
    button_box.operator("anime_hair_tools.remove_children_keys")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.AHT_propagate_type = bpy.props.IntProperty(name = "propagate type", default=1)
    bpy.types.Scene.AHT_propagate_offset = bpy.props.FloatProperty(name = "propagate offset", default=0)
    bpy.types.Scene.AHT_propagate_damping = bpy.props.FloatProperty(name = "propagate damping", default=1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
