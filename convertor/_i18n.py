import oslo_i18n
from oslo_i18n import _lazy

# The domain is the name of the App which is used to generate the folder
# containing the translation files (i.e. the .pot file and the various locales)
DOMAIN = "watcher"

_translators = oslo_i18n.TranslatorFactory(domain=DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary

# The contextual translation function using the name "_C"
_C = _translators.contextual_form

# The plural translation function using the name "_P"
_P = _translators.plural_form


def lazy_translation_enabled():
    return _lazy.USE_LAZY


def get_available_languages():
    return oslo_i18n.get_available_languages(DOMAIN)