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
                    if 'unable to infer type' in str(e) or 'field constraints are set but not enforced' in str(e):
                        # Return a dummy field or similar
                        from pydantic.v1.fields import FieldInfo
                        from pydantic.v1.config import BaseConfig
                        
                        # args can vary depending on whether it's bound or not, but typically 
                        # cls, name, value, annotation, class_validators, config
                        config = BaseConfig
                        for arg in args:
                            if isinstance(arg, type) and issubclass(arg, BaseConfig):
                                config = arg
                                break
                                
                        return pydantic_fields.ModelField(
                            name=args[1] if len(args) > 1 else "unknown",
                            type_=typing.Any,
                            class_validators=None,
                            model_config=config,
                            default=None,
                            required=False,
                            alias="unknown",
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
