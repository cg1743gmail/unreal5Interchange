# Unreal Engine 5.5 资产导入工具

基于Unreal Engine 5.5 Python API和Interchange插件的高效资产导入工具，用于自动化导入和组织模型、纹理、FBX和MA文件。

## 主要功能

- **自动化资产导入**：使用Interchange插件高效导入FBX、MA文件和纹理
- **智能资产识别**：自动识别不同类型的资产（静态网格、骨骼网格、动画、各类纹理）
- **智能纹理处理**：自动设置纹理属性、压缩和分组，支持根据文件名将特殊纹理（如HDR）导入到指定文件夹
- **智能材质创建**：根据模型名称或材质槽名称自动选择合适的材质模板，创建材质实例并连接相关纹理
- **资产组织**：按类型组织资产到合适的文件夹结构
- **配置管理**：保存和加载导入配置，支持项目间复用

## 系统要求

- Unreal Engine 5.5或更高版本
- 启用Interchange插件
- 根据选择的UI版本可能需要额外的Python库：
  - PySide2/Qt版本需要安装PySide2
  - tkinter版本使用Python标准库
  - Unreal UI版本不需要额外库

## 安装方法

1. 确保Unreal Engine项目中已启用Python和Interchange插件
2. 将所有Python文件和配置文件复制到以下位置之一：
   - Unreal项目的`/Content/Python/`目录
   - Unreal Engine的`/Engine/Plugins/Interchange/Scripts/`目录
   - 任何已添加到Python路径的目录

## 使用方法

### 启动工具

在Unreal Engine编辑器中，可以通过以下方式启动工具：

1. **Python控制台**：
   ```python
   import asset_importer_unreal
   asset_importer_unreal.main()
   ```

2. **编辑器菜单**：
   - 创建编辑器扩展菜单项指向脚本（需要额外设置）

### 基本操作流程

1. 点击"浏览..."按钮选择包含资产的文件夹
2. 配置导入选项：
   - 自动处理纹理：启用/禁用纹理处理
   - 创建材质实例：启用/禁用材质创建
   - 组织文件夹结构：启用/禁用资产组织
   - 压缩纹理：启用/禁用纹理压缩
   - 导入目标路径：设置资产导入的目标路径（如`/Game/ImportedAssets`）
   - 材质模板路径：设置用于创建材质实例的模板材质路径
3. 点击"开始导入"按钮开始导入过程
4. 导入进度和日志会实时显示在界面上

### 配置管理

- **保存配置**：点击"保存配置"按钮将当前设置保存为JSON文件
- **加载配置**：点击"加载配置"按钮加载之前保存的设置

### 材质模板映射

工具支持根据模型名称中的特定字段自动选择不同的材质模板：

1. 在配置文件中设置`material_template_mapping`部分
2. 定义模式和对应的材质模板路径
3. 导入时，工具会检查模型名称是否包含指定模式，并使用对应的材质模板

例如，名为`Chair_Wood.fbx`的模型会使用木材材质模板，而`Table_Metal.fbx`会使用金属材质模板。

### 特殊纹理文件夹

工具支持根据纹理文件名中的特定字段将纹理导入到指定的文件夹：

1. 在配置文件中设置`texture_special_folders`部分
2. 定义模式、目标文件夹和特殊设置
3. 导入时，工具会检查纹理名称是否包含指定模式，并将其导入到对应的文件夹

例如，名为`Landscape_hdr.exr`的纹理会被导入到HDR文件夹，并使用HDR压缩设置。

### 材质槽映射

工具支持根据FBX中的材质槽名称选择不同的材质模板：

1. 在配置文件中设置`material_slot_mapping`部分
2. 定义模式和对应的材质模板路径
3. 导入时，工具会检查材质槽名称是否包含指定模式，并使用对应的材质模板

例如，名为"Metal_Body"的材质槽会使用金属材质模板，而"Glass_Window"会使用玻璃材质模板。

### 材质实例命名规则

工具支持自定义材质实例的命名规则：

1. 在配置文件中设置`material_slot_mapping.naming_convention`部分
2. 定义格式字符串、空格替换规则和大小写规则
3. 导入时，工具会根据这些规则生成材质实例名称

支持的格式占位符：
- `{asset_name}` - 资产名称
- `{slot_name}` - 材质槽名称
- `{template_name}` - 材质模板名称（不含前缀和扩展名）

例如，格式字符串`"MI_{asset_name}_{slot_name}_{template_name}"`会生成类似`"MI_CHAIR_BODY_METAL"`的名称。

### 导入模式

工具支持两种导入模式：

1. **导入到指定文件夹**：使用配置中设置的目标路径作为父文件夹
2. **导入到当前内容浏览器文件夹**：使用当前内容浏览器中所在的文件夹作为父文件夹

可以在界面中选择导入模式，也可以在配置文件中设置默认模式。

## 文件命名约定

工具使用文件名模式来识别不同类型的资产。默认的命名约定如下：

- **静态网格**：包含`_SM`、`_StaticMesh`或`_Model`
- **骨骼网格**：包含`_SK`、`_SkeletalMesh`或`_Character`
- **动画**：包含`_Anim`或`_Animation`
- **漫反射纹理**：包含`_D`、`_Diffuse`、`_BaseColor`、`_Albedo`或`_Color`
- **法线纹理**：包含`_N`或`_Normal`
- **粗糙度纹理**：包含`_R`或`_Roughness`
- **金属度纹理**：包含`_M`或`_Metallic`
- **高光纹理**：包含`_S`或`_Specular`
- **自发光纹理**：包含`_E`或`_Emissive`

这些命名约定可以在`config.json`文件中自定义。

## 项目结构

- `asset_importer.py` - 使用PySide2/Qt的主脚本
- `asset_importer_tkinter.py` - 使用tkinter的主脚本
- `asset_importer_unreal.py` - 使用Unreal UI的主脚本
- `config_manager.py` - 配置管理模块
- `folder_scanner.py` - 文件夹扫描模块
- `asset_processor.py` - 资产处理模块
- `texture_processor.py` - 纹理处理模块
- `material_creator.py` - 材质创建模块
- `asset_organizer.py` - 资产组织模块
- `config.json` - 默认配置文件

## 开发文档

### 架构概述

工具采用模块化设计，每个模块负责特定功能：

1. **GUI模块**（三个版本）：提供用户界面和交互
2. **配置管理模块**：处理配置的加载和保存
3. **文件夹扫描模块**：扫描和分析资产文件
4. **资产处理模块**：处理FBX和MA文件的导入
5. **纹理处理模块**：处理纹理的导入和设置
6. **材质创建模块**：创建材质实例和连接纹理
7. **资产组织模块**：组织导入的资产

### 主要类和函数

#### GUI模块

- `AssetImporterGUI`（PySide2版本）
- `AssetImporterGUI`（tkinter版本）
- `AssetImporterTool`（Unreal UI版本）

主要方法：
- `setup_ui()`: 创建用户界面
- `start_import()`: 开始导入过程
- `log()`: 记录日志消息

#### 配置管理模块

- `ConfigManager`: 管理配置的加载和保存

主要方法：
- `load_config()`: 加载配置文件
- `save_config()`: 保存配置到文件
- `_create_default_config()`: 创建默认配置

#### 文件夹扫描模块

- `FolderScanner`: 扫描和分析资产文件
- `AssetFile`: 表示一个资产文件

主要方法：
- `scan_folder()`: 扫描文件夹并识别资产
- `_identify_texture_type()`: 识别纹理类型
- `_analyze_asset_relationships()`: 分析资产关系

#### 资产处理模块

- `AssetProcessor`: 处理资产导入

主要方法：
- `import_asset()`: 导入资产文件
- `import_fbx()`: 导入FBX文件
- `_configure_static_mesh_pipeline()`: 配置静态网格导入管道

#### 纹理处理模块

- `TextureProcessor`: 处理纹理导入和设置

主要方法：
- `import_texture()`: 导入纹理文件
- `_configure_texture_pipeline()`: 配置纹理导入管道
- `organize_textures()`: 组织纹理到适当的文件夹

#### 材质创建模块

- `MaterialCreator`: 创建材质实例和连接纹理

主要方法：
- `create_material_instance()`: 创建材质实例
- `_connect_textures_to_material()`: 将纹理连接到材质参数
- `assign_material_to_mesh()`: 将材质分配给网格体

#### 资产组织模块

- `AssetOrganizer`: 组织导入的资产

主要方法：
- `create_folder_structure()`: 创建文件夹结构
- `organize_assets()`: 组织资产到适当的文件夹
- `_move_asset()`: 移动资产到新路径

### 扩展和自定义

#### 添加新的资产类型支持

1. 在`config.json`的`filename_patterns`中添加新的模式
2. 在`folder_scanner.py`的`_process_fbx_file()`方法中添加新类型的识别
3. 在`asset_processor.py`中添加相应的处理逻辑

#### 自定义材质模板

1. 在Unreal Engine中创建自定义材质模板
2. 在配置中设置`material_template`路径指向该模板
3. 如需添加新的纹理参数映射，修改`material_creator.py`中的`_connect_textures_to_material()`方法

#### 添加新的导入选项

1. 在GUI模块中添加新的UI控件
2. 在配置管理模块中添加相应的配置项
3. 在相关处理模块中实现新选项的功能

## 故障排除

### 常见问题

1. **找不到模块**
   - 确保所有Python文件都在同一目录下
   - 检查Python路径设置

2. **导入失败**
   - 确保Interchange插件已启用
   - 检查FBX文件格式是否兼容
   - 查看Unreal Engine日志获取详细错误信息

3. **材质创建失败**
   - 确保材质模板路径正确
   - 检查纹理命名是否符合约定

4. **UI不显示**
   - 对于PySide2版本，确保已安装PySide2
   - 对于Unreal UI版本，确保使用的是正确的Unreal Python API

### 日志和调试

- 工具日志会显示在界面的日志区域
- 同时也会输出到Unreal Engine的输出日志
- 可以在代码中添加`unreal.log_warning()`或`unreal.log_error()`来输出更详细的调试信息

## 未来改进计划

- 支持更多文件格式（USD、glTF等）
- 改进材质创建逻辑，支持更复杂的材质结构
- 添加批处理模式，支持命令行操作
- 添加预览功能，在导入前预览资产
- 添加更多自定义选项，如LOD生成、碰撞设置等
- 集成版本控制系统，支持资产的版本管理

## 许可证

本工具仅供学习和使用，使用时请遵守Unreal Engine的许可条款。

## 作者

Augment Agent
