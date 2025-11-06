__id__ = "anti_ayugram_easter_eggs"
__name__ = "🛡️Anti AyuGram Easter Eggs🥚"
__version__ = "1.0"
__min_version__ = "11.12.0"
__author__ = "@ayugram_easter"
__icon__ = "AllTheMemes/0"
__description__ = """
🇬🇧EN: The plugin protects against opening AyuGram Easter eggs (tg://ayu/... train, xiaomi, relax, augh, pipe, saul, komaru, lobster)
/
🇷🇺RU: Плагин защищает от открытия пасхалок AyuGram (tg://ayu/... train, xiaomi, relax, augh, pipe, saul, komaru, lobster)
"""

import traceback
from base_plugin import BasePlugin
from hook_utils import find_class
from client_utils import get_last_fragment
from ui.alert import AlertDialogBuilder
from android_utils import run_on_ui_thread, log

try:
    from ui.settings import Header, Text
except Exception:
    Header = Text = None

try:
    from java.util import Locale
except Exception:
    Locale = None

TARGET_PATHS = {
    "train", "xiaomi", "relax", "augh", "pipe", "saul", "komaru", "lobster"
}

GITHUB_URL = "https://github.com/AlexeiCrystal/anti-ayugram-easter-eggs"

LOCALIZED = {
    "ru": {
        "links_header": "Ссылки",
        "open_github": "Открыть GitHub",
        "dialog_title": "🛡️Anti AyuGram Easter Eggs🥚",
        "dialog_message": "Вы чуть не попались на пасхалку AyuGram:\n{url}",
        "close": "Закрыть",
        "git_dialog_title": "GitHub",
        "git_dialog_ok": "OK"
    },
    "en": {
        "links_header": "Links",
        "open_github": "Open GitHub repository",
        "dialog_title": "🛡️Anti AyuGram Easter Eggs🥚",
        "dialog_message": "You almost fell for an AyuGram easter egg:\n{url}",
        "close": "Close",
        "git_dialog_title": "GitHub",
        "git_dialog_ok": "OK"
    }
}

def _get_lang():
    try:
        if Locale:
            lang = Locale.getDefault().getLanguage()
            return "ru" if str(lang).lower().startswith("ru") else "en"
    except Exception:
        pass
    return "en"

def _t(key: str, **kwargs) -> str:
    lang = _get_lang()
    block = LOCALIZED.get(lang, LOCALIZED["en"])
    text = block.get(key, LOCALIZED["en"].get(key, ""))
    try:
        return text.format(**kwargs)
    except Exception:
        return text

class _DeepLinkHookAyu:
    def __init__(self, plugin):
        self.plugin = plugin
        self.pending_param = None

    def before_hooked_method(self, param):
        try:
            intent = param.args[0]
            if not intent or not intent.getData():
                return
            url = str(intent.getData())
            if not url.startswith("tg://ayu/"):
                return

            path = url[len("tg://ayu/"):].split('/')[0].split('?')[0].strip().lower()
            if path not in TARGET_PATHS:
                return

            self.pending_param = param
            param.setResult(None)
            run_on_ui_thread(lambda: self.show_block_dialog(url))
        except Exception:
            self.plugin.log("DeepLinkHook error: " + traceback.format_exc())

    def show_block_dialog(self, url):
        fragment = get_last_fragment()
        activity = fragment.getParentActivity() if fragment else None
        if not activity:
            self.pending_param = None
            return

        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title(_t("dialog_title"))
            builder.set_message(_t("dialog_message", url=url))
            builder.set_positive_button(_t("close"), lambda b, w: self.close_dialog())
            builder.set_on_cancel_listener(lambda b: self.close_dialog())
            builder.show()
        except Exception:
            self.plugin.log("Failed to show dialog: " + traceback.format_exc())
            self.pending_param = None

    def close_dialog(self):
        self.pending_param = None

class AntiAyuPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.unhook_deeplink = None

    def on_plugin_load(self):
        self.log("Anti AyuGram Easter Eggs loaded.")
        self._setup_deeplink_hook()

    def on_plugin_unload(self):
        if self.unhook_deeplink:
            try:
                self.unhook_method(self.unhook_deeplink)
            except Exception:
                pass
            self.unhook_deeplink = None
        self.log("Anti AyuGram Easter Eggs unloaded.")

    def _setup_deeplink_hook(self):
        try:
            launch_activity_cls = find_class("org.telegram.ui.LaunchActivity")
            method = launch_activity_cls.getClass().getDeclaredMethod(
                "handleIntent",
                find_class("android.content.Intent"),
                find_class("java.lang.Boolean").TYPE,
                find_class("java.lang.Boolean").TYPE,
                find_class("java.lang.Boolean").TYPE,
                find_class("org.telegram.messenger.browser.Browser$Progress"),
                find_class("java.lang.Boolean").TYPE,
                find_class("java.lang.Boolean").TYPE
            )
            self.unhook_deeplink = self.hook_method(method, _DeepLinkHookAyu(self))
        except Exception:
            try:
                metod2 = launch_activity_cls.getClass().getDeclaredMethod("handleIntent", find_class("android.content.Intent"))
                self.unhook_deeplink = self.hook_method(metod2, _DeepLinkHookAyu(self))
            except Exception:
                self.log("Failed to hook LaunchActivity.handleIntent for Ayu links.")

    def create_settings(self):
        items = []
        try:
            if Header:
                items.append(Header(text=_t("links_header")))
        except Exception:
            pass

        def open_github(v):
            try:
                fragment = get_last_fragment()
                activity = fragment.getParentActivity() if fragment else None
                if not activity:
                    return
                try:
                    from org.telegram.messenger.browser import Browser
                    from android.net import Uri
                    Browser.openUrl(activity, Uri.parse(GITHUB_URL))
                except Exception:
                    b = AlertDialogBuilder(activity)
                    b.set_title(_t("git_dialog_title"))
                    b.set_message(GITHUB_URL)
                    b.set_positive_button(_t("git_dialog_ok"), None)
                    b.show()
            except Exception:
                self.log("Failed to open GitHub: " + traceback.format_exc())

        try:
            if Text:
                items.append(Text(text=_t("open_github"), on_click=open_github, icon="msg_link"))
        except Exception:
            pass

        return items

    def log(self, message: str):
        log(f"[Anti AyuGram Easter Eggs] {message}")