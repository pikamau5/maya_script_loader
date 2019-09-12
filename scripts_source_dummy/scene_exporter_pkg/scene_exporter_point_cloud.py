"""
Convert scene into point cloud. To be used with scene_exporter.py

TODO: add support for usd (Can't find function to import back into maya atm)
"""

from maya import cmds
import pymel.core as pm


class PointCloudExport():

    def set_attrs(self, base_path, file_format, mesh_folder):
        """
        Finds object instances and exports individual meshes, sets file path as attribute
        Args:
            base_path: path to asset folder
            file_format: file format (currently only supports fbx)
            mesh_folder: folder name where meshes will be exported to
        Returns: Dictionary with point cloud mesh info for each point
        """
        mesh_dict = {}  # dictionary to send to the extra file
        mesh_dict['PointCloudData'] = []
        nodes = cmds.ls(type="transform")  # get list of objs in scene
        # iterate through each object
        for node in nodes:
            cmds.select(clear=True)  # clear selection
            cmds.select(node)  # select node
            # check if node has polygons
            polycount = cmds.polyEvaluate(f=True)
            has_polys = isinstance(polycount, int)
            if has_polys:
                # get shape instances
                get_child = cmds.listRelatives(node,children=True)
                instances = cmds.ls(get_child[0], ap=True)

                # if no instances exist
                if len(instances) <= 1:
                    # export obj
                    node_name = str(node).split(".")[0]
                    self.save_mesh(node_name, base_path, file_format, mesh_folder)
                    relative_path = mesh_folder + "/" + node + file_format

                    # set attribute
                    try:  # see if attr exists TODO - might not be a good way to handle this?
                        cmds.getAttr(node + ".ref_path")
                    except Exception as e:  # if it doesnt exist, create attr
                        print e # TODO add to log
                        cmds.addAttr(node, longName="ref_path", dataType="string")
                        cmds.setAttr(node + "." + "ref_path", relative_path, type="string")
                    # append to dictionary
                    mesh_dict['PointCloudData'].append({
                        'Mesh': node,
                        'Path': relative_path
                    })

                # if instances exist
                if len(instances) > 1:  # TODO - check if mesh gets rewritten
                    # get shape parent
                    first_inst = cmds.listRelatives(instances[0], parent=True)
                    # set output path
                    relative_path = mesh_folder + "/" + first_inst[0] + file_format

                    # set attribute to first instance
                    try:  # see if attr exists
                        cmds.getAttr(first_inst[0] + ".ref_path")
                    except Exception as e: # if it doesnt exist, create attr
                        print e # TODO add to log
                        cmds.addAttr(first_inst[0], longName="ref_path", dataType="string")
                        cmds.setAttr(first_inst[0] + "." + "ref_path", relative_path, type="string")

                    # export obj
                    self.save_mesh(first_inst[0], base_path, file_format, mesh_folder)

                    # copy first attribute to the rest of the instances
                    for i in instances:
                        first_attr = cmds.getAttr(str(first_inst[0]) + ".ref_path")
                        inst_parent = cmds.listRelatives(i, parent=True)
                        try: # see if attr exists (somehow prone to crash)
                            cmds.getAttr(inst_parent[0] + ".ref_path")
                        except Exception as e:  # if it doesnt exist, create attr
                            print e  # TODO add to log
                            cmds.addAttr(inst_parent[0], longName="ref_path", dataType="string")
                            cmds.setAttr(inst_parent[0] + "." + "ref_path", first_attr, type="string")
                    # append to dictionary
                    mesh_dict['PointCloudData'].append({
                        'Mesh': node,
                        'Path': relative_path
                    })
        return mesh_dict

    @staticmethod
    def save_mesh(obj, base_path, file_format, mesh_folder):
        """
        Saves individual mesh to file
        Args:
            obj: Maya object
            base_path: asset path
            file_format: file format
            mesh_folder: folder name where meshes will be exported
        """
        cmds.select(clear=True)
        cmds.select(obj)
        # save the original mesh position (should be simplified)
        node_posX = cmds.getAttr(str(obj) + ".translateX")
        node_posY = cmds.getAttr(str(obj) + ".translateY")
        node_posZ = cmds.getAttr(str(obj) + ".translateZ")

        # move object to origin
        cmds.move(0, 0, 0)

        # save to alembic - currently disabled
        '''
        start = 0
        end = 0
        root = "-root " + str(node)
        save_name = base_path + "/meshes/" + node + format
        command = "-frameRange " + str(start) + " " + str(end) + " -uvWrite -worldSpace " + root + " -file " + save_name
        cmds.AbcExport(j=command)
        '''
        # save fbx
        file_path = base_path + "/" + mesh_folder + "/" + obj + file_format
        cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 0)
        cmds.FBXExportEmbeddedTextures('-v', False)
        pm.mel.eval('FBXExport -f \"' + file_path + '\"  -s')

        # move object back where it was
        cmds.move(node_posX, node_posY, node_posZ)

    @staticmethod
    def save_point_cloud_scene(base_path, scene_name, file_format, export_animation, scene_folder, selection, export_all):
        """
        Save point cloud scene to scene folder
        Args:
            base_path: asset folder path
            scene_name: name of scene
            file_format: file format
            export_animation: boolean whether animation is enabled
            scene_folder: folder name where the scene will be saved
            selection: object selection
            export_all: is export all selected in the ui
        """
        if not export_all:
            # delete objects that are not in selection
            cmds.select(selection)
            cmds.select(all=True, toggle=True)
            cmds.delete()
            # get selection
            cmds.select(selection)
        else:
            cmds.select(all=True)

        # save alembic - currently disabled
        '''
        start = 0
        end = 0
        root = "-root " + str(scene_name)
        save_name = base_path + "/scene/" + scene_name + format
        command = "-frameRange " + str(start) + " " + str(end) + " -uvWrite -worldSpace " + root + " -file " + save_name
        cmds.AbcExport(j=command)
        '''

        # export fbx
        file_path = base_path + "/" + scene_folder + "/" + scene_name + "_pointcloud" + file_format
        cmds.FBXExportEmbeddedTextures('-v', False)
        if export_animation:
            cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 1)
        else:
            cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 0)
        pm.mel.FBXExport(f=file_path)

    def del_shapes(self):
        """
        Delete shapes and leave points
        """
        cmds.select(all=True, hierarchy=True)
        selected_objs = cmds.ls(sl=1)
        selected_shapes = cmds.listRelatives(selected_objs, s=True)
        cmds.select(clear=True)
        cmds.select(selected_shapes)

        # deselect cameras
        cameras = cmds.ls(cameras=True)
        cmds.select(cameras, deselect=True)

        cmds.delete()


