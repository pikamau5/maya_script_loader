import script_loader_pkg.script_loader as script_loader
reload(script_loader)

exportUi = script_loader.ScriptLoaderUI()
exportUi.setup_ui()
exportUi.show()