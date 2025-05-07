#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FBX调试模块
用于在导入前分析和调试FBX文件

此模块提供了检查FBX文件的各种信息，包括静态物体标识、碰撞信息和材质槽完整性。
"""

import os
import unreal
import re

class FbxDebugger:
    """FBX调试类，用于分析FBX文件"""
    
    def __init__(self, config=None):
        """
        初始化FBX调试器
        
        Args:
            config (dict, optional): 配置字典
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
    
    def debug_fbx(self, fbx_file_path):
        """
        调试FBX文件
        
        Args:
            fbx_file_path (str): FBX文件路径
        
        Returns:
            dict: 调试结果
        """
        if not os.path.exists(fbx_file_path):
            return {"error": f"文件不存在: {fbx_file_path}"}
        
        if not fbx_file_path.lower().endswith('.fbx'):
            return {"error": f"不是FBX文件: {fbx_file_path}"}
        
        # 创建临时导入路径
        temp_import_path = "/Temp/FbxDebug"
        
        # 确保临时路径不存在
        if self.editor_asset_subsystem.does_directory_exist(temp_import_path):
            self.editor_asset_subsystem.delete_directory(temp_import_path)
        
        # 创建临时路径
        self.editor_asset_subsystem.make_directory(temp_import_path)
        
        # 导入FBX文件进行分析
        imported_asset = self._import_fbx_for_debug(fbx_file_path, temp_import_path)
        
        if not imported_asset:
            return {"error": f"导入FBX文件失败: {fbx_file_path}"}
        
        # 分析结果
        result = {
            "file_path": fbx_file_path,
            "file_name": os.path.basename(fbx_file_path),
            "is_static_mesh": self._is_static_mesh(fbx_file_path),
            "has_collision": self._check_collision(imported_asset),
            "material_slots": self._check_material_slots(imported_asset)
        }
        
        # 清理临时导入的资产
        self.editor_asset_subsystem.delete_directory(temp_import_path)
        
        return result
    
    def _import_fbx_for_debug(self, fbx_file_path, target_path):
        """
        导入FBX文件用于调试
        
        Args:
            fbx_file_path (str): FBX文件路径
            target_path (str): 导入目标路径
        
        Returns:
            str: 导入的资产路径
        """
        try:
            # 创建临时管道路径
            transient_path = "/Interchange/Pipelines/Transient/"
            transient_pipeline_path = transient_path + "DebugPipeline"
            
            # 删除可能存在的临时管道
            self.editor_asset_subsystem.delete_directory(transient_path)
            
            # 复制默认管道
            pipeline = self.editor_asset_subsystem.duplicate_asset(
                "/Interchange/Pipelines/DefaultAssetsPipeline", 
                transient_pipeline_path
            )
            
            # 创建源数据
            source_data = unreal.InterchangeManager.create_source_data(fbx_file_path)
            
            # 创建导入参数
            import_asset_parameters = unreal.ImportAssetParameters()
            import_asset_parameters.is_automated = True
            
            # 添加配置的管道
            import_asset_parameters.override_pipelines.append(
                unreal.SoftObjectPath(transient_pipeline_path + ".DebugPipeline")
            )
            
            # 获取Interchange管理器并导入资产
            interchange_manager = unreal.InterchangeManager.get_interchange_manager_scripted()
            result = interchange_manager.import_asset(target_path, source_data, import_asset_parameters)
            
            # 清理临时管道
            self.editor_asset_subsystem.delete_directory(transient_path)
            
            return result
        except Exception as e:
            unreal.log_error(f"导入FBX文件进行调试时出错: {e}")
            return None
    
    def _is_static_mesh(self, fbx_file_path):
        """
        检查FBX文件是否为静态网格
        
        Args:
            fbx_file_path (str): FBX文件路径
        
        Returns:
            bool: 是否为静态网格
        """
        # 检查文件名是否包含静态网格标识
        file_name = os.path.basename(fbx_file_path)
        
        # 检查是否包含SM_前缀
        if file_name.startswith("SM_") or "_SM_" in file_name:
            return True
        
        # 检查配置中的静态网格模式
        filename_patterns = self.config.get("filename_patterns", {})
        static_mesh_patterns = filename_patterns.get("static_mesh", ["_SM", "_StaticMesh", "_Model"])
        
        for pattern in static_mesh_patterns:
            if pattern in file_name:
                return True
        
        # 默认情况下，如果没有明确标识，假设为静态网格
        return True
    
    def _check_collision(self, asset_path):
        """
        检查资产是否包含碰撞信息
        
        Args:
            asset_path (str): 资产路径
        
        Returns:
            dict: 碰撞信息
        """
        try:
            # 加载资产
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            
            if not asset:
                return {"has_collision": False, "details": "无法加载资产"}
            
            # 检查是否为静态网格
            if isinstance(asset, unreal.StaticMesh):
                # 检查是否有UCX_前缀的碰撞体
                has_ucx_collision = False
                
                # 获取源模型数据
                source_models = asset.get_editor_property("source_models")
                if source_models and len(source_models) > 0:
                    # 检查是否有自定义碰撞
                    has_custom_collision = asset.get_editor_property("custom_collision")
                    
                    # 检查是否有简单碰撞
                    collision_complexity = asset.get_editor_property("collision_complexity")
                    has_simple_collision = collision_complexity != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                    
                    return {
                        "has_collision": has_custom_collision or has_simple_collision or has_ucx_collision,
                        "has_custom_collision": has_custom_collision,
                        "has_simple_collision": has_simple_collision,
                        "has_ucx_collision": has_ucx_collision,
                        "collision_complexity": str(collision_complexity)
                    }
            
            return {"has_collision": False, "details": "不是静态网格"}
        except Exception as e:
            unreal.log_error(f"检查碰撞信息时出错: {e}")
            return {"has_collision": False, "error": str(e)}
    
    def _check_material_slots(self, asset_path):
        """
        检查资产的材质槽信息
        
        Args:
            asset_path (str): 资产路径
        
        Returns:
            dict: 材质槽信息
        """
        try:
            # 加载资产
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            
            if not asset:
                return {"has_materials": False, "details": "无法加载资产"}
            
            material_slots = []
            missing_materials = []
            
            # 检查是否为静态网格或骨骼网格
            if isinstance(asset, unreal.StaticMesh):
                # 获取材质槽数量
                num_sections = asset.get_num_sections(0)
                
                for i in range(num_sections):
                    # 获取材质槽名称
                    slot_name = asset.get_material_slot_name(i)
                    
                    # 获取材质
                    material = asset.get_material(i)
                    
                    material_slots.append({
                        "index": i,
                        "name": slot_name,
                        "has_material": material is not None
                    })
                    
                    if material is None:
                        missing_materials.append(slot_name)
            
            elif isinstance(asset, unreal.SkeletalMesh):
                # 获取材质槽数量
                for i in range(asset.get_num_lod_models()):
                    for j in range(asset.get_num_sections(i)):
                        # 获取材质槽名称
                        slot_name = asset.get_material_slot_name(j)
                        
                        # 获取材质
                        material = asset.get_material(j)
                        
                        material_slots.append({
                            "lod": i,
                            "index": j,
                            "name": slot_name,
                            "has_material": material is not None
                        })
                        
                        if material is None:
                            missing_materials.append(slot_name)
            
            return {
                "has_materials": len(material_slots) > 0,
                "total_slots": len(material_slots),
                "missing_materials": len(missing_materials),
                "material_slots": material_slots,
                "missing_material_slots": missing_materials
            }
        except Exception as e:
            unreal.log_error(f"检查材质槽信息时出错: {e}")
            return {"has_materials": False, "error": str(e)}
