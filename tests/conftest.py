import sys
import logging
import typing

def patch_pydantic_v1():
    """
    Patch Pydantic v1 for Python 3.14 compatibility.
    """
    print("Applying Pydantic v1 patch...")
    try:
        import pydantic.v1.main as pydantic_main
        import pydantic.v1.fields as pydantic_fields
        from pydantic.v1.errors import ConfigError
        
        # Patch ModelMetaclass.__new__
        original_new = pydantic_main.ModelMetaclass.__new__
        
        def patched_new(mcs, name, bases, namespace, **kwargs):
            try:
                return original_new(mcs, name, bases, namespace, **kwargs)
            except (ConfigError, TypeError, Exception) as e:
                err_msg = str(e)
                if 'unable to infer type' in err_msg:
                    # Generic fix: find the attribute it's complaining about
                    import re
                    match = re.search(r'attribute "([^"]+)"', err_msg)
                    if match:
                        attr_name = match.group(1)
                        if '__annotations__' not in namespace:
                            namespace['__annotations__'] = {}
                        namespace['__annotations__'][attr_name] = typing.Any
                        try:
                            return original_new(mcs, name, bases, namespace, **kwargs)
                        except:
                            pass
                raise
        
        pydantic_main.ModelMetaclass.__new__ = patched_new
        
        # Patch ModelField.infer
        if hasattr(pydantic_fields.ModelField, 'infer'):
            original_infer = pydantic_fields.ModelField.infer
            def patched_infer(*args, **kwargs):
                try:
                    return original_infer(*args, **kwargs)
                except Exception as e:
                    if 'unable to infer type' in str(e):
                        # Return a dummy field or similar
                        from pydantic.v1.fields import FieldInfo
                        return pydantic_fields.ModelField(
                            name=args[1] if len(args) > 1 else "unknown",
                            type_=typing.Any,
                            class_validators={},
                            model_config=args[4] if len(args) > 4 else None,
                            field_info=FieldInfo(),
                        )
                    raise
            pydantic_fields.ModelField.infer = patched_infer
            
        logging.getLogger(__name__).info("Successfully applied aggressive patch to pydantic.v1")
    except ImportError:
        pass
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to patch pydantic.v1: {e}")

# Apply patch immediately
patch_pydantic_v1()
