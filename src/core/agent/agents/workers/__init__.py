import importlib
import pkgutil

# Dynamically import all modules in this package
for _, module_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
