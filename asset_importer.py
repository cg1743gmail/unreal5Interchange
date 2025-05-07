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
from PySide2 import QtCore, QtWidgets, QtGui

# 导入自定义模块
try:
    from config_manager import ConfigManager
    from folder_scanner import FolderScanner
    from asset_processor import AssetProcessor
    from texture_processor import TextureProcessor
    from material_creator import MaterialCreator
    from asset_organizer import AssetOrganizer
except ImportError:
    print("无法导入自定义模块，请确保所有模块文件都在同一目录下")

class AssetImporterGUI(QtWidgets.QMainWindow):
    """资产导入工具的主GUI类"""

    def __init__(self):
        super(AssetImporterGUI, self).__init__()

        # 设置窗口属性
        self.setWindowTitle("UE5.5 资产导入工具")
        self.setMinimumSize(800, 600)

        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # 创建主界面
        self.setup_ui()

        # 初始化日志
        self.log("资产导入工具已启动")

    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # 创建文件夹选择区域
        folder_group = QtWidgets.QGroupBox("文件夹选择")
        folder_layout = QtWidgets.QHBoxLayout()

        self.folder_path = QtWidgets.QLineEdit()
        self.folder_path.setReadOnly(True)
        self.folder_path.setPlaceholderText("选择包含资产的文件夹...")

        browse_button = QtWidgets.QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_folder)

        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(browse_button)
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)

        # 创建导入选项区域
        options_group = QtWidgets.QGroupBox("导入选项")
        options_layout = QtWidgets.QGridLayout()

        # 添加导入选项
        self.create_import_options(options_layout)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # 创建进度显示区域
        progress_group = QtWidgets.QGroupBox("导入进度")
        progress_layout = QtWidgets.QVBoxLayout()

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.progress_label = QtWidgets.QLabel("准备就绪")

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # 创建日志输出区域
        log_group = QtWidgets.QGroupBox("日志输出")
        log_layout = QtWidgets.QVBoxLayout()

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # 创建按钮区域
        button_layout = QtWidgets.QHBoxLayout()

        self.import_button = QtWidgets.QPushButton("开始导入")
        self.import_button.clicked.connect(self.start_import)
        self.import_button.setEnabled(False)

        self.save_config_button = QtWidgets.QPushButton("保存配置")
        self.save_config_button.clicked.connect(self.save_config)

        self.load_config_button = QtWidgets.QPushButton("加载配置")
        self.load_config_button.clicked.connect(self.load_config)

        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.save_config_button)
        button_layout.addWidget(self.load_config_button)

        main_layout.addLayout(button_layout)

    def create_import_options(self, layout):
        """创建导入选项控件"""
        # 自动处理纹理选项
        self.process_textures = QtWidgets.QCheckBox("自动处理纹理")
        self.process_textures.setChecked(self.config.get("process_textures", True))
        layout.addWidget(self.process_textures, 0, 0)

        # 创建材质实例选项
        self.create_materials = QtWidgets.QCheckBox("创建材质实例")
        self.create_materials.setChecked(self.config.get("create_materials", True))
        layout.addWidget(self.create_materials, 0, 1)

        # 组织文件夹选项
        self.organize_folders = QtWidgets.QCheckBox("组织文件夹结构")
        self.organize_folders.setChecked(self.config.get("organize_folders", True))
        layout.addWidget(self.organize_folders, 1, 0)

        # 纹理压缩选项
        self.compress_textures = QtWidgets.QCheckBox("压缩纹理")
        self.compress_textures.setChecked(self.config.get("compress_textures", True))
        layout.addWidget(self.compress_textures, 1, 1)

        # 目标路径
        layout.addWidget(QtWidgets.QLabel("导入目标路径:"), 2, 0)
        self.target_path = QtWidgets.QLineEdit()
        self.target_path.setText(self.config.get("target_path", "/Game/ImportedAssets"))
        layout.addWidget(self.target_path, 2, 1)

        # 材质模板路径
        layout.addWidget(QtWidgets.QLabel("材质模板路径:"), 3, 0)
        self.material_template = QtWidgets.QLineEdit()
        self.material_template.setText(self.config.get("material_template", "/Game/MaterialTemplates/M_Standard"))
        layout.addWidget(self.material_template, 3, 1)

    def browse_folder(self):
        """浏览并选择文件夹"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择资产文件夹")
        if folder:
            self.folder_path.setText(folder)
            self.import_button.setEnabled(True)
            self.log(f"已选择文件夹: {folder}")

    def save_config(self):
        """保存当前配置"""
        config = {
            "process_textures": self.process_textures.isChecked(),
            "create_materials": self.create_materials.isChecked(),
            "organize_folders": self.organize_folders.isChecked(),
            "compress_textures": self.compress_textures.isChecked(),
            "target_path": self.target_path.text(),
            "material_template": self.material_template.text()
        }

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存配置", "", "JSON文件 (*.json)"
        )

        if file_path:
            self.config_manager.save_config(config, file_path)
            self.log(f"配置已保存到: {file_path}")

    def load_config(self):
        """加载配置文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "加载配置", "", "JSON文件 (*.json)"
        )

        if file_path:
            config = self.config_manager.load_config(file_path)
            self.update_ui_from_config(config)
            self.log(f"已加载配置: {file_path}")

    def update_ui_from_config(self, config):
        """根据配置更新UI"""
        self.process_textures.setChecked(config.get("process_textures", True))
        self.create_materials.setChecked(config.get("create_materials", True))
        self.organize_folders.setChecked(config.get("organize_folders", True))
        self.compress_textures.setChecked(config.get("compress_textures", True))
        self.target_path.setText(config.get("target_path", "/Game/ImportedAssets"))
        self.material_template.setText(config.get("material_template", "/Game/MaterialTemplates/M_Standard"))

    def start_import(self):
        """开始导入过程"""
        # 获取当前设置
        source_folder = self.folder_path.text()
        target_path = self.target_path.text()

        if not source_folder:
            self.log("错误: 请选择源文件夹")
            return

        # 收集当前配置
        config = {
            "process_textures": self.process_textures.isChecked(),
            "create_materials": self.create_materials.isChecked(),
            "organize_folders": self.organize_folders.isChecked(),
            "compress_textures": self.compress_textures.isChecked(),
            "target_path": target_path,
            "material_template": self.material_template.text()
        }

        self.log("开始导入过程...")
        self.log(f"源文件夹: {source_folder}")
        self.log(f"目标路径: {target_path}")

        try:
            # 禁用导入按钮，防止重复点击
            self.import_button.setEnabled(False)

            # 初始化进度条
            self.progress_bar.setValue(0)
            self.progress_label.setText("扫描文件夹...")

            # 1. 扫描文件夹
            folder_scanner = FolderScanner(config)
            assets = folder_scanner.scan_folder(source_folder)

            # 更新进度
            self.progress_bar.setValue(10)
            self.progress_label.setText("分析资产...")

            # 记录找到的资产数量
            fbx_count = len(assets.get("fbx", []))
            ma_count = len(assets.get("ma", []))
            texture_count = sum(len(textures) for textures in assets.get("textures", {}).values())

            self.log(f"找到 {fbx_count} 个FBX文件, {ma_count} 个MA文件, {texture_count} 个纹理文件")

            # 2. 创建文件夹结构
            if config.get("organize_folders", True):
                self.progress_label.setText("创建文件夹结构...")
                asset_organizer = AssetOrganizer(config)
                asset_organizer.create_folder_structure(target_path)

            # 更新进度
            self.progress_bar.setValue(20)
            self.progress_label.setText("导入纹理...")

            # 3. 导入纹理
            imported_textures = {}
            if config.get("process_textures", True) and texture_count > 0:
                texture_processor = TextureProcessor(config)
                imported_textures = texture_processor.organize_textures(assets.get("textures", {}), target_path)
                self.log(f"已导入 {len(imported_textures)} 个纹理")

            # 更新进度
            self.progress_bar.setValue(50)
            self.progress_label.setText("导入FBX和MA文件...")

            # 4. 导入FBX和MA文件
            imported_assets = {}
            asset_processor = AssetProcessor(config)

            # 导入FBX文件
            fbx_progress_step = 30 / max(fbx_count, 1)
            for i, asset_file in enumerate(assets.get("fbx", [])):
                self.progress_label.setText(f"导入FBX: {asset_file.file_name}")
                imported_asset = asset_processor.import_asset(asset_file, target_path)
                if imported_asset:
                    imported_assets[asset_file.file_path] = imported_asset
                    self.log(f"已导入: {asset_file.file_name}")
                else:
                    self.log(f"导入失败: {asset_file.file_name}")

                # 更新进度
                self.progress_bar.setValue(50 + int((i + 1) * fbx_progress_step))

            # 导入MA文件
            ma_progress_step = 10 / max(ma_count, 1)
            for i, asset_file in enumerate(assets.get("ma", [])):
                self.progress_label.setText(f"导入MA: {asset_file.file_name}")
                imported_asset = asset_processor.import_maya_file(asset_file, target_path)
                if imported_asset:
                    imported_assets[asset_file.file_path] = imported_asset
                    self.log(f"已导入: {asset_file.file_name}")
                else:
                    self.log(f"导入失败: {asset_file.file_name}")

                # 更新进度
                self.progress_bar.setValue(80 + int((i + 1) * ma_progress_step))

            self.log(f"已导入 {len(imported_assets)} 个模型")

            # 更新进度
            self.progress_bar.setValue(90)
            self.progress_label.setText("创建材质...")

            # 5. 创建材质
            created_materials = {}
            if config.get("create_materials", True):
                material_creator = MaterialCreator(config)
                created_materials = material_creator.create_materials_for_assets(
                    assets, imported_assets, imported_textures, target_path
                )
                self.log(f"已创建 {len(created_materials)} 个材质实例")

            # 更新进度
            self.progress_bar.setValue(95)
            self.progress_label.setText("组织资产...")

            # 6. 组织资产
            if config.get("organize_folders", True):
                asset_organizer = AssetOrganizer(config)
                organized_assets = asset_organizer.organize_imported_assets(
                    assets, imported_assets, imported_textures, created_materials, target_path
                )
                self.log("已组织所有资产")

            # 完成
            self.progress_bar.setValue(100)
            self.progress_label.setText("导入完成")
            self.log("资产导入过程已完成")

        except Exception as e:
            self.log(f"导入过程中出错: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # 重新启用导入按钮
            self.import_button.setEnabled(True)

    def log(self, message):
        """添加消息到日志区域"""
        self.log_text.append(f"{message}")
        print(message)  # 同时输出到控制台

def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    window = AssetImporterGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
