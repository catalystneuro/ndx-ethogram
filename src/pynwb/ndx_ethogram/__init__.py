from importlib.resources import files
from pynwb import load_namespaces, get_class

# This extension depends on ndx-pose for the `source_pose` link target (PoseEstimation);
# importing it registers that namespace so this one can load.
import ndx_pose  # noqa: F401

# Get path to the namespace.yaml file with the expected location when installed not in editable mode
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-ethogram.namespace.yaml"

# If that path does not exist, we are likely running in editable mode. Use the local path instead
if not __spec_path.exists():
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-ethogram.namespace.yaml"

# Load the namespace
load_namespaces(str(__spec_path))

# EthogramBouts: a TimeIntervals subclass; one row per behavioral bout (the timeline).
EthogramBouts = get_class("EthogramBouts", "ndx-ethogram")
# Ethogram: a DynamicTable; one row per behavior type (the catalogue / coding scheme).
Ethogram = get_class("Ethogram", "ndx-ethogram")

__all__ = [
    "EthogramBouts",
    "Ethogram",
]

# Remove these functions/modules from the package
del load_namespaces, get_class, files, __location_of_this_file, __spec_path
