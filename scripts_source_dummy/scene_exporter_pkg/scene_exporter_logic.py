"""
Experimental scene exporter with option to export to point clouds.
By Laura Koekoek - laurakoekoek91@gmail.com - http://www.laurakart.fi

ExportLogic class handles the logic for scene exporter
"""

import os
import shutil
import json
import re
import maya.OpenMaya as om
import maya.OpenMayaUI as omu
import maya.cmds as cmds
import pymel.core as pm
import scene_exporter_point_cloud


class Validation():
    @staticmethod
    def validate_strings(scene_name):
        """
        Simple validation for string names including scene name and obj names
        Args:
            scene_name: Name of the scene
        Returns: true if validation is ok, number of incorrect strings
        """
        validation_pass = True
        validation_amount = 0

        all_objs = cmds.ls(dagObjects=True)  # get all scene objects
        regex = re.compile(r'[^a-zA-Z0-9_-]')  # set regex

        if regex.search(scene_name) is not None:  # if scene name string fails the test
            validation_pass = False
            validation_amount += 1

        for o in all_objs:  # for all scene objects
            if regex.search(o) is not None:  # if string fails the test
                validation_pass = False
                validation_amount += 1
        return validation_pass, validation_amount

    @staticmethod
    def clean_strings(scene_name):
        """
        Clean the object names and scene name from special characters
        Args:
            scene_name: name of the scene
        Returns: log string
        """
        re_string = r'[^a-zA-Z0-9_-]' # set regexp for accepted characters
        # clean scene name
        re.sub(re_string, "_", scene_name)

        log = ""
        all_objs = cmds.ls(dagObjects=True)
        regex = re.compile(re_string)

        for o in all_objs:
            if regex.search(o) != None:
                # clean object name
                clean_obj_name = re.sub(re_string, "_", o)
                cmds.rename(o, clean_obj_name)
                log += "\nChanged name of " + o + " to " + clean_obj_name
        return log

    @staticmethod
    def validate_folder(folder):
        """
        Check that assets folder is valid
        Args:
            folder: folder to check
        Returns:
            if folder passes the test, return true, otherwise return false
            error message
        """
        # is it a directory?
        is_dir = os.path.isdir(folder) # check if path is a directory
        errormsg = ""
        if not is_dir:
            errormsg = "\"" + folder + "\" is not a directory."
            return False, errormsg
        # check if folder name is correct
        last_folder = str(folder).split("/")[-1]
        if last_folder != "assets":
            errormsg = "Current folder is not called assets."
            return False, errormsg
        else:
            # check if folder has a mayaconfig file
            if not os.path.isfile(folder + "/.mayaconfig"):
                errormsg = ".mayaconfig file not found."
                return False, errormsg
        return True, errormsg

class ExtraFile():
    @staticmethod
    def generate_occlusion_extra_data(config, log):
        """
        Placeholder for missing occlusion feature in engine.
        append baked occlusion animation based on objects visible to camera.
        Args:
            config: configuration object
            log: log string
        Returns:
            json list of keyframes + objects occluded
            log string
        """
        data = {}
        if not config.export_animation:
            log += "Animation export disabled - ignoring baked occlusion generation."
            return data, log

        # get active viewport camera
        try:
            original_look_thru = cmds.lookThru(q=True)
        except Exception as e:
            log += "Active view not found. Skipping occlusion data."
            return data, log
        # set camera to look through
        cmds.lookThru(config.active_camera)

        data['CullAnimations'] = []
        mask = om.MSelectionMask()
        mask.setMask(om.MSelectionMask.kSelectMeshes)
        om.MGlobal.setObjectSelectionMask(mask)
        # go through frames
        for x in range(int(config.animation_range_min), int(config.animation_range_max)):
            cmds.select(clear=True) # clear the selection
            cmds.currentTime(x)  # go to frame
            frame_num_arr = [x] # set frame number - needs to be in this format for engine
            view = omu.M3dView.active3dView() # select the objects visible to camera
            om.MGlobal.selectFromScreen(0, 0, view.portWidth(), view.portHeight(), om.MGlobal.kReplaceList)
            visible_objs = cmds.ls(selection=True, exactType="transform")

            # Append visible objects
            data['CullAnimations'].append({
                'Visible': True,
                'Keys': frame_num_arr,
                'Objects': visible_objs
            })
            # Select all objs
            cmds.select(all=True, tgl=True ,allDagObjects=True)
            all_objs = cmds.ls(selection=True, exactType="transform")
            # append json
            data['CullAnimations'].append({
                'Visible': False,
                'Keys': frame_num_arr,
                'Objects': all_objs
            })

        # return camera view back to original
        cmds.lookThru(original_look_thru)
        return data, log

    @staticmethod
    def generate_light_extra_data():
        """
        append light info to json dictionary
        Returns: json dictionary with light info appended
        """
        data = {}
        data['Lights'] = []
        light_objs = cmds.ls(type="light") # get lights in scene
        for light in light_objs:
            light_rgb = cmds.pointLight(light, q=True, rgb=True)  # TODO - Add support for other light types
            light_intensity = cmds.pointLight(light, q=True, intensity=True)
            data['Lights'].append({
                'Light': light,
                'Color': light_rgb,
                'Intensity': light_intensity
            })
        return data

    @staticmethod
    def generate_skybox_extra_data(new_skybox_paths):
        """
        Append skybox info to json dictionary
        Args:
            new_skybox_paths: skybox paths in an array
        Returns: json dictionary with skybox data appended
        """
        data = {}
        data['Skybox'] = []
        data['Skybox'].append({
            'Env': new_skybox_paths[0],
            'Radiance': new_skybox_paths[1],
            'Irradiance': new_skybox_paths[2]
            })
        return data

    def generate_extra_file_dict(self, config, new_skybox_paths):
        """
        Get occlusion, lights, and skybox dictionaries for extra file
        Returns: Combined json dictionary data
        Args:
            config: Configuration object
            new_skybox_paths: paths to new skyboxes in an array

        Returns:
            json string for extra file
            log string
        """
        data = {}
        log = "Generating extra file.. "
        # append animated occlusion culling
        if config.occlusion:
            occlusion_data, occlusion_log = self.generate_occlusion_extra_data(config, log)
            data.update(occlusion_data)
            log += occlusion_log
        # append lights
        if config.lights:
            data.update(self.generate_light_extra_data())
        # special mats TODO - add special material support

        # append skybox path
        if config.skybox:
            data.update(self.generate_skybox_extra_data(new_skybox_paths))
        return data, log

    @staticmethod
    def write_extra_file(main_data, point_cloud_data, config):
        """
        Write extra file to disk
        Args:
            main_data: Initial data collected before scene conversion
            point_cloud_data:  data collected at pointcloud conversion
            config: configuration object
        Returns: log string
        """
        log = "Writing extra file to disk..."
        extra_file = config.folder_path + "/scene/" + config.scene_name + ".extra"
        try:
            main_data.update(point_cloud_data)
        except:
            log += "\nCould not add point cloud data."
            return log
        # write to json
        with open(extra_file, 'w') as outfile:
            json.dump(main_data, outfile, indent=4)
        return log

class Textures():
    @staticmethod
    def collect_textures(config):
        """
        Get all mats and textures in scene, collect textures into asset folder and change texture paths in maya file
        Args:
            config: configuration object
        Returns: log string
        """
        log = "Collecting textures.."
        if not config.copy_textures:  # if texture export is not selected, skip the function
            return log

        selected_shapes = cmds.ls(dag=1, o=1, s=1, sl=1)
        for shape in selected_shapes:
            all_texture_slots = []
            all_texture_files = []
            # get materials and textures
            shading_grps = cmds.listConnections(shape, type='shadingEngine')
            material = cmds.ls(cmds.listConnections(shading_grps), materials=1) # warning printed here if no mats found
            if len(material) < 1:  # skip if no material found
                continue
            all_source_textures = cmds.listConnections(material[0], type='file', connections=True)

            if all_source_textures is None:  # check if mat type is none
                continue
            num = 0
            for tex in all_source_textures:
                if (num % 2) == 0:  # even number
                    # this is a material slot
                    temp = str(tex).split(".")
                    all_texture_slots.append(temp[-1])
                else:
                    all_texture_files.append(tex)
                num += 1

            # all files
            texture_files = []  # array for all textures
            for texture_file in all_texture_files:
                current_file = cmds.getAttr("%s.fileTextureName" % texture_file)
                texture_files.append(current_file)

            # create folder for mat
            mat_folder = config.folder_path + "/textures/" + material[0]
            mat_folder_exists = os.path.isdir(mat_folder)
            if not mat_folder_exists:
                try:
                    os.mkdir(mat_folder)
                except Exception as e:
                    log += "\nCouldn't create " + str(mat_folder) + ", " + str(e)
                    continue

            i = 0
            for tex_path in texture_files:
                tex_path_short = str(tex_path).split("/assets")[0] + "/assets"  # TODO this is weird
                if config.folder_path == tex_path_short:
                    log += "\nfile is already in folder"  # TODO path will not be correct for the file anyway
                    continue
                # get name of file without path
                tex_file_short = str(tex_path).split("/")[-1]
                # copy textures
                dst_path = config.folder_path + "/textures/" + str(material[0])
                shutil.copy(tex_path, dst_path)
                new_tex_path = dst_path + "/" + tex_file_short
                log += "\nCopied texture to " + new_tex_path
                if config.keep_mat_paths:  # if keep old paths is set to true
                    return log
                # update paths to materials
                cmds.setAttr("%s.fileTextureName" % all_texture_files[i], new_tex_path, type="string")
                i += 1
        return log

    @staticmethod
    def copy_skybox(config):
        """
        Copies skybox to the assets folder
        Args:
            config: Configuration object
        Returns:
            new_skybox_paths: new skybox paths in an array
            log string
        """
        log = ""
        new_sky_env_path = new_sky_rad_path = new_sky_irrad_path = ""

        if not config.skybox:
            new_skybox_paths = [new_sky_env_path, new_sky_rad_path, new_sky_irrad_path]
            return new_skybox_paths, log
        skyboxes = {"env": config.skybox_env_path, "radiance": config.skybox_radiance_path, "irradiance": config.skybox_irradiance_path}
        for type, skybox in skyboxes.items():
            if os.path.isfile(skybox):  # if skybox file exists, copy it to skybox folder
                new_path = "skybox/" + str(skybox).split("/")[-1]
                shutil.copy(skybox, config.folder_path + "/skybox/")
                log += "\nExported " + type + " skybox to " + skybox

                if type == "env":
                    new_sky_env_path = new_path
                elif type == "radiance":
                    new_sky_rad_path = new_path
                elif type == "irradiance":
                    new_sky_irrad_path = new_path
            else:
                log += "\n" + type + " skybox not exported."
                continue
        new_skybox_paths = [new_sky_env_path, new_sky_rad_path, new_sky_irrad_path]
        return new_skybox_paths, log

class SceneExport():
    def create_point_cloud(self, selection, config):
        """
        Function to call to scene_exporter_point_cloud.py. Generates point cloud and exports the fbx files.
        Args:
            selection: Object selection
            config: configuration object
        Returns: Dictionary with point cloud data
        """
        pc = scene_exporter_point_cloud.PointCloudExport()
        # add attributes to meshes and export instances
        pointcloud_dict = pc.set_attrs(config.folder_path, ".fbx", "meshes")
        self.save_maya_file("_pc_attrs", config)  # meshes but with attributes
        pc.del_shapes()  # delete shape objects
        pc.save_point_cloud_scene(config.folder_path, config.scene_name, ".fbx", True, "scene", selection,
                                  config.export_all)
        self.save_maya_file("_pointcloud", config)

        return pointcloud_dict

    @staticmethod
    def create_single_fbx(config):
        """
        Create a single FBX file from the maya scene.
        Args:
            config: Configuration object
        """
        if config.export_all:
            cmds.select(all=True)
        # export fbx
        file_path = config.folder_path + "/scene/" + config.scene_name + "_fbxscene.fbx"
        cmds.FBXExportEmbeddedTextures('-v', False)
        if config.export_animation:
            cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 1)
        else:
            cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 0)
        pm.mel.FBXExport(f=file_path)

    def export_scene(self, selection, config):
        """
        Export the scene to either point cloud or single fbx
        Args:
            selection: Selected objects
            config: Configuration object
        Returns: Dictionary with point cloud data
        """

        cmds.select(selection)
        if config.exportmode: # if point cloud - export_point_cloud
            log = "Converting the scene into a point cloud... "
            point_cloud_dict = self.create_point_cloud(selection, config)
        else: # if fbx - export fbx
            log = "Exporting the scene to a single fbx file... "
            point_cloud_dict = {}
            self.create_single_fbx(config)
        return point_cloud_dict, log

    @staticmethod
    def save_maya_file(suffix, config):
        """
        Save maya file into asset root with a suffix
        Args:
            suffix: suffix to add to filename
            config: Configuration object
        Returns: path to generated maya file
        """
        save_maya_path = config.folder_path + "/" + config.scene_name + suffix + ".ma"
        cmds.file(rename= save_maya_path)
        cmds.file(save=True, force=True)
        return save_maya_path

# Handles the logic part of the exporter
class Utility():
    @staticmethod
    def set_selection(export_all):
        """
        Get object selection from maya
        Args:
            export_all:  Boolean whether export all is enabled
        Returns: object selection
        """
        if export_all: # if export all is enabled
            cmds.select(all=True) # select all objects
        else:
            selection = cmds.ls(selection=True)
            if len(selection) < 1: # if no objects are selected
                raise Exception("No objects selected.")
        selection = cmds.ls(selection=True)
        return selection

    @staticmethod
    def get_camera_list():
        """
        get list of the scene cameras
        Returns: list of perspective cameras
        """
        persp_cameras = cmds.listCameras(p=True) # list all cameras in the scene
        return persp_cameras

    @staticmethod
    def get_animation_range():
        """
        Get scene animation start/end time from playback time
        Returns:
            min time
            max time
        """
        anim_time_min = cmds.playbackOptions(query=True, min=True)
        anim_time_max = cmds.playbackOptions(query=True, max=True)
        return anim_time_min, anim_time_max

    @staticmethod
    def copy_default_assets(default_assets_folder, target_folder):
        """
        Copy default assets ( + assets folder itself) into the assets folder.
        Args:
            default_assets_folder: Path to default assets folder
            target_folder: Path to target folder
        Returns:
            Path to new assets folder root
            log string
        """
        log = "Copying default assets..."
        assets_folder = target_folder + "/assets"
        try:
            shutil.copytree(default_assets_folder, assets_folder)
            log += ("\nCreated new folder from " + default_assets_folder)
            return assets_folder, log
        except Exception as e:
            log += "\nCouldn't create default assets folder: " + str(e)
            return assets_folder, log

    @staticmethod
    def export_log(log, out_folder):
        """
        Write log to disk
        Args:
            log: log string array
            out_folder: folder to output to
        """
        log_string = ""
        for item in log:
            log_string += "\n" + item

        print log_string
        f = open(out_folder + "/export_log", "w+")
        f.write(log_string)