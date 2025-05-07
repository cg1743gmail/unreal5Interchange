#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件夹扫描模块
用于扫描文件夹并识别不同类型的资产文件

此模块提供了扫描文件夹、识别资产类型和分析资产关系的功能。
"""

import os
import re
import unreal

class AssetFile:
    """表示一个资产文件"""
    
    def __init__(self, file_path, asset_type, base_name=None):
        """
        初始化资产文件
        
        Args:
            file_path (str): 文件的完整路径
            asset_type (str): 资产类型 (fbx, texture, ma, etc.)
            base_name (str, optional): 资产的基础名称，用于关联相关资产
        """
        self.file_path = file_path
        self.asset_type = asset_type
        self.file_name = os.path.basename(file_path)
        self.directory = os.path.dirname(file_path)
        self.extension = os.path.splitext(file_path)[1].lower()
        
        # 如果没有提供基础名称，则从文件名中提取
        if base_name is None:
            self.base_name = self._extract_base_name(self.file_name)
        else:
            self.base_name = base_name
        
        # 初始化关联资产
        self.related_assets = []
    
    def _extract_base_name(self, file_name):
        """
        从文件名中提取基础名称
        
        Args:
            file_name (str): 文件名
        
        Returns:
            str: 基础名称
        """
        # 移除扩展名
        name_without_ext = os.path.splitext(file_name)[0]
        
        # 移除常见的后缀模式
        common_suffixes = [
            "_D", "_Diffuse", "_BaseColor", "_Albedo", "_Color",
            "_N", "_Normal", "_Norm",
            "_R", "_Roughness", "_Rough",
            "_M", "_Metallic", "_Metal",
            "_S", "_Specular", "_Spec",
            "_E", "_Emissive", "_Emission",
            "_SM", "_StaticMesh", "_Model",
            "_SK", "_SkeletalMesh", "_Character",
            "_Anim", "_Animation"
        ]
        
        for suffix in common_suffixes:
            if name_without_ext.endswith(suffix):
                return name_without_ext[:-len(suffix)]
        
        return name_without_ext
    
    def __str__(self):
        return f"{self.file_name} ({self.asset_type})"


class FolderScanner:
    """文件夹扫描类，用于扫描和分析资产文件夹"""
    
    def __init__(self, config=None):
        """
        初始化文件夹扫描器
        
        Args:
            config (dict, optional): 配置字典，包含文件名模式等设置
        """
        self.config = config or {}
        self.filename_patterns = self.config.get("filename_patterns", {})
    
    def scan_folder(self, folder_path):
        """
        扫描文件夹并识别资产
        
        Args:
            folder_path (str): 要扫描的文件夹路径
        
        Returns:
            dict: 按类型分组的资产文件字典
        """
        if not os.path.exists(folder_path):
            unreal.log_error(f"文件夹不存在: {folder_path}")
            return {}
        
        # 初始化结果字典
        assets = {
            "fbx": [],
            "ma": [],
            "textures": {
                "diffuse": [],
                "normal": [],
                "roughness": [],
                "metallic": [],
                "specular": [],
                "emissive": [],
                "other": []
            },
            "other": []
        }
        
        # 递归扫描文件夹
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1].lower()
                
                # 根据扩展名和文件名模式识别资产类型
                if extension == ".fbx":
                    asset_file = self._process_fbx_file(file_path)
                    assets["fbx"].append(asset_file)
                elif extension == ".ma":
                    asset_file = AssetFile(file_path, "ma")
                    assets["ma"].append(asset_file)
                elif extension in [".png", ".jpg", ".jpeg", ".tga", ".bmp", ".exr", ".hdr"]:
                    texture_type = self._identify_texture_type(file)
                    asset_file = AssetFile(file_path, f"texture_{texture_type}")
                    assets["textures"][texture_type].append(asset_file)
                else:
                    asset_file = AssetFile(file_path, "other")
                    assets["other"].append(asset_file)
        
        # 分析资产关系
        self._analyze_asset_relationships(assets)
        
        return assets
    
    def _process_fbx_file(self, file_path):
        """
        处理FBX文件，确定其类型（静态网格、骨骼网格或动画）
        
        Args:
            file_path (str): FBX文件路径
        
        Returns:
            AssetFile: 处理后的资产文件对象
        """
        file_name = os.path.basename(file_path)
        
        # 根据文件名判断FBX类型
        if self._match_pattern(file_name, self.filename_patterns.get("static_mesh", [])):
            fbx_type = "static_mesh"
        elif self._match_pattern(file_name, self.filename_patterns.get("skeletal_mesh", [])):
            fbx_type = "skeletal_mesh"
        elif self._match_pattern(file_name, self.filename_patterns.get("animation", [])):
            fbx_type = "animation"
        else:
            # 默认为静态网格
            fbx_type = "static_mesh"
        
        return AssetFile(file_path, fbx_type)
    
    def _identify_texture_type(self, file_name):
        """
        根据文件名识别纹理类型
        
        Args:
            file_name (str): 纹理文件名
        
        Returns:
            str: 纹理类型 (diffuse, normal, roughness, etc.)
        """
        # 检查文件名是否匹配已知的纹理类型模式
        if self._match_pattern(file_name, self.filename_patterns.get("diffuse", [])):
            return "diffuse"
        elif self._match_pattern(file_name, self.filename_patterns.get("normal", [])):
            return "normal"
        elif self._match_pattern(file_name, self.filename_patterns.get("roughness", [])):
            return "roughness"
        elif self._match_pattern(file_name, self.filename_patterns.get("metallic", [])):
            return "metallic"
        elif self._match_pattern(file_name, self.filename_patterns.get("specular", [])):
            return "specular"
        elif self._match_pattern(file_name, self.filename_patterns.get("emissive", [])):
            return "emissive"
        else:
            return "other"
    
    def _match_pattern(self, file_name, patterns):
        """
        检查文件名是否匹配给定的模式列表
        
        Args:
            file_name (str): 文件名
            patterns (list): 模式列表
        
        Returns:
            bool: 是否匹配
        """
        name_without_ext = os.path.splitext(file_name)[0]
        
        for pattern in patterns:
            if pattern in name_without_ext:
                return True
        
        return False
    
    def _analyze_asset_relationships(self, assets):
        """
        分析资产之间的关系，例如FBX模型和相关纹理
        
        Args:
            assets (dict): 按类型分组的资产字典
        """
        # 创建基础名称到资产的映射
        base_name_map = {}
        
        # 收集所有资产的基础名称
        for asset_type in ["fbx", "ma"]:
            for asset in assets[asset_type]:
                if asset.base_name not in base_name_map:
                    base_name_map[asset.base_name] = []
                base_name_map[asset.base_name].append(asset)
        
        # 收集纹理的基础名称
        for texture_type in assets["textures"]:
            for texture in assets["textures"][texture_type]:
                if texture.base_name not in base_name_map:
                    base_name_map[texture.base_name] = []
                base_name_map[texture.base_name].append(texture)
        
        # 建立关系
        for base_name, related_assets in base_name_map.items():
            if len(related_assets) > 1:
                # 如果有多个相关资产，则建立它们之间的关系
                for asset in related_assets:
                    asset.related_assets = [a for a in related_assets if a != asset]
