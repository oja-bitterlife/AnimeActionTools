import bpy
from mathutils import Vector

from . import BonePhysicsUtil

# 箱生成用
BOX_VERTS = [(0,-0.5,0),(0,0.5,0),  # 0-1
            (-0.5,-0.5,-0.5),(0,-0.5,-0.5),(0.5,-0.5,-0.5),  # 2-4
            (-0.5,-0.5,0),(0.5,-0.5,0),  # 5-6
            (-0.5,-0.5,0.5),(0,-0.5,0.5),(0.5,-0.5,0.5),  # 7-9
            (-0.5,0.5,-0.5),(0,0.5,-0.5),(0.5,0.5,-0.5),  # 10-12
            (-0.5,0.5,0),(0.5,0.5,0),  # 13-14
            (-0.5,0.5,0.5),(0,0.5,0.5),(0.5,0.5,0.5)]  # 15-17

BOX_FACES = [(2,3,0,5),(3,4,6,0),(5,0,8,7),(0,6,9,8),  # 上面
            (10,13,1,11),(11,1,14,12),(13,15,16,1),(1,16,17,14),  # 下面
            (2,5,13,10),(5,7,15,13),
            (4,12,14,6),(6,14,17,9),
            (2,10,11,3),(3,11,12,4),
            (7,8,16,15),(8,9,17,16)]


# Physics setup to Bone
# =================================================================================================
class ANIME_POSE_TOOLS_OT_create_collision_mesh(bpy.types.Operator):
    bl_idname = "anime_pose_tools.create_collision_mesh"
    bl_label = "Create Collision Mesh"

    # execute
    def execute(self, context):
        # 対象ボーンの回収
        armature = bpy.context.view_layer.objects.active
        selected_pose_bones = bpy.context.selected_pose_bones[:]

        # 対象ボーンの中央にBoxを配置
        objs = []
        for pose_bone in selected_pose_bones:
            vec = pose_bone.tail - pose_bone.head
            col_width = vec.length * context.scene.collision_box_width
            col_height = vec.length * context.scene.collision_box_height
            box_center = armature.matrix_world @ ((pose_bone.head + pose_bone.tail) * 0.5)

            # 登録先コレクション取得
            if context.scene.work_collection == None or len(context.scene.work_collection) == 0:  # からの場合はデフォルトで再設定
                context.scene.work_collection = BonePhysicsUtil.DEFAULT_WORK_COLLECTION
            collection = bpy.data.collections.get(context.scene.work_collection)
            if collection == None:
                collection = bpy.data.collections.new(context.scene.work_collection)
                bpy.context.scene.collection.children.link(collection)

            # Box作成
            # ---------------------------------------------
            # メッシュの頂点を変換して作成
            mesh = bpy.data.meshes.new("BoxMesh")
            rot_matrix = armature.matrix_world.to_3x3() @ pose_bone.matrix.to_3x3()  # 回転だけ反映

            # まずはBoxのサイズ調整
            tmp_verts = [Vector([v[0]*col_width, v[1]*col_height, v[2]*col_width]) for v in BOX_VERTS]
            box_verts = [(rot_matrix @ v).xyz for v in tmp_verts]  # ボーンの向きで傾ける
            # 上下中央はhead/tailの位置まで伸ばす
            box_verts[0] = (armature.matrix_world @ pose_bone.head) - box_center
            box_verts[1] = (armature.matrix_world @ pose_bone.tail) - box_center

            # Box作成
            mesh.from_pydata(box_verts, [], BOX_FACES)
            mesh.update(calc_edges=True)

            # オブジェクトにしてコレクションに登録
            obj = bpy.data.objects.new(BonePhysicsUtil.COLLISION_BOX_PREFIX + pose_bone.name, mesh)
            obj.location = box_center
            collection.objects.link(obj)

            objs.append(obj)

        # １つも対象がなかったら終了
        if len(objs) == 0:
            return{'FINISHED'}

        # メッシュをまとめる
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            obj.select_set(True)
        bpy.ops.object.join()


        # 頂点のマージ(Clothの場合必須)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles(threshold=BonePhysicsUtil.MESH_MARGE_THRESHOLD)
        bpy.ops.object.mode_set(mode='OBJECT')

        # オブジェクトに対する設定
        bpy.ops.object.transform_apply()
        bpy.context.object.hide_render = True

        # モディファイア(Cloth)設定
        bpy.context.view_layer.objects.active.vertex_groups.new(name="Pin")
        bpy.ops.object.modifier_add(type='CLOTH')
        modifier = bpy.context.object.modifiers["Cloth"]
        modifier.settings.vertex_group_mass = "Pin"
        modifier.point_cache.use_disk_cache = True
        modifier.point_cache.use_library_path = False
        
        # ウェイトの設定
        self.set_weight(bpy.context.view_layer.objects.active, armature, selected_pose_bones)
        bpy.context.view_layer.objects.active.vertex_groups.active_index = 0  # Pinを選択しなおす

        # POSEモードに戻しておく
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')

        return{'FINISHED'}

    def set_weight(self, obj, armature, selected_pose_bones):
        for pose_bone in selected_pose_bones:
            # 頂点ウェイトの作成
            vg = obj.vertex_groups.new(name=pose_bone.bone.name)

            # ボーンの先端に近い頂点を探してウェイトを1に
            pos = armature.matrix_world @ pose_bone.tail
            v = self.find_nearest_vertex(obj, pos)
            if v != None:
                vg.add([v.index], 1, "ADD")

    # objの持つ頂点の中でposに一番近い頂点を探す
    def find_nearest_vertex(self, obj, pos):
        nearlest_vert = None
        nearlest_len = 1
        for v in obj.data.vertices:
            length = (v.co - pos).length
            if length < nearlest_len:
                nearlest_vert = v
                nearlest_len = length
        return nearlest_vert


# Remove Physics Setup
# =================================================================================================
class ANIME_POSE_TOOLS_OT_remove_mesh(bpy.types.Operator):
    bl_idname = "anime_pose_tools.remove_mesh"
    bl_label = "Remove Mesh In Work"

    # execute
    def execute(self, context):
        # 作業対象コレクションがない
        collection = bpy.data.collections.get(context.scene.work_collection)
        if collection == None:
            return{'FINISHED'}

        for obj in bpy.data.objects:
            # 削除するのはWork下だけ
            if collection.objects.get(obj.name) != None:
                # COLLISION_BOXの削除
                if obj.name.startswith(BonePhysicsUtil.COLLISION_BOX_PREFIX):
                        bpy.data.objects.remove(obj)

        return{'FINISHED'}


# IK Setup
# =================================================================================================
class ANIME_POSE_TOOLS_OT_ik_setup(bpy.types.Operator):
    bl_idname = "anime_pose_tools.ik_setup"
    bl_label = "IK Setup"

    # execute
    def execute(self, context):
        # ターゲットメッシュ未選択
        if context.scene.ik_target_mesh == None:
            self.report({'ERROR'}, "Target mesh is not set.")
            return {'CANCELLED'}

        # 二重登録しないように
        for pose_bone in bpy.context.selected_pose_bones:
            for const in pose_bone.constraints:
                if const.name.startswith(BonePhysicsUtil.BONE_IK_PREFIX):
                    pose_bone.constraints.remove(const)

        # IK追加
        for pose_bone in bpy.context.selected_pose_bones:
            const = pose_bone.constraints.new('IK')
            const.name = BonePhysicsUtil.BONE_IK_PREFIX
            const.target = context.scene.ik_target_mesh
            const.subtarget = pose_bone.bone.name
            const.chain_count = 1

        return{'FINISHED'}


# IK Remove
# =================================================================================================
class ANIME_POSE_TOOLS_OT_ik_remove(bpy.types.Operator):
    bl_idname = "anime_pose_tools.ik_remove"
    bl_label = "IK Remove"

    # execute
    def execute(self, context):
        # 名前で判断して削除
        for pose_bone in bpy.context.selected_pose_bones:
            for const in pose_bone.constraints:
                if const.name.startswith(BonePhysicsUtil.BONE_IK_PREFIX):
                    pose_bone.constraints.remove(const)

        return{'FINISHED'}


# UI描画設定
# =================================================================================================
label = "Setup"
classes = [
    ANIME_POSE_TOOLS_OT_create_collision_mesh,
    ANIME_POSE_TOOLS_OT_remove_mesh,
    ANIME_POSE_TOOLS_OT_ik_setup,
    ANIME_POSE_TOOLS_OT_ik_remove,
]

def draw(parent, context, layout):
    if context.mode == "POSE":
        layout.enabled == False
    box = layout.box()
    box.prop(context.scene, "work_collection", text="Work Collection", slider=True)

    mesh = box.box()
    mesh.prop(context.scene, "collision_box_width", text="Collision Width", slider=True)
    mesh.prop(context.scene, "collision_box_height", text="Collision Height", slider=True)
    mesh_op = mesh.row()
    mesh_op.operator("anime_pose_tools.create_collision_mesh")
    mesh_op.operator("anime_pose_tools.remove_mesh")

    ik = box.box()
    ik.prop(context.scene, "ik_target_mesh", text="IK Target Mesh")
    ik_op = ik.row()
    ik_op.operator("anime_pose_tools.ik_setup")
    ik_op.operator("anime_pose_tools.ik_remove")


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
