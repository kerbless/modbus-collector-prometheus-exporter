#!/usr/bin/env python3
"""Validate YAML files against OpenModbus schema"""

import json
import sys
from pathlib import Path

try:
    import yaml
    import jsonschema
except ImportError:
    print("Error: Required Python packages not installed")
    print("Install with: pip3 install pyyaml jsonschema")
    sys.exit(1)

# Common type aliases that should suggest corrections
TYPE_ALIASES = {
    'short': 'int16',
    'ushort': 'uint16',
    'int': 'int32',
    'uint': 'uint32',
    'long': 'int64',
    'long64': 'int64',
    'ulong': 'uint64',
    'ulong64': 'uint64',
    'float': 'float32',
    'double': 'float64',
    'byte': 'int8',
    'char': 'uint8',
}

def suggest_type_correction(value):
    """Suggest correction for common type aliases"""
    if value in TYPE_ALIASES:
        return TYPE_ALIASES[value]
    return None

def validate_file(yaml_path, schema):
    """Validate a single YAML file against the schema"""
    print(f"Validating: {yaml_path.name}")

    # Load YAML
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # Validate
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"  ✓ PASS")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"  ✗ FAIL")
        print(f"    {e.message}")
        if e.path:
            print(f"    Path: {' -> '.join(str(p) for p in e.path)}")

        # Check if this is a type enum error and suggest correction
        if "is not one of" in e.message and len(e.path) >= 2:
            # Path is typically: ['registers', '0', 'type']
            path_list = list(e.path)
            if len(path_list) >= 3 and path_list[0] == 'registers' and path_list[2] == 'type':
                register_addr = path_list[1]
                if 'registers' in data and register_addr in data['registers']:
                    invalid_type = data['registers'][register_addr].get('type')
                    if invalid_type:
                        suggestion = suggest_type_correction(invalid_type)
                        if suggestion:
                            print(f"    💡 Did you mean '{suggestion}'?")

        return False

def main():
    print("OpenModbus Schema Validation")
    print("=" * 50)
    print()

    # Load schema
    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / "schema" / "openmodbus-schema-v0.3.0.json"
    with open(schema_path) as f:
        schema = json.load(f)

    print(f"Schema: {schema_path}")
    print()

    # Find all YAML files in registry directory
    registry_dir = repo_root / "devices"
    yaml_files = list(registry_dir.rglob("*.yaml"))

    passed = 0
    failed = 0

    for yaml_file in sorted(yaml_files):
        if validate_file(yaml_file, schema):
            passed += 1
        else:
            failed += 1
        print()

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print()

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
