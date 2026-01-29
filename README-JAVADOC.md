# Hytale API Documentation

This directory contains auto-generated documentation for the Hytale Server API, extracted from `HytaleServer.jar`.

## Generation

To regenerate this documentation:

```bash
# Source environment variables (choose your machine)
source set_env-anduril.sh  # or set_env-sauron.sh

# Generate documentation
just generate-hytale-docs
```

Alternatively, run the script directly:

```bash
cd 00-Argonath-External-Docs
python3 extract_hytale_api.py
```

## Structure

- **[index.md](javadoc/index.md)** - Main documentation entry point
- **[index.classes.md](javadoc/index.classes.md)** - Browse all classes by package
- **[index.methods.md](javadoc/index.methods.md)** - Browse methods by class
- **Package directories** - Individual class documentation files organized by package structure

## Source

- **JAR Location**: Configured via `$HYTALE_SERVER_JAR` environment variable
- **Default Path**: `D:\Gaming\Hytales\install\release\package\game\latest\Server\HytaleServer.jar`

## Notes

- Documentation is generated using `javap` to inspect compiled class files
- Only Hytale-specific packages are included (filters out shaded dependencies)
- Each class documentation includes:
  - Full class definition
  - Fields
  - Constructors
  - Methods

## Dependencies

- Python 3.6+
- JDK (for `javap` tool)
- `HYTALE_SERVER_JAR` environment variable set

## Last Updated

Run `just generate-hytale-docs` to update this documentation to match your current HytaleServer.jar version.
