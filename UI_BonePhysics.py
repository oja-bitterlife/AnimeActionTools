import bpy
from .BonePhysics import BonePhysicsSwitch, BonePhysicsSetup

modules = [
    BonePhysicsSetup,
    BonePhysicsSwitch
]

# UI描画設定
# =================================================================================================
class ANIME_POSE_TOOLS_PT_bone_physics(bpy.types.Panel):
    bl_label = "Bone Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "AHT_ACTION_PT_UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        for i, module in enumerate(modules):
            if hasattr(module, "draw"):
                if hasattr(module, "label"):
                    self.layout.label(text=module.label)
                module.draw(self, context, self.layout.box())

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
