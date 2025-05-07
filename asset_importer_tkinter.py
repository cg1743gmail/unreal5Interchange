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
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

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

class AssetImporterGUI:
    """资产导入工具的主GUI类"""
    
    def __init__(self, root):
        """
        初始化GUI
        
        Args:
            root: tkinter根窗口
        """
        self.root = root
        self.root.title("UE5.5 资产导入工具")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 创建主界面
        self.setup_ui()
        
        # 初始化日志
        self.log("资产导入工具已启动")
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建文件夹选择区域
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="5")
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, state="readonly")
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(folder_frame, text="浏览...", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # 创建导入选项区域
        options_frame = ttk.LabelFrame(main_frame, text="导入选项", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        # 创建选项网格
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加导入选项
        self.create_import_options(options_grid)
        
        # 创建进度显示区域
        progress_frame = ttk.LabelFrame(main_frame, text="导入进度", padding="5")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # 创建日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.import_button = ttk.Button(button_frame, text="开始导入", command=self.start_import, state="disabled")
        self.import_button.pack(side=tk.LEFT, padx=5)
        
        self.save_config_button = ttk.Button(button_frame, text="保存配置", command=self.save_config)
        self.save_config_button.pack(side=tk.LEFT, padx=5)
        
        self.load_config_button = ttk.Button(button_frame, text="加载配置", command=self.load_config)
        self.load_config_button.pack(side=tk.LEFT, padx=5)
    
    def create_import_options(self, parent):
        """
        创建导入选项控件
        
        Args:
            parent: 父控件
        """
        # 创建变量
        self.process_textures_var = tk.BooleanVar(value=self.config.get("process_textures", True))
        self.create_materials_var = tk.BooleanVar(value=self.config.get("create_materials", True))
        self.organize_folders_var = tk.BooleanVar(value=self.config.get("organize_folders", True))
        self.compress_textures_var = tk.BooleanVar(value=self.config.get("compress_textures", True))
        self.target_path_var = tk.StringVar(value=self.config.get("target_path", "/Game/ImportedAssets"))
        self.material_template_var = tk.StringVar(value=self.config.get("material_template", "/Game/MaterialTemplates/M_Standard"))
        
        # 第一行选项
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, pady=2)
        
        process_textures_check = ttk.Checkbutton(row1, text="自动处理纹理", variable=self.process_textures_var)
        process_textures_check.pack(side=tk.LEFT, padx=(0, 10))
        
        create_materials_check = ttk.Checkbutton(row1, text="创建材质实例", variable=self.create_materials_var)
        create_materials_check.pack(side=tk.LEFT)
        
        # 第二行选项
        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, pady=2)
        
        organize_folders_check = ttk.Checkbutton(row2, text="组织文件夹结构", variable=self.organize_folders_var)
        organize_folders_check.pack(side=tk.LEFT, padx=(0, 10))
        
        compress_textures_check = ttk.Checkbutton(row2, text="压缩纹理", variable=self.compress_textures_var)
        compress_textures_check.pack(side=tk.LEFT)
        
        # 第三行选项
        row3 = ttk.Frame(parent)
        row3.pack(fill=tk.X, pady=2)
        
        ttk.Label(row3, text="导入目标路径:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row3, textvariable=self.target_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 第四行选项
        row4 = ttk.Frame(parent)
        row4.pack(fill=tk.X, pady=2)
        
        ttk.Label(row4, text="材质模板路径:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row4, textvariable=self.material_template_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_folder(self):
        """浏览并选择文件夹"""
        folder = filedialog.askdirectory(title="选择资产文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.import_button["state"] = "normal"
            self.log(f"已选择文件夹: {folder}")
    
    def save_config(self):
        """保存当前配置"""
        config = {
            "process_textures": self.process_textures_var.get(),
            "create_materials": self.create_materials_var.get(),
            "organize_folders": self.organize_folders_var.get(),
            "compress_textures": self.compress_textures_var.get(),
            "target_path": self.target_path_var.get(),
            "material_template": self.material_template_var.get()
        }
        
        file_path = filedialog.asksaveasfilename(
            title="保存配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if file_path:
            self.config_manager.save_config(config, file_path)
            self.log(f"配置已保存到: {file_path}")
    
    def load_config(self):
        """加载配置文件"""
        file_path = filedialog.askopenfilename(
            title="加载配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if file_path:
            config = self.config_manager.load_config(file_path)
            self.update_ui_from_config(config)
            self.log(f"已加载配置: {file_path}")
    
    def update_ui_from_config(self, config):
        """
        根据配置更新UI
        
        Args:
            config (dict): 配置字典
        """
        self.process_textures_var.set(config.get("process_textures", True))
        self.create_materials_var.set(config.get("create_materials", True))
        self.organize_folders_var.set(config.get("organize_folders", True))
        self.compress_textures_var.set(config.get("compress_textures", True))
        self.target_path_var.set(config.get("target_path", "/Game/ImportedAssets"))
        self.material_template_var.set(config.get("material_template", "/Game/MaterialTemplates/M_Standard"))
    
    def start_import(self):
        """开始导入过程"""
        # 获取当前设置
        source_folder = self.folder_path_var.get()
        target_path = self.target_path_var.get()
        
        if not source_folder:
            messagebox.showerror("错误", "请选择源文件夹")
            return
        
        # 收集当前配置
        config = {
            "process_textures": self.process_textures_var.get(),
            "create_materials": self.create_materials_var.get(),
            "organize_folders": self.organize_folders_var.get(),
            "compress_textures": self.compress_textures_var.get(),
            "target_path": target_path,
            "material_template": self.material_template_var.get()
        }
        
        self.log("开始导入过程...")
        self.log(f"源文件夹: {source_folder}")
        self.log(f"目标路径: {target_path}")
        
        # 禁用导入按钮，防止重复点击
        self.import_button["state"] = "disabled"
        
        # 创建一个单独的线程来执行导入过程
        import threading
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
            self.root.after(0, lambda: self.import_button.configure(state="normal"))
    
    def update_progress(self, value, text):
        """
        更新进度条和进度文本
        
        Args:
            value (int): 进度值 (0-100)
            text (str): 进度文本
        """
        self.root.after(0, lambda: self.progress_var.set(value))
        self.root.after(0, lambda: self.progress_label.configure(text=text))
    
    def log(self, message):
        """
        添加消息到日志区域
        
        Args:
            message (str): 日志消息
        """
        def _update_log():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        
        self.root.after(0, _update_log)
        print(message)  # 同时输出到控制台

def main():
    """主函数"""
    root = tk.Tk()
    app = AssetImporterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
