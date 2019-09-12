'''
Simple unit test for scene_exporter, to be used in Houdini project.
TODO: Use unittest instead!
'''

import os
import json
import glob
import unittest
import logging
import sys

class MyTest(unittest.TestCase):

    config = "herp"
    folder = "derp"
    print "config: " + config
    def setUp(self):

        """
        Init function
        """
        # load the config file
        print "self.config: " + self.config
        try:
            with open(self.config) as json_file:
                data = json.load(json_file)
                for c in data['config']:
                    # TODO: check that these vars make sense
                    self.asset_path = c['assets_path']
                    self.scene_name = c['scene_name']
                    self.export_all = c['export_all']
                    self.export_animation = c['export_animation']
                    self.anim_range_min = c['animation_range_min']
                    self.anim_range_max = c['animation_range_max']
                    self.copy_textures = c['copy_textures']
                    self.keep_mat_paths = c['keep_mat_paths']
                    self.export_mode = c['pointcloud_mode']
                    self.extra_ptcloud = c['extra_pointcloud']
                    self.extra_occlusion = c['extra_culling']
                    self.active_camera = c['active_camera']
                    self.extra_lights = c['extra_lights']
                    self.extra_special_mats = c['extra_mats']
                    self.skybox = c['skybox_check']
                    self.skybox_path = c['skybox_path']
            print "config file loaded."
        except:
            raise Exception("Failed to load config at " + self.config)

    def test_maya(self):
        """
        Test if maya config file exists
        Returns: true if test passed
        """
        test_pass = False
        # check if .mayaconfig file exists
        if os.path.isfile(self.folder + "/.mayaconfig"):
            test_pass = True
        self.assertEqual(test_pass, True)

    def runTest(self):
        self.assertEqual(True, True)

    def test_textures(self):
        """
        Test for texture creation
        Returns: true if test passed
        """
        test_pass = False
        if not self.copy_textures:
            # if config is disabled, skip
            return True
        # check if any file is copied into the textures folder
        textures = glob.glob(self.folder + "/textures/*/*" + ".*")
        if len(textures) > 0:
            test_pass = True
        self.assertEqual(test_pass, True)

    def test_scenefile(self):
        """
        Test if scenefile extists
        Returns: true if test passed
        """
        test_pass = False
        if self.export_mode:
            # point cloud mode
            if os.path.isfile(self.folder + "/scene/" + self.scene_name + "_pointcloud.fbx"):
                test_pass = True
        if not self.export_mode:
            # fbx mode
            if os.path.isfile(self.folder + "/scene/" + self.scene_name + "_fbxscene.fbx"): # KESKEN
                test_pass = True
        self.assertEqual(test_pass, True)

    def test_extre(self):
        """
        Test if extrafile is generated
        Returns: true if test passed
        """
        test_pass = False
        # check if any of the extra options are true
        if any([self.extra_lights, self.extra_occlusion, self.extra_ptcloud, self.extra_special_mats]):
            # check if extra file exists
            if os.path.isfile(self.folder + "/scene/" + self.scene_name + ".extra"):
                test_pass = True
        self.assertEqual(test_pass, True)


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
unittest.TextTestRunner().run(MyTest())
