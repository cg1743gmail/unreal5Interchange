#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
纹理处理模块
用于处理纹理导入和设置

此模块提供了导入纹理、设置纹理属性和组织纹理的功能。
"""

import os
import unreal

class TextureProcessor:
    """纹理处理类，用于导入和处理纹理"""

    def __init__(self, config=None):
        """
        初始化纹理处理器

        Args:
            config (dict, optional): 配置字典，包含纹理导入设置
        """
        self.config = config or {}

        # 获取编辑器子系统
        self.editor_asset_subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
        self.level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

        # 纹理设置映射
        self.texture_settings = self.config.get("texture_settings", {})

        # 特殊纹理文件夹映射
        self.texture_special_folders = self.config.get("texture_special_folders", {})
        self.use_special_folders = self.texture_special_folders.get("enabled", False)

    def import_texture(self, texture_file, target_path):
        """
        导入纹理文件

        Args:
            texture_file: 要导入的纹理文件对象
            target_path (str): 导入目标路径

        Returns:
            object: 导入的纹理对象
        """
        # 创建临时管道路径
        transient_path = "/Interchange/Pipelines/Transient/"
        transient_pipeline_path = transient_path + "CustomTexturePipeline"

        # 删除可能存在的临时管道
        self.editor_asset_subsystem.delete_directory(transient_path)

        # 复制默认纹理管道
        pipeline = self.editor_asset_subsystem.duplicate_asset(
            "/Interchange/Pipelines/DefaultTexturePipeline",
            transient_pipeline_path
        )

        # 根据纹理类型配置管道
        texture_type = self._get_texture_type(texture_file)
        self._configure_texture_pipeline(pipeline, texture_type)

        # 创建源数据
        source_data = unreal.InterchangeManager.create_source_data(texture_file.file_path)

        # 创建导入参数
        import_asset_parameters = unreal.ImportAssetParameters()
        import_asset_parameters.is_automated = True

        # 添加配置的管道
        import_asset_parameters.override_pipelines.append(
            unreal.SoftObjectPath(transient_pipeline_path + ".CustomTexturePipeline")
        )

        # 获取Interchange管理器并导入资产
        interchange_manager = unreal.InterchangeManager.get_interchange_manager_scripted()
        result = interchange_manager.import_asset(target_path, source_data, import_asset_parameters)

        # 清理临时管道
        self.editor_asset_subsystem.delete_directory(transient_path)

        # 如果导入成功，设置纹理属性
        if result and self.config.get("compress_textures", True):
            self._set_texture_properties(result, texture_type)

        return result

    def _get_texture_type(self, texture_file):
        """
        获取纹理类型

        Args:
            texture_file: 纹理文件对象

        Returns:
            str: 纹理类型
        """
        # 从资产类型中提取纹理类型
        if texture_file.asset_type.startswith("texture_"):
            return texture_file.asset_type[8:]  # 移除 "texture_" 前缀
        return "other"

    def _check_special_folder(self, texture_file):
        """
        检查纹理是否应该使用特殊文件夹

        Args:
            texture_file: 纹理文件对象

        Returns:
            tuple: (是否使用特殊文件夹, 文件夹名称, 设置)
        """
        # 如果未启用特殊文件夹，直接返回False
        if not self.use_special_folders:
            return False, None, None

        # 获取映射列表
        mappings = self.texture_special_folders.get("mappings", [])

        # 检查文件名是否匹配任何模式
        file_name = texture_file.file_name

        for mapping in mappings:
            pattern = mapping.get("pattern", "")
            if pattern and pattern.lower() in file_name.lower():
                folder = mapping.get("folder", "")
                if folder:
                    # 创建设置字典
                    settings = {
                        "compression_settings": mapping.get("compression_settings", "Default"),
                        "srgb": mapping.get("srgb", True)
                    }
                    return True, folder, settings

        # 如果没有匹配的模式，返回False
        return False, None, None

    def _configure_texture_pipeline(self, pipeline, texture_type):
        """
        配置纹理导入管道

        Args:
            pipeline: 要配置的管道对象
            texture_type (str): 纹理类型
        """
        # 获取纹理类型的设置
        settings = self.texture_settings.get(texture_type, {})

        # 设置SRGB
        pipeline.texture_pipeline.set_srgb = True
        pipeline.texture_pipeline.srgb = settings.get("srgb", True)

        # 设置压缩
        if self.config.get("compress_textures", True):
            pipeline.texture_pipeline.set_compression_settings = True
            compression_setting = settings.get("compression_settings", "Default")

            # 将字符串转换为枚举值
            try:
                compression_enum = getattr(unreal.TextureCompressionSettings, compression_setting)
                pipeline.texture_pipeline.compression_settings = compression_enum
            except AttributeError:
                unreal.log_warning(f"无效的纹理压缩设置: {compression_setting}")
                pipeline.texture_pipeline.compression_settings = unreal.TextureCompressionSettings.DEFAULT

        # 设置纹理组
        texture_group = self.config.get("texture_group", "World")
        try:
            texture_group_enum = getattr(unreal.TextureGroup, texture_group)
            pipeline.texture_pipeline.texture_group = texture_group_enum
        except AttributeError:
            unreal.log_warning(f"无效的纹理组: {texture_group}")
            pipeline.texture_pipeline.texture_group = unreal.TextureGroup.WORLD

    def _set_texture_properties(self, texture_asset, texture_type):
        """
        设置纹理属性

        Args:
            texture_asset: 导入的纹理资产
            texture_type (str): 纹理类型
        """
        # 获取纹理对象
        texture_object = unreal.AssetRegistryHelpers.get_asset(texture_asset)
        if not texture_object:
            unreal.log_warning(f"无法获取纹理对象: {texture_asset}")
            return

        # 获取纹理类型的设置
        settings = self.texture_settings.get(texture_type, {})

        # 设置SRGB
        texture_object.set_editor_property("srgb", settings.get("srgb", True))

        # 设置压缩
        if self.config.get("compress_textures", True):
            compression_setting = settings.get("compression_settings", "Default")
            try:
                compression_enum = getattr(unreal.TextureCompressionSettings, compression_setting)
                texture_object.set_editor_property("compression_settings", compression_enum)
            except AttributeError:
                unreal.log_warning(f"无效的纹理压缩设置: {compression_setting}")

        # 设置MIP生成设置
        mip_gen_setting = settings.get("mip_gen_settings", "FromTextureGroup")
        try:
            mip_gen_enum = getattr(unreal.TextureMipGenSettings, mip_gen_setting)
            texture_object.set_editor_property("mip_gen_settings", mip_gen_enum)
        except AttributeError:
            unreal.log_warning(f"无效的MIP生成设置: {mip_gen_setting}")

        # 设置纹理组
        texture_group = self.config.get("texture_group", "World")
        try:
            texture_group_enum = getattr(unreal.TextureGroup, texture_group)
            texture_object.set_editor_property("lod_group", texture_group_enum)
        except AttributeError:
            unreal.log_warning(f"无效的纹理组: {texture_group}")

        # 保存纹理
        unreal.EditorAssetLibrary.save_loaded_asset(texture_object)

    def organize_textures(self, textures, target_path):
        """
        组织纹理到适当的文件夹

        Args:
            textures (dict): 按类型分组的纹理字典
            target_path (str): 基础目标路径

        Returns:
            dict: 导入的纹理映射 {纹理文件路径: 导入的纹理资产}
        """
        imported_textures = {}

        # 确保基本纹理文件夹存在
        base_texture_folder = f"{target_path}/Textures"
        if not unreal.EditorAssetLibrary.does_directory_exist(base_texture_folder):
            unreal.EditorAssetLibrary.make_directory(base_texture_folder)

        # 为每种纹理类型创建子文件夹
        for texture_type, texture_list in textures.items():
            if not texture_list:
                continue

            # 导入每个纹理
            for texture_file in texture_list:
                # 检查是否应该使用特殊文件夹
                use_special, special_folder, special_settings = self._check_special_folder(texture_file)

                if use_special and special_folder:
                    # 使用特殊文件夹
                    folder_path = f"{base_texture_folder}/{special_folder}"
                    unreal.log(f"将纹理 {texture_file.file_name} 导入到特殊文件夹: {special_folder}")

                    # 确保特殊文件夹存在
                    if not unreal.EditorAssetLibrary.does_directory_exist(folder_path):
                        unreal.EditorAssetLibrary.make_directory(folder_path)

                    # 如果有特殊设置，临时覆盖纹理设置
                    if special_settings:
                        original_settings = self.texture_settings.get(texture_type, {})
                        self.texture_settings[texture_type] = special_settings

                        # 导入纹理
                        imported_texture = self.import_texture(texture_file, folder_path)

                        # 恢复原始设置
                        self.texture_settings[texture_type] = original_settings
                    else:
                        # 导入纹理
                        imported_texture = self.import_texture(texture_file, folder_path)
                else:
                    # 使用常规文件夹
                    type_folder = f"{base_texture_folder}/{texture_type.capitalize()}"

                    # 确保文件夹存在
                    if not unreal.EditorAssetLibrary.does_directory_exist(type_folder):
                        unreal.EditorAssetLibrary.make_directory(type_folder)

                    # 导入纹理
                    imported_texture = self.import_texture(texture_file, type_folder)

                # 记录导入的纹理
                if imported_texture:
                    imported_textures[texture_file.file_path] = imported_texture

        return imported_textures
