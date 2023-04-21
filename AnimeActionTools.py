import bpy

# Main UI
# ===========================================================================================
# 3DView Tools Panel
class ANIME_ACTION_TOOLS_PT_ui(bpy.types.Panel):
    bl_label = "Anime Action Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AHT"
    bl_idname = "APT_ACTION_PT_UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass

