#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资产组织模块
用于管理导入后的资产结构

此模块提供了创建文件夹结构、移动和重命名资产的功能。
"""

import os
import unreal

class AssetOrganizer:
    """资产组织类，用于组织导入的资产"""
    
    def __init__(self, config=None):
        """
        初始化资产组织器
        
        Args:
            config (dict, optional): 配置字典，包含组织设置
        """
        self.config = config or {}
    
    def create_folder_structure(self, target_path):
        """
        创建基本的文件夹结构
        
        Args:
            target_path (str): 基础目标路径
        """
        # 创建主要文件夹
        folders = [
            f"{target_path}/Meshes/StaticMeshes",
            f"{target_path}/Meshes/SkeletalMeshes",
            f"{target_path}/Animations",
            f"{target_path}/Materials",
            f"{target_path}/Textures/Diffuse",
            f"{target_path}/Textures/Normal",
            f"{target_path}/Textures/Roughness",
            f"{target_path}/Textures/Metallic",
            f"{target_path}/Textures/Specular",
            f"{target_path}/Textures/Emissive",
            f"{target_path}/Textures/Other"
        ]
        
        # 创建每个文件夹
        for folder in folders:
            if not unreal.EditorAssetLibrary.does_directory_exist(folder):
                unreal.EditorAssetLibrary.make_directory(folder)
                unreal.log(f"已创建文件夹: {folder}")
    
    def organize_assets(self, assets, imported_assets, target_path):
        """
        组织导入的资产到适当的文件夹
        
        Args:
            assets (dict): 按类型分组的资产字典
            imported_assets (dict): 导入的资产映射 {资产文件路径: 导入的资产}
            target_path (str): 基础目标路径
        
        Returns:
            dict: 组织后的资产映射 {资产文件路径: 新的资产路径}
        """
        organized_assets = {}
        
        # 确保文件夹结构存在
        self.create_folder_structure(target_path)
        
        # 组织FBX资产
        for asset_file in assets.get("fbx", []):
            if asset_file.file_path not in imported_assets:
                continue
            
            imported_asset = imported_assets[asset_file.file_path]
            new_path = self._get_target_path_for_asset(asset_file, target_path)
            
            # 移动资产到目标路径
            if self._move_asset(imported_asset, new_path):
                organized_assets[asset_file.file_path] = new_path
        
        # 组织MA资产（如果有）
        for asset_file in assets.get("ma", []):
            if asset_file.file_path not in imported_assets:
                continue
            
            imported_asset = imported_assets[asset_file.file_path]
            new_path = self._get_target_path_for_asset(asset_file, target_path)
            
            # 移动资产到目标路径
            if self._move_asset(imported_asset, new_path):
                organized_assets[asset_file.file_path] = new_path
        
        return organized_assets
    
    def _get_target_path_for_asset(self, asset_file, target_path):
        """
        获取资产的目标路径
        
        Args:
            asset_file: 资产文件对象
            target_path (str): 基础目标路径
        
        Returns:
            str: 目标路径
        """
        # 根据资产类型确定目标文件夹
        if asset_file.asset_type == "static_mesh":
            folder = f"{target_path}/Meshes/StaticMeshes"
        elif asset_file.asset_type == "skeletal_mesh":
            folder = f"{target_path}/Meshes/SkeletalMeshes"
        elif asset_file.asset_type == "animation":
            folder = f"{target_path}/Animations"
        else:
            folder = target_path
        
        # 构建目标路径
        return f"{folder}/{asset_file.base_name}"
    
    def _move_asset(self, asset_path, new_path):
        """
        移动资产到新路径
        
        Args:
            asset_path (str): 当前资产路径
            new_path (str): 新的资产路径
        
        Returns:
            bool: 是否成功移动
        """
        try:
            # 检查源资产是否存在
            if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
                unreal.log_warning(f"资产不存在: {asset_path}")
                return False
            
            # 检查目标路径是否已存在
            if unreal.EditorAssetLibrary.does_asset_exist(new_path):
                unreal.log_warning(f"目标路径已存在资产: {new_path}")
                return False
            
            # 移动资产
            result = unreal.EditorAssetLibrary.rename_asset(asset_path, new_path)
            
            if result:
                unreal.log(f"已移动资产: {asset_path} -> {new_path}")
            else:
                unreal.log_warning(f"移动资产失败: {asset_path} -> {new_path}")
            
            return result
        except Exception as e:
            unreal.log_error(f"移动资产时出错: {e}")
            return False
    
    def organize_imported_assets(self, assets, imported_assets, imported_textures, created_materials, target_path):
        """
        组织所有导入的资产
        
        Args:
            assets (dict): 按类型分组的资产字典
            imported_assets (dict): 导入的资产映射 {资产文件路径: 导入的资产}
            imported_textures (dict): 导入的纹理映射 {纹理文件路径: 导入的纹理资产}
            created_materials (dict): 创建的材质实例映射 {基础名称: 材质实例}
            target_path (str): 基础目标路径
        
        Returns:
            dict: 组织后的所有资产
        """
        # 创建文件夹结构
        self.create_folder_structure(target_path)
        
        # 组织模型和动画
        organized_assets = self.organize_assets(assets, imported_assets, target_path)
        
        # 纹理已经在导入时组织到适当的文件夹
        # 材质已经在创建时组织到适当的文件夹
        
        return {
            "assets": organized_assets,
            "textures": imported_textures,
            "materials": created_materials
        }
