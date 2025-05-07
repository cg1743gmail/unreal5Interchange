#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unreal Engine 5.5 Asset Importer Tool
使用Interchange插件的Python资产导入工具

此工具用于高效、自动地将包含模型、纹理、FBX文件和MA文件的文件夹导入Unreal Engine 5.5，
根据不同资产类型进行分类处理，完成纹理链接、材质实例创建，并合理组织资产存储结构。

作者: Augment Agent
"""

import unreal
import os
import sys
import json
import re
import threading

# 导入自定义模块
try:
    from config_manager import ConfigManager
    from folder_scanner import FolderScanner
    from asset_processor import AssetProcessor
    from texture_processor import TextureProcessor
    from material_creator import MaterialCreator
    from asset_organizer import AssetOrganizer
except ImportError:
    unreal.log_error("无法导入自定义模块，请确保所有模块文件都在同一目录下")

class AssetImporterTool:
    """资产导入工具类"""
    
    def __init__(self):
        """初始化资产导入工具"""
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 初始化UI变量
        self.window = None
        self.folder_path_text = None
        self.progress_bar = None
        self.progress_text = None
        self.log_text = None
        
        # 初始化选项变量
        self.process_textures_checkbox = None
        self.create_materials_checkbox = None
        self.organize_folders_checkbox = None
        self.compress_textures_checkbox = None
        self.target_path_text = None
        self.material_template_text = None
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建用户界面"""
        # 创建窗口
        self.window = unreal.PythonBPLib.create_window(
            "UE5.5 资产导入工具", 
            "资产导入工具", 
            800, 600
        )
        
        # 创建垂直布局
        main_layout = unreal.PythonBPLib.create_vertical_box()
        unreal.PythonBPLib.set_content(self.window, main_layout)
        
        # 创建文件夹选择区域
        folder_group = self._create_group_box("文件夹选择")
        unreal.PythonBPLib.add_slot(main_layout, folder_group)
        
        folder_layout = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(folder_group, folder_layout)
        
        self.folder_path_text = unreal.PythonBPLib.create_editable_text_box()
        unreal.PythonBPLib.set_text(self.folder_path_text, "")
        unreal.PythonBPLib.set_is_read_only(self.folder_path_text, True)
        unreal.PythonBPLib.set_hint_text(self.folder_path_text, "选择包含资产的文件夹...")
        unreal.PythonBPLib.add_slot(folder_layout, self.folder_path_text, 1.0)
        
        browse_button = unreal.PythonBPLib.create_button("浏览...")
        unreal.PythonBPLib.set_on_clicked(browse_button, self._on_browse_clicked)
        unreal.PythonBPLib.add_slot(folder_layout, browse_button)
        
        # 创建导入选项区域
        options_group = self._create_group_box("导入选项")
        unreal.PythonBPLib.add_slot(main_layout, options_group)
        
        options_layout = unreal.PythonBPLib.create_vertical_box()
        unreal.PythonBPLib.add_slot(options_group, options_layout)
        
        # 添加选项
        self._create_import_options(options_layout)
        
        # 创建进度显示区域
        progress_group = self._create_group_box("导入进度")
        unreal.PythonBPLib.add_slot(main_layout, progress_group)
        
        progress_layout = unreal.PythonBPLib.create_vertical_box()
        unreal.PythonBPLib.add_slot(progress_group, progress_layout)
        
        self.progress_text = unreal.PythonBPLib.create_text_block("准备就绪")
        unreal.PythonBPLib.add_slot(progress_layout, self.progress_text)
        
        self.progress_bar = unreal.PythonBPLib.create_progress_bar()
        unreal.PythonBPLib.set_percent(self.progress_bar, 0.0)
        unreal.PythonBPLib.add_slot(progress_layout, self.progress_bar)
        
        # 创建日志输出区域
        log_group = self._create_group_box("日志输出")
        unreal.PythonBPLib.add_slot(main_layout, log_group, 1.0)
        
        self.log_text = unreal.PythonBPLib.create_multi_line_editable_text_box()
        unreal.PythonBPLib.set_is_read_only(self.log_text, True)
        unreal.PythonBPLib.add_slot(log_group, self.log_text, 1.0)
        
        # 创建按钮区域
        button_layout = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(main_layout, button_layout)
        
        self.import_button = unreal.PythonBPLib.create_button("开始导入")
        unreal.PythonBPLib.set_on_clicked(self.import_button, self._on_import_clicked)
        unreal.PythonBPLib.set_is_enabled(self.import_button, False)
        unreal.PythonBPLib.add_slot(button_layout, self.import_button)
        
        save_config_button = unreal.PythonBPLib.create_button("保存配置")
        unreal.PythonBPLib.set_on_clicked(save_config_button, self._on_save_config_clicked)
        unreal.PythonBPLib.add_slot(button_layout, save_config_button)
        
        load_config_button = unreal.PythonBPLib.create_button("加载配置")
        unreal.PythonBPLib.set_on_clicked(load_config_button, self._on_load_config_clicked)
        unreal.PythonBPLib.add_slot(button_layout, load_config_button)
        
        # 初始化日志
        self.log("资产导入工具已启动")
    
    def _create_group_box(self, title):
        """
        创建分组框
        
        Args:
            title (str): 分组标题
        
        Returns:
            object: 分组框对象
        """
        group_box = unreal.PythonBPLib.create_group_box()
        unreal.PythonBPLib.set_group_box_title(group_box, title)
        return group_box
    
    def _create_import_options(self, parent):
        """
        创建导入选项控件
        
        Args:
            parent: 父控件
        """
        # 第一行选项
        row1 = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(parent, row1)
        
        self.process_textures_checkbox = unreal.PythonBPLib.create_check_box("自动处理纹理")
        unreal.PythonBPLib.set_is_checked(self.process_textures_checkbox, self.config.get("process_textures", True))
        unreal.PythonBPLib.add_slot(row1, self.process_textures_checkbox)
        
        self.create_materials_checkbox = unreal.PythonBPLib.create_check_box("创建材质实例")
        unreal.PythonBPLib.set_is_checked(self.create_materials_checkbox, self.config.get("create_materials", True))
        unreal.PythonBPLib.add_slot(row1, self.create_materials_checkbox)
        
        # 第二行选项
        row2 = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(parent, row2)
        
        self.organize_folders_checkbox = unreal.PythonBPLib.create_check_box("组织文件夹结构")
        unreal.PythonBPLib.set_is_checked(self.organize_folders_checkbox, self.config.get("organize_folders", True))
        unreal.PythonBPLib.add_slot(row2, self.organize_folders_checkbox)
        
        self.compress_textures_checkbox = unreal.PythonBPLib.create_check_box("压缩纹理")
        unreal.PythonBPLib.set_is_checked(self.compress_textures_checkbox, self.config.get("compress_textures", True))
        unreal.PythonBPLib.add_slot(row2, self.compress_textures_checkbox)
        
        # 第三行选项
        row3 = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(parent, row3)
        
        target_path_label = unreal.PythonBPLib.create_text_block("导入目标路径:")
        unreal.PythonBPLib.add_slot(row3, target_path_label)
        
        self.target_path_text = unreal.PythonBPLib.create_editable_text_box()
        unreal.PythonBPLib.set_text(self.target_path_text, self.config.get("target_path", "/Game/ImportedAssets"))
        unreal.PythonBPLib.add_slot(row3, self.target_path_text, 1.0)
        
        # 第四行选项
        row4 = unreal.PythonBPLib.create_horizontal_box()
        unreal.PythonBPLib.add_slot(parent, row4)
        
        material_template_label = unreal.PythonBPLib.create_text_block("材质模板路径:")
        unreal.PythonBPLib.add_slot(row4, material_template_label)
        
        self.material_template_text = unreal.PythonBPLib.create_editable_text_box()
        unreal.PythonBPLib.set_text(self.material_template_text, self.config.get("material_template", "/Game/MaterialTemplates/M_Standard"))
        unreal.PythonBPLib.add_slot(row4, self.material_template_text, 1.0)
    
    def _on_browse_clicked(self):
        """浏览按钮点击事件"""
        folder = unreal.PythonBPLib.open_directory_dialog("选择资产文件夹", "")
        if folder:
            unreal.PythonBPLib.set_text(self.folder_path_text, folder)
            unreal.PythonBPLib.set_is_enabled(self.import_button, True)
            self.log(f"已选择文件夹: {folder}")
    
    def _on_save_config_clicked(self):
        """保存配置按钮点击事件"""
        config = {
            "process_textures": unreal.PythonBPLib.is_checked(self.process_textures_checkbox),
            "create_materials": unreal.PythonBPLib.is_checked(self.create_materials_checkbox),
            "organize_folders": unreal.PythonBPLib.is_checked(self.organize_folders_checkbox),
            "compress_textures": unreal.PythonBPLib.is_checked(self.compress_textures_checkbox),
            "target_path": unreal.PythonBPLib.get_text(self.target_path_text),
            "material_template": unreal.PythonBPLib.get_text(self.material_template_text)
        }
        
        file_path = unreal.PythonBPLib.save_file_dialog("保存配置", "", "*.json")
        if file_path:
            self.config_manager.save_config(config, file_path)
            self.log(f"配置已保存到: {file_path}")
    
    def _on_load_config_clicked(self):
        """加载配置按钮点击事件"""
        file_path = unreal.PythonBPLib.open_file_dialog("加载配置", "", "*.json")
        if file_path:
            config = self.config_manager.load_config(file_path)
            self._update_ui_from_config(config)
            self.log(f"已加载配置: {file_path}")
    
    def _update_ui_from_config(self, config):
        """
        根据配置更新UI
        
        Args:
            config (dict): 配置字典
        """
        unreal.PythonBPLib.set_is_checked(self.process_textures_checkbox, config.get("process_textures", True))
        unreal.PythonBPLib.set_is_checked(self.create_materials_checkbox, config.get("create_materials", True))
        unreal.PythonBPLib.set_is_checked(self.organize_folders_checkbox, config.get("organize_folders", True))
        unreal.PythonBPLib.set_is_checked(self.compress_textures_checkbox, config.get("compress_textures", True))
        unreal.PythonBPLib.set_text(self.target_path_text, config.get("target_path", "/Game/ImportedAssets"))
        unreal.PythonBPLib.set_text(self.material_template_text, config.get("material_template", "/Game/MaterialTemplates/M_Standard"))
    
    def _on_import_clicked(self):
        """导入按钮点击事件"""
        # 获取当前设置
        source_folder = unreal.PythonBPLib.get_text(self.folder_path_text)
        target_path = unreal.PythonBPLib.get_text(self.target_path_text)
        
        if not source_folder:
            unreal.PythonBPLib.show_message_dialog("错误", "请选择源文件夹", "确定")
            return
        
        # 收集当前配置
        config = {
            "process_textures": unreal.PythonBPLib.is_checked(self.process_textures_checkbox),
            "create_materials": unreal.PythonBPLib.is_checked(self.create_materials_checkbox),
            "organize_folders": unreal.PythonBPLib.is_checked(self.organize_folders_checkbox),
            "compress_textures": unreal.PythonBPLib.is_checked(self.compress_textures_checkbox),
            "target_path": target_path,
            "material_template": unreal.PythonBPLib.get_text(self.material_template_text)
        }
        
        self.log("开始导入过程...")
        self.log(f"源文件夹: {source_folder}")
        self.log(f"目标路径: {target_path}")
        
        # 禁用导入按钮，防止重复点击
        unreal.PythonBPLib.set_is_enabled(self.import_button, False)
        
        # 创建一个单独的线程来执行导入过程
        import_thread = threading.Thread(target=self._import_process, args=(source_folder, config))
        import_thread.daemon = True
        import_thread.start()
    
    def _import_process(self, source_folder, config):
        """
        执行导入过程
        
        Args:
            source_folder (str): 源文件夹路径
            config (dict): 配置字典
        """
        try:
            # 初始化进度条
            self.update_progress(0, "扫描文件夹...")
            
            # 1. 扫描文件夹
            folder_scanner = FolderScanner(config)
            assets = folder_scanner.scan_folder(source_folder)
            
            # 更新进度
            self.update_progress(10, "分析资产...")
            
            # 记录找到的资产数量
            fbx_count = len(assets.get("fbx", []))
            ma_count = len(assets.get("ma", []))
            texture_count = sum(len(textures) for textures in assets.get("textures", {}).values())
            
            self.log(f"找到 {fbx_count} 个FBX文件, {ma_count} 个MA文件, {texture_count} 个纹理文件")
            
            # 2. 创建文件夹结构
            if config.get("organize_folders", True):
                self.update_progress(15, "创建文件夹结构...")
                asset_organizer = AssetOrganizer(config)
                asset_organizer.create_folder_structure(config["target_path"])
            
            # 更新进度
            self.update_progress(20, "导入纹理...")
            
            # 3. 导入纹理
            imported_textures = {}
            if config.get("process_textures", True) and texture_count > 0:
                texture_processor = TextureProcessor(config)
                imported_textures = texture_processor.organize_textures(assets.get("textures", {}), config["target_path"])
                self.log(f"已导入 {len(imported_textures)} 个纹理")
            
            # 更新进度
            self.update_progress(50, "导入FBX和MA文件...")
            
            # 4. 导入FBX和MA文件
            imported_assets = {}
            asset_processor = AssetProcessor(config)
            
            # 导入FBX文件
            fbx_progress_step = 30 / max(fbx_count, 1)
            for i, asset_file in enumerate(assets.get("fbx", [])):
                self.update_progress(50 + int((i + 0.5) * fbx_progress_step), f"导入FBX: {asset_file.file_name}")
                imported_asset = asset_processor.import_asset(asset_file, config["target_path"])
                if imported_asset:
                    imported_assets[asset_file.file_path] = imported_asset
                    self.log(f"已导入: {asset_file.file_name}")
                else:
                    self.log(f"导入失败: {asset_file.file_name}")
            
            # 导入MA文件
            ma_progress_step = 10 / max(ma_count, 1)
            for i, asset_file in enumerate(assets.get("ma", [])):
                self.update_progress(80 + int((i + 0.5) * ma_progress_step), f"导入MA: {asset_file.file_name}")
                imported_asset = asset_processor.import_maya_file(asset_file, config["target_path"])
                if imported_asset:
                    imported_assets[asset_file.file_path] = imported_asset
                    self.log(f"已导入: {asset_file.file_name}")
                else:
                    self.log(f"导入失败: {asset_file.file_name}")
            
            self.log(f"已导入 {len(imported_assets)} 个模型")
            
            # 更新进度
            self.update_progress(90, "创建材质...")
            
            # 5. 创建材质
            created_materials = {}
            if config.get("create_materials", True):
                material_creator = MaterialCreator(config)
                created_materials = material_creator.create_materials_for_assets(
                    assets, imported_assets, imported_textures, config["target_path"]
                )
                self.log(f"已创建 {len(created_materials)} 个材质实例")
            
            # 更新进度
            self.update_progress(95, "组织资产...")
            
            # 6. 组织资产
            if config.get("organize_folders", True):
                asset_organizer = AssetOrganizer(config)
                organized_assets = asset_organizer.organize_imported_assets(
                    assets, imported_assets, imported_textures, created_materials, config["target_path"]
                )
                self.log("已组织所有资产")
            
            # 完成
            self.update_progress(100, "导入完成")
            self.log("资产导入过程已完成")
            
        except Exception as e:
            self.log(f"导入过程中出错: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # 重新启用导入按钮
            unreal.PythonBPLib.set_is_enabled(self.import_button, True)
    
    def update_progress(self, value, text):
        """
        更新进度条和进度文本
        
        Args:
            value (int): 进度值 (0-100)
            text (str): 进度文本
        """
        unreal.PythonBPLib.set_percent(self.progress_bar, value / 100.0)
        unreal.PythonBPLib.set_text(self.progress_text, text)
    
    def log(self, message):
        """
        添加消息到日志区域
        
        Args:
            message (str): 日志消息
        """
        current_text = unreal.PythonBPLib.get_text(self.log_text)
        new_text = f"{current_text}\n{message}" if current_text else message
        unreal.PythonBPLib.set_text(self.log_text, new_text)
        unreal.log(message)  # 同时输出到Unreal日志

def main():
    """主函数"""
    tool = AssetImporterTool()

if __name__ == "__main__":
    main()
