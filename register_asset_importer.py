import unreal
   
   def register_asset_importer():
       print("注册资产导入工具"))
       # 创建菜单项
       menu_entry = unreal.ToolMenuEntry(
           name="Python.AssetImporter",
           type=unreal.MultiBlockType.TOOL_BAR_BUTTON,
           label="资产导入工具"
       )
       
       # 设置菜单项点击事件
       menu_entry.set_string_command(
           command_type=unreal.ToolMenuStringCommandType.PYTHON,
           custom_type="Python",
           string="import asset_importer_unreal; asset_importer_unreal.main()"
       )
       
       # 获取主菜单
       menus = unreal.ToolMenus.get()
       main_menu = menus.find_menu("LevelEditor.MainMenu")
       
       # 添加菜单项
       if main_menu:
           section = main_menu.find_section("Tools")
           section.add_menu_entry("Python", menu_entry)
           menus.refresh_all_widgets()
   
   # 注册菜单项
   register_asset_importer()