import sublime


class Integration:
    """Checks if Kite integration is turned on
    """

    @classmethod
    def enabled(cls):
        """Returns True if Kite integration is enabled
        """

        settings = sublime.load_settings('AnacondaKite.sublime-settings')
        enabled = settings.get('integrate_with_kite', False)
        if enabled:
            try:
                from Kite.lib.installer import check
                from Kite.lib.exceptions import KiteNotSupported
                if not check.is_running():
                    return False
            except ImportError:
                return False
            except KiteNotSupported:
                # Kite will raise KiteNotSupported on Linux
                return True

            return True

        return False

    @classmethod
    def enable(cls):
        """Enable Kite integration
        """

        settings = sublime.load_settings('AnacondaKite.sublime-settings')
        settings.set('integrate_with_kite', True)
        settings.save_settings('AnacondaKite.sublime-settings')

    @classmethod
    def disable(cls):
        """Disable Kite integration
        """

        settings = sublime.load_settings('AnacondaKite.sublime-settings')
        settings.set('integrate_with_kite', False)
        settings.save_settings('AnacondaKite.sublime-settings')
