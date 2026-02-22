import sys
import logging
import typing
import pytest

# --- PYDANTIC V1 PATCH FOR PYTHON 3.14 ---
def patch_pydantic_v1():
    try:
        import pydantic.v1.main as pydantic_main
        from pydantic.v1.errors import ConfigError
        
        original_new = pydantic_main.ModelMetaclass.__new__
        
        def patched_new(mcs, name, bases, namespace, **kwargs):
            try:
                return original_new(mcs, name, bases, namespace, **kwargs)
            except (ConfigError, TypeError, Exception) as e:
                err_msg = str(e)
                if 'unable to infer type' in err_msg:
                    import re
                    match = re.search(r'attribute "([^"]+)"', err_msg)
                    if match:
                        attr_name = match.group(1)
                        if '__annotations__' not in namespace:
                            namespace['__annotations__'] = {}
                        namespace['__annotations__'][attr_name] = typing.Any
                        try:
                            return original_new(mcs, name, bases, namespace, **kwargs)
                        except: pass
                raise
        
        pydantic_main.ModelMetaclass.__new__ = patched_new
    except: pass

def pytest_configure(config):
    """
    Hook to apply patches at the beginning of the pytest session.
    """
    patch_pydantic_v1()
    print("\n[HOOK] Pydantic v1 monkey-patch applied")

# Also apply immediately just in case collection starts before hook
patch_pydantic_v1()
