#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
材质创建模块
用于创建材质实例和连接纹理

此模块提供了创建材质实例、连接纹理到材质参数和组织材质的功能。
"""

import os
import unreal

class MaterialCreator:
    """材质创建类，用于创建和设置材质"""

    def __init__(self, config=None):
        """
        初始化材质创建器

        Args:
            config (dict, optional): 配置字典，包含材质创建设置
        """
        self.config = config or {}

        # 获取编辑器子系统
        self.editor_asset_subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

        # 材质模板路径
        self.material_template = self.config.get("material_template", "/Game/MaterialTemplates/M_Standard")

        # 材质实例后缀
        self.material_instance_suffix = self.config.get("material_instance_suffix", "_Inst")

        # 材质模板映射
        self.material_template_mapping = self.config.get("material_template_mapping", {})
        self.use_template_mapping = self.material_template_mapping.get("enabled", False)

    def create_material_instance(self, base_name, target_path, textures=None, material_template=None):
        """
        创建材质实例

        Args:
            base_name (str): 基础名称，用于命名材质实例
            target_path (str): 目标路径
            textures (dict, optional): 纹理映射 {纹理类型: 纹理资产}
            material_template (str, optional): 材质模板路径，如果为None则使用默认模板

        Returns:
            object: 创建的材质实例
        """
        # 使用提供的模板或默认模板
        template_path = material_template or self.material_template

        # 检查材质模板是否存在
        if not unreal.EditorAssetLibrary.does_asset_exist(template_path):
            unreal.log_error(f"材质模板不存在: {template_path}")
            return None

        # 创建材质实例路径
        material_instance_name = f"{base_name}{self.material_instance_suffix}"
        material_instance_path = f"{target_path}/Materials/{material_instance_name}"

        # 确保材质文件夹存在
        materials_folder = f"{target_path}/Materials"
        if not unreal.EditorAssetLibrary.does_directory_exist(materials_folder):
            unreal.EditorAssetLibrary.make_directory(materials_folder)

        # 检查材质实例是否已存在
        if unreal.EditorAssetLibrary.does_asset_exist(material_instance_path):
            # 如果已存在，加载它
            material_instance = unreal.EditorAssetLibrary.load_asset(material_instance_path)
        else:
            # 创建新的材质实例
            material_instance_factory = unreal.MaterialInstanceConstantFactoryNew()
            material_instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                material_instance_name,
                materials_folder,
                unreal.MaterialInstanceConstant,
                material_instance_factory
            )

            # 设置父材质
            parent_material = unreal.EditorAssetLibrary.load_asset(template_path)
            material_instance.set_editor_property("parent", parent_material)

        # 如果提供了纹理，连接它们
        if textures:
            self._connect_textures_to_material(material_instance, textures)

        # 保存材质实例
        unreal.EditorAssetLibrary.save_loaded_asset(material_instance)

        return material_instance

    def _connect_textures_to_material(self, material_instance, textures):
        """
        将纹理连接到材质实例的参数

        Args:
            material_instance: 材质实例对象
            textures (dict): 纹理映射 {纹理类型: 纹理资产}
        """
        # 定义纹理类型到材质参数名称的映射
        param_names = {
            "diffuse": "BaseColor",
            "normal": "Normal",
            "roughness": "Roughness",
            "metallic": "Metallic",
            "specular": "Specular",
            "emissive": "Emissive"
        }

        # 连接每种纹理
        for texture_type, texture_asset in textures.items():
            if texture_type in param_names:
                param_name = param_names[texture_type]

                # 加载纹理对象
                texture_object = unreal.EditorAssetLibrary.load_asset(texture_asset)
                if not texture_object:
                    unreal.log_warning(f"无法加载纹理: {texture_asset}")
                    continue

                # 设置纹理参数
                try:
                    # 创建参数信息
                    param_info = unreal.MaterialInstanceParameterInfo()
                    param_info.set_editor_property("name", param_name)

                    # 设置纹理参数值
                    material_instance.set_texture_parameter_value_by_info(param_info, texture_object)

                    unreal.log(f"已连接纹理 {texture_type} 到参数 {param_name}")
                except Exception as e:
                    unreal.log_error(f"连接纹理到材质参数时出错: {e}")

    def assign_material_to_mesh(self, mesh_asset, material_instance):
        """
        将材质实例分配给网格体

        Args:
            mesh_asset: 网格体资产
            material_instance: 材质实例

        Returns:
            bool: 是否成功分配
        """
        try:
            # 加载网格体对象
            mesh_object = unreal.EditorAssetLibrary.load_asset(mesh_asset)
            if not mesh_object:
                unreal.log_warning(f"无法加载网格体: {mesh_asset}")
                return False

            # 检查是静态网格还是骨骼网格
            if isinstance(mesh_object, unreal.StaticMesh):
                # 静态网格
                for i in range(mesh_object.get_num_sections(0)):
                    mesh_object.set_material(i, material_instance)

                unreal.log(f"已将材质分配给静态网格 {mesh_asset}")
            elif isinstance(mesh_object, unreal.SkeletalMesh):
                # 骨骼网格
                for i in range(mesh_object.get_num_lod_models()):
                    for j in range(mesh_object.get_num_sections(i)):
                        mesh_object.set_material(j, material_instance)

                unreal.log(f"已将材质分配给骨骼网格 {mesh_asset}")
            else:
                unreal.log_warning(f"不支持的网格体类型: {type(mesh_object)}")
                return False

            # 保存网格体
            unreal.EditorAssetLibrary.save_loaded_asset(mesh_object)

            return True
        except Exception as e:
            unreal.log_error(f"分配材质到网格体时出错: {e}")
            return False

    def create_materials_for_assets(self, assets, imported_assets, imported_textures, target_path):
        """
        为导入的资产创建材质

        Args:
            assets (dict): 按类型分组的资产字典
            imported_assets (dict): 导入的资产映射 {资产文件路径: 导入的资产}
            imported_textures (dict): 导入的纹理映射 {纹理文件路径: 导入的纹理资产}
            target_path (str): 基础目标路径

        Returns:
            dict: 创建的材质实例映射 {基础名称: 材质实例}
        """
        created_materials = {}

        # 处理FBX资产
        for asset_file in assets.get("fbx", []):
            # 检查资产是否已导入
            if asset_file.file_path not in imported_assets:
                continue

            # 获取导入的资产
            imported_asset = imported_assets[asset_file.file_path]

            # 收集相关纹理
            asset_textures = {}
            for related_asset in asset_file.related_assets:
                if related_asset.file_path in imported_textures:
                    texture_type = self._get_texture_type(related_asset)
                    asset_textures[texture_type] = imported_textures[related_asset.file_path]

            # 根据资产名称选择合适的材质模板
            material_template = self._get_material_template_for_asset(asset_file)

            # 如果有相关纹理，创建材质实例
            if asset_textures:
                material_instance = self.create_material_instance(
                    asset_file.base_name,
                    target_path,
                    asset_textures,
                    material_template
                )

                if material_instance:
                    created_materials[asset_file.base_name] = material_instance

                    # 将材质分配给网格体
                    self.assign_material_to_mesh(imported_asset, material_instance)

        return created_materials

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

    def _get_material_template_for_asset(self, asset_file):
        """
        根据资产文件名选择合适的材质模板

        Args:
            asset_file: 资产文件对象

        Returns:
            str: 材质模板路径
        """
        # 如果未启用模板映射，使用默认模板
        if not self.use_template_mapping:
            return self.material_template

        # 获取默认模板
        default_template = self.material_template_mapping.get("default_template", self.material_template)

        # 获取映射列表
        mappings = self.material_template_mapping.get("mappings", [])

        # 检查文件名是否匹配任何模式
        file_name = asset_file.file_name

        for mapping in mappings:
            pattern = mapping.get("pattern", "")
            if pattern and pattern in file_name:
                template = mapping.get("template", "")
                if template and unreal.EditorAssetLibrary.does_asset_exist(template):
                    unreal.log(f"为资产 {file_name} 使用材质模板: {template}")
                    return template
                else:
                    unreal.log_warning(f"材质模板不存在: {template}，使用默认模板")

        # 如果没有匹配的模式，使用默认模板
        return default_template
