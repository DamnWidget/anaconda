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
                                "command": "open_file",
                                "args": {"file": "${packages}/$package_folder/Anaconda.sublime-settings"},
                                "caption": "Settings - Default"
                            },
                            {
                                "command": "open_file",
                                "args": {"file": "${packages}/User/Anaconda.sublime-settings"},
                                "caption": "Settings – User"
                            },
                            {
                                "command": "open_file_settings",
                                "caption": "Settings – Syntax Specific – User"
                            },
                            { "caption": "-" },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/$package_folder/Default (OSX).sublime-keymap",
                                    "platform": "OSX"
                                },
                                "caption": "Key Bindings – Default"
                            },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/$package_folder/Default (Linux).sublime-keymap",
                                    "platform": "Linux"
                                },
                                "caption": "Key Bindings – Default"
                            },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/$package_folder/Default (Windows).sublime-keymap",
                                    "platform": "Windows"
                                },
                                "caption": "Key Bindings – Default"
                            },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/User/Default (OSX).sublime-keymap",
                                    "platform": "OSX"
                                },
                                "caption": "Key Bindings – User"
                            },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/User/Default (Linux).sublime-keymap",
                                    "platform": "Linux"
                                },
                                "caption": "Key Bindings – User"
                            },
                            {
                                "command": "open_file",
                                "args": {
                                    "file": "${packages}/User/Default (Windows).sublime-keymap",
                                    "platform": "Windows"
                                },
                                "caption": "Key Bindings – User"
                            },
                            { "caption": "-" }
                        ]
                    }
                ]
            }
        ]
    }

]