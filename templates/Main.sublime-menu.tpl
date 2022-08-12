[
    {

        "id": "preferences",
        "children":
        [
            {
                "caption": "Package Settings",
                "mnemonic": "P",
                "id": "package-settings",
                "children":
                [
                    {
                        "caption": "Anaconda",
                        "children":
                        [
                            {
                                "command": "open_file",
                                "args": {"file": "${packages}/$package_folder/README.md"},
                                "caption": "README"
                            },
                            {
                                "command": "open_file",
                                "args": {"file": "${packages}/$package_folder/LICENSE"},
                                "caption": "LICENSE"
                            },
                            { "caption": "-" },
                            {
                                "caption": "Preferences: Settings",
                                "command": "edit_settings", "args":
                                {
                                    "base_file": "${packages}/$package_folder/Anaconda.sublime-settings",
                                    "default": "{\n\t$0\n}\n"
                                }
                            },
                            {
                                "command": "open_file_settings",
                                "caption": "Settings – Syntax Specific – User"
                            },
                            { "caption": "-" },
                            {
                                "caption": "Preferences: Key Bindings",
                                "command": "edit_settings", "args":
                                {
                                    "base_file": "${packages}/$package_folder/Default ($platform).sublime-keymap",
                                    "default": "[\n\t$0\n]\n"
                                }
                            },
                            { "caption": "-" }
                        ]
                    }
                ]
            }
        ]
    }

]
