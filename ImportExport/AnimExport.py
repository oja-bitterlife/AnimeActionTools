import bpy
import json, traceback, re


# Export AnimationData to JSON
# =================================================================================================
class ANIME_ACTION_TOOLS_OT_anim_export(bpy.types.Operator):
    bl_idname = "anime_action_tools.anim_export"
    bl_label = "Export Animations"

    # ファイル選択ダイアログ
    filepath: bpy.props.StringProperty()
    filter_glob: bpy.props.StringProperty(
        default="*.json",
    )
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # execute
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        if armature.type != "ARMATURE":
            self.report({'ERROR'}, "activeなオブジェクトがArmatureじゃない(通常あり得ない)")
            return {'CANCELLED'}

        # かならず.jsonに
        if not self.filepath.lower().endswith(".json"):
            self.filepath += ".json"

        data = {}
        data["bones"] = self.get_animation_bones([bone.name for bone in armature.pose.bones])
        data["animation"] = self.get_animation_data(data["bones"])

        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except:
            self.report({'ERROR'}, traceback.format_exc())
            return {'CANCELLED'}


        return {'FINISHED'}


    # Actionで使われているBoneのみ拾う
    def get_animation_bones(self, all_bones):
        use_bones = []
        for action in bpy.data.actions:
            for fcurve in action.fcurves:
                if fcurve.group.name in use_bones:
                    continue  # 登録済み
                # ActiveなArmatureのみ対象
                if fcurve.group.name in all_bones:
                    use_bones.append(fcurve.group.name)
        return use_bones


    # アニメーションデータを全部取得する
    def get_animation_data(self, bones):
        actions = {}
        for action in bpy.data.actions:
            action_data = self.get_action_data(action, bones)

            # データがあったら登録
            if action_data:
                actions[action.name] = action_data

        return actions

    # アクション１つのデータを取得する
    def get_action_data(self, action, bones):
        fcurves = {}
        for fcurve in action.fcurves:
            # bone名はリストで一括変更できるように、インデックス番号で扱う
            try:
                bone_index = bones.index(fcurve.group.name)
            except:
                continue

            replaced_data_path = fcurve.data_path.replace("\"%s\"" % fcurve.group.name, "@%d" % bone_index)
            if replaced_data_path not in fcurves:
                fcurves[replaced_data_path] = {}

            # point設定
            point_array = []
            for point in fcurve.keyframe_points:
                point_data = {
                    "co": point.co.to_tuple(),
                    "easing": point.easing,
                    "handle_left": point.handle_left.to_tuple(),
                    "handle_left_type": point.handle_left_type,
                    "handle_right": point.handle_right.to_tuple(),
                    "handle_right_type": point.handle_right_type,
                    "interpolation": point.interpolation,
                    "period": point.period,
                    "type": point.type,
                }
                point_array.append(point_data)
            fcurves[replaced_data_path][fcurve.array_index] = point_array

        return fcurves



# To Rest Position
# =================================================================================================
class ANIME_ACTION_TOOLS_OT_anim_import(bpy.types.Operator):
    bl_idname = "anime_action_tools.anim_import"
    bl_label = "Import Animations"

    # ファイル選択ダイアログ
    filepath: bpy.props.StringProperty()
    filter_glob: bpy.props.StringProperty(
        default="*.json",
    )
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # execute
    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        if armature.type != "ARMATURE":
            self.report({'ERROR'}, "activeなオブジェクトがArmatureじゃない(通常あり得ない)")
            return {'CANCELLED'}

        # JSON読み込み
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
        except:
            self.report({'ERROR'}, traceback.format_exc())
            return {'CANCELLED'}

        bones = data["bones"]
        animation = data["animation"]
        target_bones = [bone.name for bone in armature.pose.bones]

        # bone存在チェック
        for bone_name in bones:
            if bone_name not in target_bones:
                self.report({'ERROR'}, "boneが存在しません: %s" % bone_name)
                continue


        # アクションの作成
        for action_name in animation:
            new_action = bpy.data.actions.new(name=action_name)

            # ボーンごとに処理
            data_paths = animation[action_name]
            for data_path_name in data_paths:
                # パス名の分解
                m = re.match(r'.+\[@(\d+)\]\..+', data_path_name)
                if not m:
                    self.report({'ERROR'}, "deta_pathが不正です: %s" % data_path_name)
                    continue

                # ボーン名,data_path名の取得
                bone_name = bones[int(m.groups()[0])]
                data_path = data_path_name.replace("@%s" % m.groups()[0], "\"%s\"" % bone_name)

                # bone存在チェック
                if bone_name not in target_bones:
                    continue

                # array_index(x,y,z,w)ごとに処理
                for array_index_no in data_paths[data_path_name]:
                    array_index = int(array_index_no)  # {0:w 1:x 2:y 3:z} or {0:x 1:y 2:z}
                    new_fcurve = new_action.fcurves.new(data_path=data_path, index=array_index, action_group=bone_name)

                    # キーフレームの追加
                    points = data_paths[data_path_name][array_index_no]
                    for point in points:
                        new_point = new_fcurve.keyframe_points.insert(point["co"][0], point["co"][1], keyframe_type=point["type"])
                        # 残りのデータ転送
                        new_point.easing = point["easing"]
                        new_point.handle_left = point["handle_left"]
                        new_point.handle_left_type = point["handle_left_type"]
                        new_point.handle_right = point["handle_right"]
                        new_point.handle_right_type = point["handle_right_type"]
                        new_point.interpolation = point["interpolation"]
                        new_point.period = point["period"]

        return {'FINISHED'}


# UI描画設定
# =================================================================================================
label = "Import/Export Animations"
classes = [
    ANIME_ACTION_TOOLS_OT_anim_import,
    ANIME_ACTION_TOOLS_OT_anim_export
]

def draw(parent, context, layout):
    if context.view_layer.objects.active.type != "ARMATURE":
        layout.enabled = False
    if context.mode != "OBJECT":
        layout.enabled = False

    layout.operator("anime_action_tools.anim_import")
    layout.operator("anime_action_tools.anim_export")

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
