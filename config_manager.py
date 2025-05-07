#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块
用于管理资产导入工具的配置设置

此模块提供了加载、保存和管理配置的功能，支持默认配置和用户自定义配置。
"""

import os
import json
import unreal

class ConfigManager:
    """配置管理类，处理导入工具的配置"""
    
    def __init__(self, default_config_path=None):
        """
        初始化配置管理器
        
        Args:
            default_config_path (str, optional): 默认配置文件路径。如果为None，使用内置默认配置。
        """
        self.default_config_path = default_config_path
        self.default_config = self._get_default_config()
    
    def _get_default_config(self):
        """
        获取默认配置
        
        Returns:
            dict: 默认配置字典
        """
        # 如果指定了默认配置文件且文件存在，则从文件加载
        if self.default_config_path and os.path.exists(self.default_config_path):
            try:
                with open(self.default_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                unreal.log_warning(f"无法加载默认配置文件: {e}")
                return self._create_default_config()
        else:
            # 否则使用内置默认配置
            return self._create_default_config()
    
    def _create_default_config(self):
        """
        创建内置默认配置
        
        Returns:
            dict: 默认配置字典
        """
        return {
            # 基本设置
            "target_path": "/Game/ImportedAssets",
            "organize_folders": True,
            
            # 纹理设置
            "process_textures": True,
            "compress_textures": True,
            "texture_group": "World",
            "texture_settings": {
                "diffuse": {
                    "compression_settings": "UserInterface2D",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": True
                },
                "normal": {
                    "compression_settings": "Normalmap",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": False
                },
                "roughness": {
                    "compression_settings": "Masks",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": False
                },
                "metallic": {
                    "compression_settings": "Masks",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": False
                },
                "specular": {
                    "compression_settings": "Masks",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": False
                },
                "emissive": {
                    "compression_settings": "UserInterface2D",
                    "mip_gen_settings": "FromTextureGroup",
                    "srgb": True
                }
            },
            
            # 材质设置
            "create_materials": True,
            "material_template": "/Game/MaterialTemplates/M_Standard",
            "material_instance_suffix": "_Inst",
            
            # FBX导入设置
            "fbx_import": {
                "static_mesh": {
                    "generate_lightmap_uvs": True,
                    "combine_meshes": False,
                    "auto_generate_collision": True,
                    "remove_degenerates": True,
                    "build_nanite": True
                },
                "skeletal_mesh": {
                    "import_morph_targets": True,
                    "import_meshes_in_bone_hierarchy": True,
                    "preserve_smoothing_groups": True,
                    "import_animations": True
                },
                "animation": {
                    "import_animations": True,
                    "animation_length": "ExportedTime",
                    "frame_import_range": [0, 0],
                    "use_default_sample_rate": True,
                    "custom_sample_rate": 30
                }
            },
            
            # 文件名模式设置
            "filename_patterns": {
                "static_mesh": ["_SM", "_StaticMesh", "_Model"],
                "skeletal_mesh": ["_SK", "_SkeletalMesh", "_Character"],
                "animation": ["_Anim", "_Animation"],
                "diffuse": ["_D", "_Diffuse", "_BaseColor", "_Albedo", "_Color"],
                "normal": ["_N", "_Normal", "_Norm"],
                "roughness": ["_R", "_Roughness", "_Rough"],
                "metallic": ["_M", "_Metallic", "_Metal"],
                "specular": ["_S", "_Specular", "_Spec"],
                "emissive": ["_E", "_Emissive", "_Emission"]
            }
        }
    
    def load_config(self, config_path=None):
        """
        加载配置文件
        
        Args:
            config_path (str, optional): 配置文件路径。如果为None，返回默认配置。
        
        Returns:
            dict: 配置字典
        """
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    
                # 合并用户配置和默认配置，确保所有必要的键都存在
                config = self.default_config.copy()
                self._deep_update(config, user_config)
                return config
            except Exception as e:
                unreal.log_warning(f"无法加载配置文件 {config_path}: {e}")
                return self.default_config
        else:
            return self.default_config
    
    def save_config(self, config, config_path):
        """
        保存配置到文件
        
        Args:
            config (dict): 要保存的配置字典
            config_path (str): 保存的文件路径
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            unreal.log_warning(f"无法保存配置到 {config_path}: {e}")
            return False
    
    def _deep_update(self, d, u):
        """
        深度更新字典
        
        Args:
            d (dict): 要更新的目标字典
            u (dict): 包含更新内容的字典
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
