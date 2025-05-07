#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
材质创建模块
用于创建材质实例和连接纹理

此模块提供了创建材质实例、连接纹理到材质参数和组织材质的功能。
"""

import os
import unreal
import re
import os.path

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

        # 材质槽映射
        self.material_slot_mapping = self.config.get("material_slot_mapping", {})
        self.use_slot_mapping = self.material_slot_mapping.get("enabled", False)
        self.save_material_instances = self.material_slot_mapping.get("save_material_instances", True)
        self.material_instances_path = self.material_slot_mapping.get("material_instances_path", "/Game/MaterialInstances")

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

        # 创建材质实例名称
        material_instance_name = self._format_material_instance_name(base_name, None, template_path)
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

        # 导入AssetProcessor以获取材质槽名称
        from asset_processor import AssetProcessor
        asset_processor = AssetProcessor(self.config)

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

            # 检查是否使用材质槽映射
            if self.use_slot_mapping:
                # 获取材质槽名称
                material_slot_names = asset_processor.get_material_slot_names(imported_asset)

                if material_slot_names:
                    # 为每个材质槽创建材质实例
                    slot_materials = {}
                    for slot_name in material_slot_names:
                        # 创建材质实例
                        material_instance = self.create_material_instance_for_slot(
                            asset_file.base_name,
                            slot_name,
                            asset_textures
                        )

                        if material_instance:
                            slot_materials[slot_name] = material_instance

                    # 将材质实例保存到结果中
                    if slot_materials:
                        created_materials[asset_file.base_name] = slot_materials

                        # 如果不保存材质实例，则将它们分配给网格体
                        if not self.save_material_instances:
                            # TODO: 实现根据槽名称分配材质
                            pass

                    # 继续处理下一个资产
                    continue

            # 如果没有使用材质槽映射或没有找到材质槽，使用基于文件名的映射
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

    def _format_material_instance_name(self, asset_name, slot_name=None, template_path=None):
        """
        根据命名规则格式化材质实例名称

        Args:
            asset_name (str): 资产名称
            slot_name (str, optional): 材质槽名称
            template_path (str, optional): 材质模板路径

        Returns:
            str: 格式化后的材质实例名称
        """
        # 如果未启用材质槽映射或没有命名规则，使用默认命名方式
        if not self.use_slot_mapping:
            return f"{asset_name}{self.material_instance_suffix}"

        # 获取命名规则
        naming_convention = self.material_slot_mapping.get("naming_convention", {})
        if not naming_convention:
            return f"{asset_name}_{slot_name}" if slot_name else asset_name

        # 获取格式字符串
        format_str = naming_convention.get("format", "MI_{asset_name}_{slot_name}")

        # 提取模板名称（如果有）
        template_name = ""
        if template_path:
            template_name = os.path.basename(template_path)
            # 移除扩展名和前缀
            template_name = os.path.splitext(template_name)[0]
            if template_name.startswith("M_"):
                template_name = template_name[2:]

        # 替换格式字符串中的占位符
        name = format_str
        name = name.replace("{asset_name}", asset_name)
        name = name.replace("{slot_name}", slot_name or "")
        name = name.replace("{template_name}", template_name)

        # 替换空格
        replace_spaces = naming_convention.get("replace_spaces", "_")
        if replace_spaces:
            name = name.replace(" ", replace_spaces)

        # 应用大小写规则
        case = naming_convention.get("case", "preserve")
        if case == "upper":
            name = name.upper()
        elif case == "lower":
            name = name.lower()
        elif case == "title":
            name = name.title()

        # 清理名称（移除连续的下划线等）
        name = re.sub(r'_+', '_', name)  # 将多个连续下划线替换为单个下划线
        name = name.strip('_')  # 移除开头和结尾的下划线

        return name

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

    def _get_material_template_for_slot(self, slot_name):
        """
        根据材质槽名称选择合适的材质模板

        Args:
            slot_name (str): 材质槽名称

        Returns:
            str: 材质模板路径
        """
        # 如果未启用槽映射，使用默认模板
        if not self.use_slot_mapping or not slot_name:
            return self.material_template

        # 获取默认模板
        default_template = self.material_slot_mapping.get("default_template", self.material_template)

        # 获取映射列表
        mappings = self.material_slot_mapping.get("mappings", [])

        # 检查槽名称是否匹配任何模式
        for mapping in mappings:
            pattern = mapping.get("pattern", "")
            if pattern and pattern in slot_name:
                template = mapping.get("template", "")
                if template and unreal.EditorAssetLibrary.does_asset_exist(template):
                    unreal.log(f"为材质槽 {slot_name} 使用材质模板: {template}")
                    return template
                else:
                    unreal.log_warning(f"材质模板不存在: {template}，使用默认模板")

        # 如果没有匹配的模式，使用默认模板
        return default_template

    def create_material_instance_for_slot(self, base_name, slot_name, textures=None):
        """
        为材质槽创建材质实例

        Args:
            base_name (str): 基础名称
            slot_name (str): 材质槽名称
            textures (dict, optional): 纹理映射 {纹理类型: 纹理资产}

        Returns:
            object: 创建的材质实例
        """
        # 根据槽名称选择材质模板
        material_template = self._get_material_template_for_slot(slot_name)

        # 创建实例名称
        instance_name = self._format_material_instance_name(base_name, slot_name, material_template)

        # 确保材质实例路径存在
        if not unreal.EditorAssetLibrary.does_directory_exist(self.material_instances_path):
            unreal.EditorAssetLibrary.make_directory(self.material_instances_path)

        # 创建材质实例
        return self.create_material_instance(
            instance_name,
            self.material_instances_path,
            textures,
            material_template
        )
