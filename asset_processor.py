#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资产处理模块
用于处理不同类型的资产导入

此模块提供了导入FBX、MA文件和其他资产类型的功能，使用Interchange插件API。
"""

import os
import unreal

class AssetProcessor:
    """资产处理类，用于导入不同类型的资产"""
    
    def __init__(self, config=None):
        """
        初始化资产处理器
        
        Args:
            config (dict, optional): 配置字典，包含导入设置
        """
        self.config = config or {}
        
        # 获取编辑器子系统
        self.editor_asset_subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
        self.level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        
        # 启用FBX导入功能（如果需要）
        self._enable_fbx_import()
    
    def _enable_fbx_import(self):
        """启用Interchange FBX导入功能"""
        unreal.SystemLibrary.execute_console_command(
            self.level_editor_subsystem.get_world(), 
            'Interchange.FeatureFlags.Import.FBX true'
        )
    
    def import_asset(self, asset_file, target_path):
        """
        导入资产文件
        
        Args:
            asset_file: 要导入的资产文件对象
            target_path (str): 导入目标路径
        
        Returns:
            object: 导入的资产对象
        """
        if asset_file.extension == ".fbx":
            return self.import_fbx(asset_file, target_path)
        elif asset_file.extension == ".ma":
            return self.import_maya_file(asset_file, target_path)
        else:
            unreal.log_warning(f"不支持的资产类型: {asset_file.extension}")
            return None
    
    def import_fbx(self, asset_file, target_path):
        """
        导入FBX文件
        
        Args:
            asset_file: FBX资产文件对象
            target_path (str): 导入目标路径
        
        Returns:
            object: 导入的资产对象
        """
        # 创建临时管道路径
        transient_path = "/Interchange/Pipelines/Transient/"
        transient_pipeline_path = transient_path + "CustomAssetPipeline"
        
        # 删除可能存在的临时管道
        self.editor_asset_subsystem.delete_directory(transient_path)
        
        # 复制默认管道
        pipeline = self.editor_asset_subsystem.duplicate_asset(
            "/Interchange/Pipelines/DefaultAssetsPipeline", 
            transient_pipeline_path
        )
        
        # 根据资产类型配置管道
        if asset_file.asset_type == "static_mesh":
            self._configure_static_mesh_pipeline(pipeline)
        elif asset_file.asset_type == "skeletal_mesh":
            self._configure_skeletal_mesh_pipeline(pipeline)
        elif asset_file.asset_type == "animation":
            self._configure_animation_pipeline(pipeline)
        
        # 创建源数据
        source_data = unreal.InterchangeManager.create_source_data(asset_file.file_path)
        
        # 创建导入参数
        import_asset_parameters = unreal.ImportAssetParameters()
        import_asset_parameters.is_automated = True
        
        # 添加配置的管道
        import_asset_parameters.override_pipelines.append(
            unreal.SoftObjectPath(transient_pipeline_path + ".CustomAssetPipeline")
        )
        
        # 获取Interchange管理器并导入资产
        interchange_manager = unreal.InterchangeManager.get_interchange_manager_scripted()
        result = interchange_manager.import_asset(target_path, source_data, import_asset_parameters)
        
        # 清理临时管道
        self.editor_asset_subsystem.delete_directory(transient_path)
        
        return result
    
    def _configure_static_mesh_pipeline(self, pipeline):
        """
        配置静态网格导入管道
        
        Args:
            pipeline: 要配置的管道对象
        """
        # 设置为静态网格
        pipeline.common_meshes_properties.force_all_mesh_as_type = unreal.InterchangeForceMeshType.IFMT_STATIC_MESH
        
        # 获取静态网格导入设置
        static_mesh_config = self.config.get("fbx_import", {}).get("static_mesh", {})
        
        # 应用设置
        pipeline.mesh_pipeline.combine_static_meshes = static_mesh_config.get("combine_meshes", False)
        pipeline.mesh_pipeline.generate_lightmap_uvs = static_mesh_config.get("generate_lightmap_uvs", True)
        pipeline.mesh_pipeline.auto_generate_collision = static_mesh_config.get("auto_generate_collision", True)
        pipeline.mesh_pipeline.remove_degenerates = static_mesh_config.get("remove_degenerates", True)
        
        # 设置材质导入选项
        self._configure_material_pipeline(pipeline)
    
    def _configure_skeletal_mesh_pipeline(self, pipeline):
        """
        配置骨骼网格导入管道
        
        Args:
            pipeline: 要配置的管道对象
        """
        # 设置为骨骼网格
        pipeline.common_meshes_properties.force_all_mesh_as_type = unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH
        
        # 获取骨骼网格导入设置
        skeletal_mesh_config = self.config.get("fbx_import", {}).get("skeletal_mesh", {})
        
        # 应用设置
        pipeline.mesh_pipeline.import_morph_targets = skeletal_mesh_config.get("import_morph_targets", True)
        pipeline.mesh_pipeline.import_meshes_in_bone_hierarchy = skeletal_mesh_config.get("import_meshes_in_bone_hierarchy", True)
        pipeline.mesh_pipeline.preserve_smoothing_groups = skeletal_mesh_config.get("preserve_smoothing_groups", True)
        
        # 设置动画导入选项
        pipeline.animation_pipeline.import_animations = skeletal_mesh_config.get("import_animations", True)
        
        # 设置材质导入选项
        self._configure_material_pipeline(pipeline)
    
    def _configure_animation_pipeline(self, pipeline):
        """
        配置动画导入管道
        
        Args:
            pipeline: 要配置的管道对象
        """
        # 获取动画导入设置
        animation_config = self.config.get("fbx_import", {}).get("animation", {})
        
        # 应用设置
        pipeline.animation_pipeline.import_animations = animation_config.get("import_animations", True)
        pipeline.animation_pipeline.animation_length = animation_config.get("animation_length", "ExportedTime")
        
        # 设置帧范围
        frame_range = animation_config.get("frame_import_range", [0, 0])
        pipeline.animation_pipeline.frame_import_range = unreal.Int32Interval(frame_range[0], frame_range[1])
        
        # 设置采样率
        pipeline.animation_pipeline.use_default_sample_rate = animation_config.get("use_default_sample_rate", True)
        pipeline.animation_pipeline.custom_sample_rate = animation_config.get("custom_sample_rate", 30)
    
    def _configure_material_pipeline(self, pipeline):
        """
        配置材质导入管道
        
        Args:
            pipeline: 要配置的管道对象
        """
        # 根据配置设置是否导入材质
        pipeline.material_pipeline.import_materials = self.config.get("create_materials", True)
        
        # 如果不导入材质，也不导入纹理
        if not self.config.get("create_materials", True):
            pipeline.material_pipeline.texture_pipeline.import_textures = False
        else:
            # 设置纹理导入选项
            pipeline.material_pipeline.texture_pipeline.import_textures = self.config.get("process_textures", True)
    
    def import_maya_file(self, asset_file, target_path):
        """
        导入Maya文件
        
        Args:
            asset_file: Maya资产文件对象
            target_path (str): 导入目标路径
        
        Returns:
            object: 导入的资产对象
        """
        # Maya文件需要先转换为FBX
        # 这里可以调用Maya的命令行工具进行转换
        # 由于这需要Maya的安装和额外设置，这里只提供一个示例框架
        
        unreal.log_warning("Maya文件导入需要先转换为FBX格式。请使用Maya导出为FBX后再导入。")
        return None
