#
#  Copyright (C) 2022 Roger Torm
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

import bpy
import cv2 as cv
import numpy as np
from mathutils import Matrix, Vector


# getsceneinfo collects information from the movie clip and its camera, 
# as well as 2D points and 3D points from the chosen collection
def getsceneinfo(self, context):
    # get currently loaded movieclip or image
    clip = context.area.spaces.active.clip
    if not clip:
        self.report({'ERROR'}, 'Please load an image in the clip editor')
        return {'CANCELLED'}

    # get picture and camera metrics
    size = clip.size
    clipcam = clip.tracking.camera
    focal = clipcam.focal_length_pixels # 
    if bpy.app.version < (3, 5, 0):
        optcent = clipcam.principal
    else:
        optcent = clipcam.principal_point_pixels
    # take radial distortion parameters: 
    if clipcam.distortion_model == 'POLYNOMIAL':
        k1, k2, k3 = clipcam.k1, clipcam.k2, clipcam.k3
    elif clipcam.distortion_model == 'BROWN':
        k1, k2, k3 = clipcam.brown_k1, clipcam.brown_k2, clipcam.brown_k3
    else:
        k1, k2, k3 = 0.0, 0.0, 0.0
        self.report({'WARNING'}, 'Current distortion model is not supported, use Polynomial instead.')

    # get current frame to retrieve marker locations
    fr = context.scene.frame_current

    # get list of tracks and retrieve marker positions at current frame
    points2d = []
    tracks = clip.tracking.tracks
    if not tracks:
        self.report({'ERROR'}, 'Please add markers on the image as 2D points')
        return {'CANCELLED'}
        l2d = 0
    else:
        for track in sorted(tracks, key = lambda o: o.name):
            marker = track.markers.find_frame(fr)
            if not marker:
                self.report({'ERROR'}, 'Marker for %s not set on current frame' %track.name)
                return {'CANCELLED'}
            else:
                points2d.append([marker.co[0]*size[0], size[1]-marker.co[1]*size[1]])
        points2d = np.asarray(points2d, dtype='double')
        l2d = points2d.shape[0]

    # retrieve 3D points from scene objects
    points3d = []
    col3d = context.scene.campnp_points_collection
    if col3d == None:
        self.report({'ERROR'}, 'Please specify a collection for the 3D points')
        l3d = 0
        return {'CANCELLED'}
    else: 
        for point in sorted(col3d.all_objects, key = lambda o: o.name):
            points3d.append(point.location)
        points3d = np.asarray(points3d, dtype='double')
        l3d = points3d.shape[0]

    # check point list length compatibility
    npoints = l2d
    if l2d > l3d: 
        points2d = points2d[:l3d,:]
        self.report({'WARNING'}, 'Ignoring extra 2D points')
        npoints = l3d
    elif l2d < l3d: 
        points3d = points3d[:l2d,:]
        self.report({'WARNING'}, 'Ignoring extra 3D points')

    # construct camera intrinsics
    camintr = np.array([ [focal, 0, optcent[0]],
                    [0, focal, size[1]-optcent[1]],
                    [0, 0, 1] ], dtype='double')

    # construct distortion vector, only k1,k2,k3 (polynomial or brown models)
    distcoef = np.array([k1, k2, 0, 0, k3])
    
    return self, context, clip, points3d, points2d, camintr, distcoef, size, npoints


# main PnP solver function
def solvepnp(self, context, clip, points3d, points2d, camintr, distcoef, size, npoints):
    if npoints < 4:
        self.report({'ERROR'}, 'Not enough point pairs, use at least 4 pairs to solve a camera pose.')
        return {'CANCELLED'}
    
    # solve Perspective-n-Point
    ret, rvec, tvec, error = cv.solvePnPGeneric( points3d
                                                , points2d
                                                , camintr
                                                , distcoef 
                                                , flags = cv.SOLVEPNP_SQPNP) # TODO: further investigation on other algorithms             
    rmat, _ = cv.Rodrigues(rvec[0])
    if not ret or len(error) > 1:
        self.report({'ERROR'}, "solvePnP failed!")
        return {'CANCELLED'}
    context.scene.campnp_msg = ("Reprojection Error: %.2f" %error) 
    
    # calculate and print projection errors for each point pair
    # this will output to the Console, useful for debugging markers
    points3dproj, _ = cv.projectPoints( points3d, rvec[0], tvec[0], camintr, distcoef)
    print("\nReprojection errors (px):")
    for i in range(npoints):
        pairerror = (  (points3dproj[i][0][0]-points2d[i][0])**2 + 
                   (points3dproj[i][0][1]-points2d[i][1])**2    ) **0.5
        print(clip.tracking.tracks[i].name.ljust(14) + ": %.3f " % pairerror)

    # get R and T matrices
    # https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
    R_world2cv = Matrix(rmat.tolist()) 
    T_world2cv = Vector(tvec[0]) 

    # blender camera to opencv camera coordinate conversion 
    R_bcam2cv = Matrix(
        ((1, 0, 0),
         (0, -1, 0),
         (0, 0, -1)))

    # calculate transform in world coordinates
    R_cv2world = R_world2cv.transposed()
    rot = R_cv2world @ R_bcam2cv
    loc =  -1 * R_cv2world @ T_world2cv

    # Create new camera or use existing
    # check if active object is a camera, if so, assume user wants to set it up, otherwise create a new camera
    if context.active_object == None or context.active_object.type != 'CAMERA': # add a new one
        bpy.ops.object.add(type='CAMERA')
        bpy.context.object.name = clip.name 

    # Set camera intrinsics, extrinsics and background
    cam = context.object
    camd = cam.data
    camd.type = 'PERSP'
    camd.lens = clip.tracking.camera.focal_length
    camd.sensor_width = clip.tracking.camera.sensor_width
    camd.sensor_height = clip.tracking.camera.sensor_width*size[1]/size[0]
    render_size = [context.scene.render.pixel_aspect_x * context.scene.render.resolution_x,
                    context.scene.render.pixel_aspect_y * context.scene.render.resolution_y]
    camd.sensor_fit = 'HORIZONTAL' if render_size[0]/render_size[1] <= size[0]/size[1] else 'VERTICAL'
    refsize = size[0] if render_size[0]/render_size[1] <= size[0]/size[1] else size[1]
    if bpy.app.version < (3, 5, 0):
        camd.shift_x = (size[0]*0.5 - clip.tracking.camera.principal[0])/refsize
        camd.shift_y = (size[1]*0.5 - clip.tracking.camera.principal[1])/refsize
    else:
        camd.shift_x = (size[0]*0.5 - clip.tracking.camera.principal_point_pixels[0])/refsize
        camd.shift_y = (size[1]*0.5 - clip.tracking.camera.principal_point_pixels[1])/refsize
    
    camd.show_background_images = True
    if not camd.background_images: bg = camd.background_images.new()
    else: bg = camd.background_images[0]
    bg.source = 'MOVIE_CLIP'
    bg.clip = clip
    bg.frame_method = 'FIT' 
    bg.display_depth = 'FRONT'
    bg.clip_user.use_render_undistorted = True
    
    cam.matrix_world = Matrix.Translation(loc) @ rot.to_4x4()
    context.scene.camera = cam
    
    return {'FINISHED'}


# main Calibration solver function
def camcalib(self, context, clip, points3d, points2d, camintr, distcoef, size, npoints):   
    if npoints < 6:
        self.report({'ERROR'}, 'Not enough point pairs, use at least 6 pairs to calibrate a camera.')
        return {'CANCELLED'}

    flags = (cv.CALIB_USE_INTRINSIC_GUESS + cv.CALIB_FIX_ASPECT_RATIO + cv.CALIB_ZERO_TANGENT_DIST
            + (cv.CALIB_FIX_PRINCIPAL_POINT if not context.scene.campnp_intrinsics_principal_point else 0)
            + (cv.CALIB_FIX_FOCAL_LENGTH if not context.scene.campnp_intrinsics_focal_length else 0)
            + (cv.CALIB_FIX_K1 if not context.scene.campnp_intrinsics_distortion_k1 else 0)
            + (cv.CALIB_FIX_K2 if not context.scene.campnp_intrinsics_distortion_k2 else 0)
            + (cv.CALIB_FIX_K3 if not context.scene.campnp_intrinsics_distortion_k3 else 0))
    
    ret, camintr, distcoef, _, _ = cv.calibrateCamera(np.asarray([points3d], dtype='float32'), 
                                                    np.asarray([points2d], dtype='float32'), 
                                                    size, 
                                                    camintr, distcoef,
                                                    flags = flags )
                                                    
    context.scene.campnp_msg = ("Reprojection Error: %.2f" %ret)
    
    # set picture and camera metrics
    if context.scene.campnp_intrinsics_focal_length: 
        clip.tracking.camera.focal_length_pixels = camintr[0][0] 
    if context.scene.campnp_intrinsics_principal_point: 
        if bpy.app.version < (3, 5, 0):
            clip.tracking.camera.principal = [camintr[0][2], size[1]-camintr[1][2]]
        else:
            clip.tracking.camera.principal_point_pixels = [camintr[0][2], size[1]-camintr[1][2]]
    if (context.scene.campnp_intrinsics_distortion_k1 or 
        context.scene.campnp_intrinsics_distortion_k2 or 
        context.scene.campnp_intrinsics_distortion_k3): 
        clip.tracking.camera.k1 = distcoef[0]
        clip.tracking.camera.k2 = distcoef[1]
        clip.tracking.camera.k3 = distcoef[4]
        clip.tracking.camera.brown_k1 = distcoef[0]
        clip.tracking.camera.brown_k2 = distcoef[1]
        clip.tracking.camera.brown_k3 = distcoef[4]

    return {'FINISHED'}