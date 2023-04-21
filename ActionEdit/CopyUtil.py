import bpy
import re

# keyの内容をコピーする
def copy_keyframe(src_point, dest_point):
    dest_point.amplitude = src_point.amplitude
    dest_point.back = src_point.back
    # new_point.co
    # new_point.co_ui
    dest_point.easing = src_point.easing
    dest_point.handle_left = src_point.handle_left
    dest_point.handle_left_type = src_point.handle_left_type
    dest_point.handle_right = src_point.handle_right
    dest_point.handle_right_type = src_point.handle_right_type
    dest_point.interpolation = src_point.interpolation
    dest_point.period = src_point.period


# 子Boneからキーを削除する
def remove_all_keys_from_children(action, children_list):
    children_dict = {bone.name: bone for bone in children_list}

    # 子Boneからキーフレームを削除する
    for fcurve in action.fcurves:
        # ボーン名と適用対象の取得
        match = re.search(r'pose.bones\["(.+?)"\].+?([^.]+$)', fcurve.data_path)
        if match:
            bone_name, target = match.groups()

            # 子のBoneだけ処理
            if bone_name in children_dict:
                # キーを削除
                action.fcurves.remove(fcurve)


# 子Boneから指定ボーンまでの距離を計測する。到達できなければ-1
def calc_parent_distance(parent_bone, bone, count=0):
    if bone == None:
        return -1
    if parent_bone.name == bone.name:
        return count
    return calc_parent_distance(parent_bone, bone.parent, count+1)


# pose_boneの子を再帰的に選択する
def pose_bone_gather_children(pose_bone, select_func=None):
    pose_bone_list = []
    for child_pose_bone in pose_bone.children:
        # 選択関数があれば選択するかチェック
        if select_func != None:
            if not select_func(child_pose_bone):
                continue  # 非選択になったら処理しない
        # 登録
        pose_bone_list.append(child_pose_bone)

        # 再帰で潜って追加していく
        pose_bone_list.extend(pose_bone_gather_children(child_pose_bone))

    return pose_bone_list

