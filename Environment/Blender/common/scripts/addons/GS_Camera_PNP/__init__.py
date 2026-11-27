#
#  Copyright (C) 2024 Roger Torm
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

bl_info = {
    "name": "Perspective-n-Point",
    "author": "Roger Torm",
    "license": "GPL",
    "version": (0, 0, 7),
    "blender": (3, 0, 0),
    "location": "Clip Editor > Tools > Solve > Solve PnP",
    "doc_url": "https://github.com/RT-studios/camera-pnpoint",
    "description": "PnP solver. Requires OpenCV.",
    "category": "Camera",
}

import bpy
import os
import sys
import importlib

# Offline OpenCV: the studio installs it into the workstation's Python 3.9, since Blender can't pip install
# without internet. USERPROFILE, not USERNAME: the profile folder can be "<user>.<DOMAIN>".
opencv_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Programs", "Python", "Python39",
                           "Lib", "site-packages")
dependencies_installed = False


def import_opencv():
    if opencv_path not in sys.path:
        sys.path.insert(0, opencv_path)
    importlib.import_module("cv2")


class CAMPNP_OT_pose_camera(bpy.types.Operator):
    bl_idname = "campnp.solvepnp"
    bl_label = "Solve camera extrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera extrinsics using available markers and 3D points"

    def execute(self, context):
        if context.object and context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
        #call solver
        sceneinfo = getsceneinfo(self, context)
        if sceneinfo == {'CANCELLED'}:
            return {'CANCELLED'}
        return solvepnp(*sceneinfo)

class CAMPNP_OT_calibrate_camera(bpy.types.Operator):
    bl_idname = "campnp.camcalib"
    bl_label = "Solve camera intrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera intrinsics using available markers and 3D points"

    def execute(self, context):
        if context.object and context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
        #call solver
        sceneinfo = getsceneinfo(self, context)
        if sceneinfo == {'CANCELLED'}:
            return {'CANCELLED'}
        return camcalib(*sceneinfo)


class CAMPNP_PT_pnp_panel(bpy.types.Panel):    # panel class
    bl_label = "Solve PnP"
    bl_idname = "VIEW3D_PT_PnP_Panel"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Solve"

    @classmethod
    def poll(cls, context):
        return context.space_data.mode == 'TRACKING'

    def draw(self, context):
        layout = self.layout

        col = layout.column(heading="3D Points", align=True)
        col.prop(context.scene, "campnp_points_collection")

        col = layout.column(heading="Calibrate", align=True)
        col.prop(context.scene, "campnp_intrinsics_focal_length", text="Focal Length")
        col.prop(context.scene, "campnp_intrinsics_principal_point", text="Optical Center")
        row = col.row(align=True).split(factor=0.22)
        row.prop(context.scene, "campnp_intrinsics_distortion_k1", text="K1")
        row = row.row(align=True).split(factor=0.3)
        row.prop(context.scene, "campnp_intrinsics_distortion_k2", text="K2")
        row.prop(context.scene, "campnp_intrinsics_distortion_k3", text="K3 Distortion")

        col = layout.column(align=True)
        col.operator("campnp.camcalib", text="Calibrate Camera")

        col = layout.column(align=True)
        col.operator("campnp.solvepnp", text="Solve Camera Pose")
        col.scale_y = 2.0

        col = layout.column(align=True)
        col.label(text=context.scene.campnp_msg)

# Main Class registration list
class_list = (CAMPNP_OT_calibrate_camera,
              CAMPNP_OT_pose_camera,
              CAMPNP_PT_pnp_panel,)


class CAMPNP_preferences(bpy.types.AddonPreferences):
    bl_label = "Dependencies"
    bl_idname = __name__

    def draw(self, context):
        col = self.layout.column()
        if not dependencies_installed:
            col.label(text="Dependency Status: OpenCV not found.")
            col.label(text="Expected in: %s" % opencv_path)
        else:
            col.label(text="Dependency Status: OpenCV is installed.")

# Preference class registration list
prefclass_list = (CAMPNP_preferences,)


def register():

    bpy.types.Scene.campnp_points_collection = bpy.props.PointerProperty(
        name = "",
        type = bpy.types.Collection)
    bpy.types.Scene.campnp_intrinsics_focal_length = bpy.props.BoolProperty(
        name="Focal Length",
        description="Calibrate Focal Length",
        default = True)
    bpy.types.Scene.campnp_intrinsics_principal_point = bpy.props.BoolProperty(
        name="Optical Center",
        description="Calibrate Optical Center",
        default = False)
    bpy.types.Scene.campnp_intrinsics_distortion_k1 = bpy.props.BoolProperty(
        name="Distortion K1",
        description="Calibrate Radial Distortion K1",
        default = False)
    bpy.types.Scene.campnp_intrinsics_distortion_k2 = bpy.props.BoolProperty(
        name="Distortion K2",
        description="Calibrate Radial Distortion K2",
        default = False)
    bpy.types.Scene.campnp_intrinsics_distortion_k3 = bpy.props.BoolProperty(
        name="Distortion K3",
        description="Calibrate Radial Distortion K3",
        default = False)
    bpy.types.Scene.campnp_msg = bpy.props.StringProperty(
        name="Information",
        description="Solver Output Message")

    global dependencies_installed
    dependencies_installed = False

    for cls in prefclass_list:
        bpy.utils.register_class(cls)

    try:
        import_opencv()
        dependencies_installed = True
    except ImportError as err:
        print("Perspective-n-Point: OpenCV not found in %s (%s)" % (opencv_path, err))
        return

    # if opencv is installed, load the rest of the modules
    campnp = importlib.import_module(__name__ + ".campnp")
    globals()["getsceneinfo"] = getattr(campnp, "getsceneinfo")
    globals()["solvepnp"] = getattr(campnp, "solvepnp")
    globals()["camcalib"] = getattr(campnp, "camcalib")

    for cls in class_list:
        bpy.utils.register_class(cls)

def unregister():
    if dependencies_installed:
        for cls in reversed(class_list):
            bpy.utils.unregister_class(cls)

    for cls in reversed(prefclass_list):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.campnp_msg
    del bpy.types.Scene.campnp_intrinsics_distortion_k3
    del bpy.types.Scene.campnp_intrinsics_distortion_k2
    del bpy.types.Scene.campnp_intrinsics_distortion_k1
    del bpy.types.Scene.campnp_intrinsics_principal_point
    del bpy.types.Scene.campnp_intrinsics_focal_length
    del bpy.types.Scene.campnp_points_collection

if __name__ == "__main__":
    register()
