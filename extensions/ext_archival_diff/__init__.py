try:
    from .plugin import register_extension
except ImportError:
    from extensions.ext_archival_diff.plugin import register_extension

__all__ = ["register_extension"]
