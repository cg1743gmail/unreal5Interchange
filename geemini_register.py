import unreal
import os
import sys

# 添加当前脚本所在目录到Python路径
# 这确保了Python能找到同一目录下的 asset_importer_unreal.py 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
    # 打印确认路径是否已添加 (可选，用于调试)
    # print(f"Added {script_dir} to sys.path")


# 定义一个 Owner Name，用于所有由本脚本创建的 ToolMenuEntry 和 ToolMenu
# 建议使用您的插件或项目的唯一标识符，这里只是一个示例
ASSET_IMPORTER_OWNER = unreal.Name("MyAssetImporterSystem") # 使用一个独特的英文Owner Name

def register_asset_importer():
    print("正在注册资产导入工具菜单...")

    # 定义共享的字符串命令
    # 注意：命令字符串中的模块名 (asset_importer_unreal) 需要在Python Path中可找到
    # 确保 asset_importer_unreal.py 文件存在且包含 main() 和 AssetImporterTool 类
    open_tool_command_string = "import asset_importer_unreal; asset_importer_unreal.main()"
    debug_fbx_command_string = "import asset_importer_unreal; tool = asset_importer_unreal.AssetImporterTool(); tool.show_ui(); tool._on_debug_clicked()"
    help_command_string = "import unreal; unreal.log('资产导入工具帮助：请参阅README.md文件')"

    # 获取主菜单和工具栏
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    toolbar_menu = menus.find_menu("LevelEditor.LevelEditorToolBar")

    # === 1. 在主菜单栏添加一个全新的顶层子菜单 ===
    # 使用更简单的 add_sub_menu 签名，直接在 LevelEditor.MainMenu 上添加
    asset_importer_sub_menu = None
    if main_menu:
        try:
            asset_importer_sub_menu = main_menu.add_sub_menu(
                unreal.Name("AssetImporterTopLevelMenu"),  # <--- 新子菜单的唯一内部名 (英文)
                "资产导入工具",                           # <--- 在主菜单栏中显示的标签 (中文)
                "打开资产导入工具菜单"                     # <--- 子菜单的 tooltip
                # 注意: 这里不再指定 owner 和 section_name，这通常用于添加到现有Section
            )
            if asset_importer_sub_menu:
                print("成功创建 '资产导入工具' 顶层子菜单头。")
            else:
                 print("警告: add_sub_menu 调用失败，未能获取有效的子菜单对象!")
        except Exception as e:
             print(f"错误: 创建 '资产导入工具' 顶层子菜单时发生异常: {e}")
             asset_importer_sub_menu = None # 确保失败时对象为 None


    # === 2. 在新创建的子菜单中添加 Section 和菜单项 (如果子菜单创建成功) ===
    if asset_importer_sub_menu:
        # 添加 Section 到新的子菜单中
        asset_importer_section = None
        try:
            # 第一个参数是 Section 的内部名 (英文)，第二个参数是 Section 的显示标签 (可以是中文)
            asset_importer_section = asset_importer_sub_menu.add_section(
                unreal.Name("ImporterActionsSection"),  # <--- Section 的内部名 (英文)
                "导入工具操作"                          # <--- Section 的标题 (中文)
            )
            if asset_importer_section:
                print("成功创建 '导入工具操作' Section。")
            else:
                 print("警告: add_section 调用失败，未能获取有效的 Section 对象!")
        except Exception as e:
            print(f"错误: 创建 '导入工具操作' Section 时发生异常: {e}")
            asset_importer_section = None # 确保失败时对象为 None


        if asset_importer_section:
            # 添加 "打开资产导入工具" 菜单项
            try:
                open_tool_entry = unreal.ToolMenuEntry(
                    owner=ASSET_IMPORTER_OWNER, # <--- 指定 Owner
                    name=unreal.Name("OpenAssetImporterEntry"), # <--- 菜单项的唯一内部名 (英文)
                    type=unreal.MultiBlockType.MENU_ENTRY
                )
                # 使用 ToolMenuEntryExtensions 设置命令 (推荐方式)
                unreal.ToolMenuEntryExtensions.set_string_command(
                    open_tool_entry,
                    type=unreal.ToolMenuStringCommandType.PYTHON,
                    custom_type=unreal.Name("Python"),
                    string=open_tool_command_string # 使用之前定义的命令字符串
                )
                open_tool_entry.set_label("打开资产导入工具") # <--- 设置显示标签 (中文)
                # 将 Entry 添加到 Section。第一个参数是 Entry 在这个 Section 中的唯一实例名。
                asset_importer_section.add_menu_entry(unreal.Name("OpenAssetImporterEntryInstance"), open_tool_entry)
                print("成功添加 '打开资产导入工具' 菜单项。")
            except Exception as e:
                 print(f"错误: 添加 '打开资产导入工具' 菜单项时发生异常: {e}")


            # 添加 "调试FBX" 菜单项
            try:
                debug_fbx_entry = unreal.ToolMenuEntry(
                    owner=ASSET_IMPORTER_OWNER, # <--- 指定 Owner
                    name=unreal.Name("DebugFBXEntry"), # <--- 菜单项的唯一内部名 (英文)
                    type=unreal.MultiBlockType.MENU_ENTRY
                )
                # 使用 ToolMenuEntryExtensions 设置命令 (推荐方式)
                unreal.ToolMenuEntryExtensions.set_string_command(
                    debug_fbx_entry,
                    type=unreal.ToolMenuStringCommandType.PYTHON,
                    custom_type=unreal.Name("Python"),
                    string=debug_fbx_command_string # 使用之前定义的命令字符串
                )
                debug_fbx_entry.set_label("调试FBX") # <--- 设置显示标签 (中文)
                 # 将 Entry 添加到 Section
                asset_importer_section.add_menu_entry(unreal.Name("DebugFBXEntryInstance"), debug_fbx_entry)
                print("成功添加 '调试FBX' 菜单项。")
            except Exception as e:
                 print(f"错误: 添加 '调试FBX' 菜单项时发生异常: {e}")


            # 添加 "帮助" 菜单项
            try:
                help_entry = unreal.ToolMenuEntry(
                    owner=ASSET_IMPORTER_OWNER, # <--- 指定 Owner
                    name=unreal.Name("AssetImporterHelpEntry"), # <--- 菜单项的唯一内部名 (英文)
                    type=unreal.MultiBlockType.MENU_ENTRY
                )
                # 使用 ToolMenuEntryExtensions 设置命令 (推荐方式)
                unreal.ToolMenuEntryExtensions.set_string_command(
                    help_entry,
                    type=unreal.ToolMenuStringCommandType.PYTHON,
                    custom_type=unreal.Name("Python"),
                    string=help_command_string # 使用之前定义的命令字符串
                )
                help_entry.set_label("帮助") # <--- 设置显示标签 (中文)
                 # 将 Entry 添加到 Section
                asset_importer_section.add_menu_entry(unreal.Name("AssetImporterHelpEntryInstance"), help_entry)
                print("成功添加 '帮助' 菜单项。")
            except Exception as e:
                 print(f"错误: 添加 '帮助' 菜单项时发生异常: {e}")
        # else: 警告已在创建 section 时打印


    # === 3. 添加工具栏按钮 (如果toolbar_menu存在) ===
    # 这是一个单独的按钮，通常用于直接执行打开工具的操作
    if toolbar_menu:
        # 创建用于工具栏的菜单项 (类型为 TOOL_BAR_BUTTON)，指定 owner
        toolbar_button_entry = unreal.ToolMenuEntry(
            owner=ASSET_IMPORTER_OWNER, # <--- 指定 Owner
            name=unreal.Name("AssetImporterToolbarButtonEntry"), # <--- 按钮的唯一内部名 (英文)
            type=unreal.MultiBlockType.TOOL_BAR_BUTTON
        )
        # 使用 ToolMenuEntryExtensions 设置命令 (推荐方式)
        unreal.ToolMenuEntryExtensions.set_string_command(
            toolbar_button_entry,
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type=unreal.Name("Python"),
            string=open_tool_command_string # 工具栏按钮通常用于打开工具，所以使用 open_tool_command_string
        )
        toolbar_button_entry.set_label("资产导入工具")
        toolbar_button_entry.set_tool_tip("打开资产导入工具") # 添加一个Tooltip

        # 找到一个现有的Section来添加按钮
        # 注意：LevelEditor.LevelEditorToolBar 的 Section 名称需要通过 find_sections() 查看确认
        # 例如，常见的 Section 有 "Content", "Build", "Tools" 等
        # 这里使用 "Content" 作为一个可能的示例 Section，请根据实际情况调整
        target_toolbar_section_name = unreal.Name("Content") # 尝试添加到 Content Section

        target_toolbar_section = toolbar_menu.find_section(target_toolbar_section_name)

        if target_toolbar_section:
            try:
                # 将工具栏 Entry 添加到 Section 中
                # add_menu_entry 的第一个参数是这个 Entry 在此 Section 中的唯一实例名
                 target_toolbar_section.add_menu_entry(
                    unreal.Name("AssetImporterToolbarButtonInstance"), # <--- 在Section中的唯一内部实例名 (英文)
                    toolbar_button_entry # <--- 添加 TOOL_BAR_BUTTON 类型的 Entry
                )
                 print(f"成功将工具栏按钮添加到 '{target_toolbar_section_name}' Section。")
            except Exception as e:
                 print(f"错误: 将工具栏按钮添加到 '{target_toolbar_section_name}' Section 时发生异常: {e}")
        else:
            # 如果找不到目标 Section，打印警告，您可以选择添加到其他 Section 或创建一个新的 Section (更复杂)
            print(f"警告: 未找到工具栏 Section '{target_toolbar_section_name}'，无法添加资产导入工具按钮。请检查 Section 名称。")
            # 您可以在 UE5 Python 交互式窗口运行以下代码来查看可用的工具栏 Section 名称：
            # menus = unreal.ToolMenus.get()
            # toolbar_menu = menus.find_menu("LevelEditor.LevelEditorToolBar")
            # if toolbar_menu:
            #     print("LevelEditor.LevelEditorToolBar 可用 Section:")
            #     for section in toolbar_menu.find_sections():
            #         print(section.get_name())


    # === 4. 刷新菜单以显示更改 ===
    # 这个步骤是必须的，否则您在代码中的更改不会立即反映在编辑器界面中
    menus.refresh_all_widgets()
    print("资产导入工具菜单注册流程结束。请检查编辑器界面和输出日志。")


# === 5. 注册菜单项 ===
# 确保在 UE5 Editor 环境中运行此脚本 (例如通过 UE 的 Python Editor 插件)
try:
    register_asset_importer()
except Exception as e:
    print(f"注册资产导入工具菜单脚本主执行时发生未捕获的异常: {e}")