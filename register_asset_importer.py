import unreal
import os
import sys

# 添加当前脚本所在目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

def register_asset_importer():
    print("注册资产导入工具")

    # 创建菜单项
    menu_entry = unreal.ToolMenuEntry(
        name="Python.AssetImporter",
        type=unreal.MultiBlockType.TOOL_BAR_BUTTON
    )
    menu_entry.set_label("资产导入工具")

    # 设置菜单项点击事件
    menu_entry.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="Python",
        string="import asset_importer_unreal; asset_importer_unreal.main()"
    )

    # 创建调试FBX菜单项
    debug_menu_entry = unreal.ToolMenuEntry(
        name="Python.AssetImporterDebug",
        type=unreal.MultiBlockType.TOOL_BAR_BUTTON
    )
    debug_menu_entry.set_label("调试FBX")

    # 设置调试菜单项点击事件
    debug_menu_entry.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="Python",
        string="import asset_importer_unreal; tool = asset_importer_unreal.AssetImporterTool(); tool.show_ui(); tool._on_debug_clicked()"
    )

    # 获取主菜单
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")

    # 添加菜单项
    if main_menu:
        # 创建资产导入工具子菜单
        asset_importer_menu = main_menu.add_sub_menu(
            "AssetImporterMenu",
            "资产导入工具",
            "资产导入工具",
            "资产导入工具"
        )

        # 添加菜单项
        asset_importer_section = asset_importer_menu.add_section(
            "AssetImporterSection",
            "资产导入工具"
        )

        # 添加打开工具菜单项
        asset_importer_section.add_menu_entry(
            "OpenAssetImporter",
            unreal.ToolMenuEntry(
                name="打开资产导入工具",
                type=unreal.MultiBlockType.MENU_ENTRY,
                insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.DEFAULT),
                string_command=menu_entry.string_command
            )
        )

        # 添加调试FBX菜单项
        asset_importer_section.add_menu_entry(
            "DebugFBX",
            unreal.ToolMenuEntry(
                name="调试FBX",
                type=unreal.MultiBlockType.MENU_ENTRY,
                insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.DEFAULT),
                string_command=debug_menu_entry.string_command
            )
        )

        # 添加帮助菜单项
        asset_importer_section.add_menu_entry(
            "AssetImporterHelp",
            unreal.ToolMenuEntry(
                name="帮助",
                type=unreal.MultiBlockType.MENU_ENTRY,
                insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.DEFAULT),
                string_command=unreal.ToolMenuStringCommand(
                    type=unreal.ToolMenuStringCommandType.PYTHON,
                    custom_type="Python",
                    string="import unreal; unreal.log('资产导入工具帮助：请参阅README.md文件')"
                )
            )
        )

        # 同时保留原来的工具栏按钮
        main_menu.add_menu_entry("Tools", menu_entry)

        # 刷新菜单
        menus.refresh_all_widgets()

# 注册菜单项
register_asset_importer()