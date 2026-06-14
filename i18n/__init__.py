"""国际化模块 — 多语言翻译支持。

用法:
    from i18n import t

    label.setText(t("balance_title"))       # 静态文本
    label.setText(t("last_updated", time="14:30"))  # 带参数
"""

from i18n.translations import TRANSLATIONS, LANGUAGES

# 当前语言（默认简体中文）
_current_lang: str = "zh_CN"


def set_language(lang: str) -> None:
    """设置当前语言。"""
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang
    else:
        _current_lang = "zh_CN"


def get_language() -> str:
    """获取当前语言代码。"""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """获取翻译文本。

    Args:
        key: 翻译键名。
        **kwargs: 格式化参数（如 time="14:30"）。

    Returns:
        翻译后的文本。找不到时回退到简体中文，再找不到返回 key 本身。
    """
    text = TRANSLATIONS.get(_current_lang, {}).get(key)
    if text is None:
        text = TRANSLATIONS.get("zh_CN", {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
