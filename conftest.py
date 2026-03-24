import logging
import re
import typing

import pydantic.v1.main
from pydantic.v1 import errors


# --- PYDANTIC V1 PATCH FOR PYTHON 3.14 ---
def patch_pydantic_v1():
    """
    Apply Pydantic v1 patch for Python 3.14 compatibility.
    This is a local version that mirrors src/__init__.py apply_python314_patches.
    """
    try:
        original_new = pydantic.v1.main.ModelMetaclass.__new__

        def patched_new(mcs, name, bases, namespace, **kwargs):
            try:
                return original_new(mcs, name, bases, namespace, **kwargs)
            except (errors.ConfigError, TypeError, Exception) as e:
                err_msg = str(e)
                if "unable to infer type" in err_msg:
                    match = re.search(r'attribute "([^"]+)"', err_msg)
                    if match:
                        attr_name = match.group(1)
                        if "__annotations__" not in namespace:
                            namespace["__annotations__"] = {}
                        namespace["__annotations__"][attr_name] = typing.Any
                        try:
                            return original_new(mcs, name, bases, namespace, **kwargs)
                        except Exception:
                            pass
                raise

        pydantic.v1.main.ModelMetaclass.__new__ = patched_new
        logging.info("Pydantic v1 monkey-patch applied successfully")
    except Exception as e:
        logging.warning(f"Pydantic v1 monkey-patch failed to apply: {e}")


def pytest_configure(config):
    """
    Hook to apply patches at the beginning of the pytest session.
    """
    patch_pydantic_v1()
    print("\n[HOOK] Pydantic v1 monkey-patch applied")


# Also apply immediately just in case collection starts before hook
patch_pydantic_v1()
