# Defines
# =================================================================================================
DEFAULT_WORK_COLLECTION = "APT_Work"
COLLISION_BOX_PREFIX = "APT_ColBox@"
BONE_IK_PREFIX = "APT_IK"

MESH_MARGE_THRESHOLD = 0.0005  # 通常のWeldの半分で、CleanUpの5倍


# Utility Methods
# =================================================================================================
# boneが含まれているレイヤーがArmatureの表示レイヤーになっているかどうか
def is_layer_enable(armature, edit_bone):
    for i, b in enumerate(edit_bone.layers):
        if b:
            return armature.data.layers[i]
    return False

# OBJECTモード中で頂点選択を外す
def deselect_vertex_in_object_mode(obj):
    for polygon in obj.data.polygons:
        polygon.select = False
    for edge in obj.data.edges:
        edge.select = False
    for vertex in obj.data.vertices:
        vertex.select = False