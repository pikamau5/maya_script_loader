"""
Experimental scene exporter with option to export to point clouds.
By Laura Koekoek - laurakoekoek91@gmail.com - http://www.laurakart.fi

What it does:
    Create assets folder with default assets
    Collect all scene assets into the folder
    Export scene file to either a point cloud or a single FBX file

    Generate extra file:
        * point cloud info
        * Generate baked occlusion animation (active camera needed)
        * Light info
        * special materials
        * skybox

TODO: use maya's "set folder" without adding all the folders to get relative paths
TODO: Group ui elements in qt creator
TODO: Add a progress bar (see texture checking tool for reference)
TODO: add sentry/some other error tracking
"""

import os
import json
import subprocess
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QFileDialog
from scene_exporter_ui import Ui_Form
import scene_exporter_logic
# from profiler import Profiler


# For running the script without UI
class ExportNoUI:
    """
    For running the script without the UI
    """

    def __init__(self):
        """
        init function
        """
        # create configuration
        self.config = Config()
        # create logic classes
        self.scene_export = scene_exporter_logic.SceneExport()
        self.validation = scene_exporter_logic.Validation()
        self.extrafile = scene_exporter_logic.ExtraFile()
        self.textures = scene_exporter_logic.Textures()
        self.utility = scene_exporter_logic.Utility()

    @staticmethod
    def get_settings(settings_file, assets_folder, config):
        """
        get ui settings (is this needed?) and print out settings to log
        Args:
            settings_file: path to separate settings file)
            assets_folder: custom path to assets folder
            config: configuration object
        Returns: settings in dictionary
        """
        log = "Getting the settings..."
        if os.path.isfile(settings_file): # if settings file is found
            with open(settings_file) as json_file:
                data = json.load(json_file)
                for c in data['config']:
                    if assets_folder != "":
                        assets_folder += "/"
                        config.folder_path = assets_folder
                    else:
                        config.folder_path = (c['assets_path'])
                    config.scene_name = (c['scene_name'])
                    config.export_all = (c['export_all'])
                    config.export_animation = (c['export_animation'])
                    config.animation_range_min = (c['animation_range_min'])
                    config.animation_range_max = (c['animation_range_max'])
                    config.copy_textures = (c['copy_textures'])
                    config.keep_mat_paths = False
                    config.exportmode = (c['pointcloud_mode'])
                    config.ptcloud = (c['extra_pointcloud'])
                    config.occlusion = (c['extra_culling'])
                    config.active_camera = (c['active_camera'])
                    config.lights = (c['extra_lights'])
                    config.special_mats = (c['extra_mats'])
                    config.skybox = (c['skybox_check'])
                    config.skybox_env_path = (c['skybox_path'])
                    config.skybox_radiance_path = ""
                    config.skybox_irradiance_path = ""
            # add config to log
            log += "\nLoaded the following configuration:"
            for config_json in data['config']:
                    for x in config_json:
                        log += "\n" + str(x) + ": " + str(config_json[x])
            log += "\n-------------\n"

        else:
           log += "settings file not found. using default settings."
        return config, log

    def run_export(self, config_file=None, default_assets_folder=None, assets_folder=None):
        """
        Exports the scene without the UI
        Args:
            config_file: path to settings file
            default_assets_folder: Path to default assets folder
            assets_folder: assets folder to export to. must end with /assets. If left empty will use settings file.
        """
        log_out = []
        if None in (config_file, default_assets_folder, assets_folder):
            raise Exception("Missing arguments.")

        config, log = self.get_settings(config_file, assets_folder, self.config)  # Update settings
        log_out.append(log)
        config.folder_path = assets_folder
        root_folder = str(config.folder_path).split("/assets")  # set the root folder
        new_folder, log = self.utility.copy_default_assets(default_assets_folder, root_folder[0])
        log_out.append(log)

        val_pass, val_amount = self.validation.validate_strings(config.scene_name)  # validate scene name and objects
        if not val_pass:
            log = self.validation.clean_strings(config.scene_name)
            log_out.append(log)
        try:
            folder_valid, errormsg = self.validation.validate_folder(config.folder_path)  # validate asset folder path
            if not folder_valid:
                log_out.append(errormsg)
            selection = self.utility.set_selection(config.export_all)  # get current or all selection
            self.scene_export.save_maya_file("_original", config)  # save original maya file
            log = self.textures.collect_textures(config)  # collect textures to assets folder
            log_out.append(log)
            new_skybox_paths, log = self.textures.copy_skybox(config)  # collect skyboxes
            log_out.append(log)
            main_dict, log = self.extrafile.generate_extra_file_dict(config, new_skybox_paths)  # collect data to extra file
            log_out.append(log)
            pc_dict, log = self.scene_export.export_scene(selection, config)  # export scene either as point cloud or fbx
            log_out.append(log)
            log = self.extrafile.write_extra_file(main_dict, pc_dict, config)  # write extra file to disk
            log_out.append(log)
            log_out.append("Export done.")
            self.utility.export_log(log_out, config.folder_path)  # write log to disk

        except Exception as error:
            log_out += str(error)
            self.utility.export_log(log_out, config.folder_path)


# For running the script with UI
class ExportUI(QtWidgets.QWidget, Ui_Form):
    """
    Run the script inside maya with a pyqt ui
    """
    def __init__(self):
        """
        init function
        """
        super(ExportUI, self).__init__(None)
        self._ui = Ui_Form()
        self._ui.setupUi(self)

        # create configuration
        self.config = Config()
        # create logic classes
        self.scene_export = scene_exporter_logic.SceneExport()
        self.validation = scene_exporter_logic.Validation()
        self.extrafile = scene_exporter_logic.ExtraFile()
        self.textures = scene_exporter_logic.Textures()
        self.utility = scene_exporter_logic.Utility()

        # Default assets folder location
        self.default_assets_folder = os.path.dirname(os.path.realpath(__file__)) + "/sceneExporter/defaultassets"

    def setup_ui(self):
        """
        PyQt window and function connection setup. inherits from the UI file.
        """
        form = self
        # get setupui method from generated pyqt file
        super(ExportUI, self).setupUi(form)

        # default ui settings
        self.radio_export_all.setChecked(True)
        self.radio_export_ptcloud.setChecked(True)

        # init some ui elements as false
        self.check_skybox_radiance.setEnabled(False)
        self.textbox_skybox_path.setEnabled(False)
        self.skybox_browse.setEnabled(False)
        self.folder_status.setText("")

        # radiance and irradiance labels
        self.skybox_envpath_label.setEnabled(False)
        self.skybox_radiance_label.setEnabled(False)
        self.skybox_irradiance_label.setEnabled(False)

        self.keep_mat_paths.setEnabled(False)
        self.anim_range_min.setEnabled(False)
        self.anim_range_max.setEnabled(False)
        self.anim_range_label.setEnabled(False)

        self.check_extra_special_mats.setEnabled(False)  # TODO this still needs to be added

        # get initial animation range
        anim_time_min, anim_time_max = self.utility.get_animation_range()
        self.anim_range_min.setValue(anim_time_min)
        self.anim_range_max.setValue(anim_time_max)

        # populate camera dropdown list and disable it by default
        self.active_camera.clear()
        self.active_camera.addItems(self.utility.get_camera_list())
        self.active_camera.setEnabled(False)
        self.active_camera_label.setEnabled(False)

        # connected functions
        self.btn_export.clicked.connect(self.run_export)  # REFERENCES TO LOGIC
        self.browse_asset_path.clicked.connect(self.browse_assets_folder)
        self.skybox_browse.clicked.connect(lambda: self.browse_skybox("env"))
        self.radiance_browse.clicked.connect(lambda: self.browse_skybox("radiance"))
        self.irradiance_browse.clicked.connect(lambda: self.browse_skybox("irradiance"))
        self.check_extra_occlusion.stateChanged.connect(self.enable_occlusion_export_ui)
        self.clear_log.clicked.connect(self.text_log.clear)
        self.check_copy_textures.stateChanged.connect(self.set_mat_path_ui)
        self.check_export_animation.stateChanged.connect(self.set_animation_ui)
        self.check_skybox.stateChanged.connect(self.set_skybox_ui)
        self.check_skybox_radiance.stateChanged.connect(self.set_radiance_ui)

        # Window always on top
        form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def run_export(self):
        """
        Run the export inside the maya UI
        """

        log_out = []
        # Update with settings from the UI
        ui_config, log = self.get_settings(self.config)
        log_out.append(log)
        # validate scene name and objects
        val_pass, val_amount = self.validation.validate_strings(self.config.scene_name)
        if not val_pass:
            log = self.validation.clean_strings(self.config.scene_name)
            log_out.append(log)
        try:
            if ui_config.occlusion:
                # confirm occlusion baking from user
                confirm_occlusion_bake = self.message_query("Occlusion baking", "Baking the occlusion list can take a long time with a large scene. Continue?")
                if not confirm_occlusion_bake:
                    log_out.append("Cancelled.")
                    return
            # validate asset folder path
            folder_valid, errormsg = self.validation.validate_folder(ui_config.folder_path)
            if not folder_valid:
                self.popup_message(errormsg, errormsg)
                return
            # get selection based on config
            selection = self.utility.set_selection(ui_config.export_all)
            # save original maya file
            original_maya_path = self.scene_export.save_maya_file("_original", ui_config)
            # collect textures into assets folder
            log = self.textures.collect_textures(ui_config)
            log_out.append(log)
            # copy skyboxes to folder
            new_skybox_paths, log = self.textures.copy_skybox(ui_config)
            log_out.append(log)
            # create first part of extra file dictionary
            main_dict, log = self.extrafile.generate_extra_file_dict(ui_config, new_skybox_paths)
            log_out.append(log)
            # export the scene files
            pc_dict, log = self.scene_export.export_scene(selection, ui_config)
            log_out.append(log)
            # ask to return to original if point clouds were exported
            if self.config.exportmode:
                load_original_file_query = self.message_query("Point cloud exported", "Load maya file from original state?")
                if load_original_file_query:
                    cmds.file(original_maya_path, o=True, f=True)
            # write the extra file to disk
            log = self.extrafile.write_extra_file(main_dict, pc_dict, ui_config)  # write extra file to disk
            log_out.append(log)
            # save user configuration to disk
            self.save_config(self.config.folder_path)
            # popup when exporting is done
            if self.message_query("Export done", "Scene export done. Open assets folder?"):
                # open the assets folder
                path = os.path.normpath(str(self.config.folder_path))
                subprocess.call("explorer " + path, shell=True)
            log_out.append("Export done.")
            self.utility.export_log(log_out, ui_config.folder_path)

        except Exception as error:
            self.handle_error(str(error))

    def get_settings(self, config):
        """
        Get settings from the UI
        Args:
            config: Configuration object
        Returns: updated config
        """

        config.folder_path = self.asset_path.text()
        config.scene_name = self.scene_name_input.text()
        config.export_all = self.radio_export_all.isChecked()
        # export animation + range
        config.export_animation = self.check_export_animation.isChecked()
        config.animation_range_min = self.anim_range_min.value()
        config.animation_range_max = self.anim_range_max.value()
        # textures
        config.copy_textures = self.check_copy_textures.isChecked()
        config.keep_mat_paths = self.keep_mat_paths.isChecked()
        # point cloud
        config.exportmode = self.radio_export_ptcloud.isChecked()
        # extra file
        config.ptcloud = self.check_extra_ptcloud.isChecked()
        config.occlusion = self.check_extra_occlusion.isChecked()
        config.active_camera = self.active_camera.currentText()
        config.lights = self.check_extra_lights.isChecked()
        config.special_mats = self.check_extra_special_mats.isChecked()
        # Skybox
        config.skybox = self.check_skybox.isChecked()
        config.skybox_env_path = self.textbox_skybox_path.text()
        config.skybox_radiance_path = self.textbox_radiance_path.text()
        config.skybox_irradiance_path = self.textbox_irradiance_path.text()

        # print settings to log
        log = ("Using the following settings to export:" + "\n" +
                          "Folder: " + str(config.folder_path) + "\n" +
                          "Scene name: " + str(config.scene_name) + "\n" +
                          "Export all: " + str(config.export_all) + "\n" +
                          "Export animations: " + str(config.export_animation) + "\n" +
                          "animation range: " + str(config.animation_range_min) + " - "
                          + str(config.animation_range_max) + "\n" +
                          "Copy textures: " + str(config.copy_textures) + "\n" +
                          "Update mat paths: " + str(config.keep_mat_paths) + "\n" +
                          "Extra - occlusion: " + str(config.occlusion) + "\n" +
                          "Active camera: "+ str(config.active_camera) + "\n" +
                          "Extra - lights: " + str(config.lights) + "\n" +
                          "Extra - special materials: " + str(config.special_mats) + "\n" +
                          "Skybox enabled: " + str(config.skybox) + ", skybox env path: " + str(config.skybox_env_path) + "\n" +
                          "Skybox radiance: " + str(config.skybox_radiance_path) + "\n" +
                          "Skybox irradiance: " + str(config.skybox_irradiance_path)
                          + "\n" + "-----------------------")
        self.write_to_log(log)
        return config, log

    def set_radiance_ui(self):
        """
        Change enabled state for skybox path browse
        """
        enabled = False
        if self.check_skybox.isChecked() and self.check_skybox_radiance.isChecked():
            enabled = True
        self.skybox_radiance_label.setEnabled(enabled)
        self.skybox_irradiance_label.setEnabled(enabled)
        self.textbox_radiance_path.setEnabled(enabled)
        self.textbox_irradiance_path.setEnabled(enabled)
        self.radiance_browse.setEnabled(enabled)
        self.irradiance_browse.setEnabled(enabled)

    def set_skybox_ui(self):
        """
        Change enabled state for skybox path browse
        """
        enabled = False
        if self.check_skybox.isChecked():
            enabled = True
        self.skybox_envpath_label.setEnabled(enabled)
        self.textbox_skybox_path.setEnabled(enabled)
        self.skybox_browse.setEnabled(enabled)
        self.check_skybox_radiance.setEnabled(enabled)

    def set_animation_ui(self):
        """
        change enabled state for animation range
        """
        enabled = False
        if self.check_export_animation.isChecked():
            enabled = True
        self.anim_range_min.setEnabled(enabled)
        self.anim_range_max.setEnabled(enabled)
        self.anim_range_label.setEnabled(enabled)

    def set_mat_path_ui(self):
        """
        change enabled state for "Update material paths" checkbox
        """
        if self.check_copy_textures.isChecked():
            self.keep_mat_paths.setEnabled(True)
        else:
            self.keep_mat_paths.setEnabled(False)
            self.keep_mat_paths.setChecked(False)

    def enable_occlusion_export_ui(self):
        """
        Updates the camera dropdown list and enables/disables it
        """
        enabled = False
        if self.check_extra_occlusion.isChecked():  # if occlusion testing checkbox is enabled
            enabled = True
            self.active_camera.clear()  # clear the ui list
            self.active_camera.addItems(self.utility.get_camera_list())  # add updated camera list
        # enable ui items
        self.active_camera.setEnabled(enabled)
        self.active_camera_label.setEnabled(enabled)

        # enable animation checkbox if not enabled.
        if not self.check_export_animation.isChecked() and self.check_extra_occlusion.isChecked():
            self.write_to_log("Enabling animation export, it is needed for the occlusion generation.")
            self.check_export_animation.setChecked(True)

    def browse_skybox(self, skybox_type):
        """
        Browse for skybox path
        Args:
            skybox_type: Is skybox env, radiance or irradiance type
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name = QFileDialog.getOpenFileName(self, "Select Skybox")
        if file_name:
            if skybox_type == "env":
                self.textbox_skybox_path.setText(str(file_name[0]))
            if skybox_type == "radiance":
                self.textbox_radiance_path.setText(str(file_name[0]))
            if skybox_type == "irradiance":
                    self.textbox_irradiance_path.setText(str(file_name[0]))

    def browse_assets_folder(self):
        """
        Browse for asset folder path
        """
        # open folder browse dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        browsed_folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        # if get a file name
        if browsed_folder:
            # check if folder is valid
            is_valid_folder, errormsg = self.validation.validate_folder(browsed_folder)

            if is_valid_folder:
                load_settings_query = self.message_query("Valid folder",
                                                         "Valid asset folder found! load previous settings?")
                if load_settings_query:
                    # load configuration
                    self.load_config(browsed_folder)

            else:
                create_folder_query = self.message_query("Not a valid \"assets\" folder",
                                                         "This is not a valid assets folder. Create new folder here?")
                if not create_folder_query:
                    return
                else:
                    # create assets folder into dir and copy default assets there.
                    browsed_folder, message = self.utility.copy_default_assets(self.default_assets_folder, browsed_folder)
                    self.popup_message(message, message)

        # set folder path to UI
        self.asset_path.setText(browsed_folder) # TODO could be separated

    def load_config(self, folder):
        """
        Load configuration used with previous export in existing assets folder
        Args:
            folder: asset folder path
        """
        config_path = folder + "/.mayaconfig"
        if os.path.isfile(config_path):
            try:
                with open(config_path) as json_file:
                    data = json.load(json_file)
                    for c in data['config']:
                        # TODO: check that these vars make sense
                        self.asset_path.setText(c['assets_path'])
                        self.scene_name_input.setText(c['scene_name'])
                        self.radio_export_all.setChecked(c['export_all'])
                        self.check_export_animation.setChecked(c['export_animation'])
                        self.anim_range_min.setValue(c['animation_range_min'])
                        self.anim_range_max.setValue(c['animation_range_max'])
                        self.check_copy_textures.setChecked(c['copy_textures'])
                        self.keep_mat_paths.setChecked(c['keep_mat_paths'])
                        self.radio_export_ptcloud.setChecked(c['pointcloud_mode'])
                        self.check_extra_ptcloud.setChecked(c['extra_pointcloud'])
                        self.check_extra_occlusion.setChecked(c['extra_culling'])
                        active_cam_index = self.active_camera.findText(c['active_camera'])
                        self.active_camera.setCurrentIndex(active_cam_index)
                        self.check_extra_lights.setChecked(c['extra_lights'])
                        self.check_extra_special_mats.setChecked(c['extra_mats'])
                        self.check_skybox.setChecked(c['skybox_check'])
                        self.textbox_skybox_path.setText(c['skybox_path'])
                self.write_to_log("maya config loaded from " + config_path)
            except Exception as e:
                self.handle_error("Failed to load config: " + str(e))
        else:
            self.handle_error(".mayaconfig not found")

    def save_config(self, folder):
        """
        Save UI configuraton into asset folder
        Args:
            folder: asset folder path
        """
        config_path = folder + "/.mayaconfig"
        data = {}
        data['config'] = []
        data['config'].append({
            'assets_path': self.asset_path.text(),
            'scene_name': self.scene_name_input.text(),
            'export_all': self.radio_export_all.isChecked(),
            'export_animation': self.check_export_animation.isChecked(),
            'animation_range_min': self.anim_range_min.value(),
            'animation_range_max': self.anim_range_max.value(),
            'copy_textures': self.check_copy_textures.isChecked(),
            'keep_mat_paths': self.keep_mat_paths.isChecked(),
            'pointcloud_mode': self.radio_export_ptcloud.isChecked(),
            'extra_pointcloud': self.check_extra_ptcloud.isChecked(),
            'extra_culling': self.check_extra_occlusion.isChecked(),
            'active_camera': self.active_camera.currentText(),
            'extra_lights': self.check_extra_lights.isChecked(),
            'extra_mats': self.check_extra_special_mats.isChecked(),
            'skybox_check': self.check_skybox.isChecked(),
            'skybox_path': self.textbox_skybox_path.text()
        })
        # write to json
        with open(config_path, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

        self.write_to_log("maya config saved to " + config_path)

    def message_query(self, title, message):
        """
        Popup to ask user input
        Args:
            title: Title of the popup
            message: Message of the popup
        Returns: True / False for the user's answer
        """
        result = QtWidgets.QMessageBox.question(self, title, message,
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            answer = True
        else:
            answer = False
        self.write_to_log(title + " | " + message + " | " + str(answer))
        return answer

    def handle_error(self, error_message):
        """
        Handle error by sending an error message
        Args:
            error_message: the error message
        """
        QtWidgets.QMessageBox.warning(self, "Warning", error_message)
        print error_message
        self.write_to_log(error_message)

    def popup_message(self, title, message):
        """
        A popup message
        Args:
            title: Title of the popup message
            message: Body of the popup message
        """
        QtWidgets.QMessageBox.information(self, title, message)
        self.write_to_log(title + " | " + message)

    def write_to_log(self, message):
        """
        Write message to log (on the 2nd tab)
        Args:
            message: message to write to log
        """
        self.text_log.appendPlainText(message)


class Config:
    """
    Configuration class
    """
    folder_path = ""
    scene_name = ""
    export_all = False
    # export animation + range
    export_animation = False
    animation_range_min = 0
    animation_range_max = 0
    # textures
    copy_textures = False
    keep_mat_paths = False
    # point cloud
    exportmode = False
    # extra file
    ptcloud = False
    occlusion = False
    active_camera = False
    lights = False
    special_mats = False
    # Skybox
    skybox = False
    skybox_env_path = ""
    skybox_radiance_path = ""
    skybox_irradiance_path = ""
