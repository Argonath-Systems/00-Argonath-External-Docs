#!/usr/bin/env python3
"""
Hytale API Documentation Extractor

This script extracts Hytale API documentation from HytaleServer.jar
and generates Markdown documentation files organized by package structure.

Usage:
    python extract_hytale_api.py

Requirements:
    - HYTALE_SERVER_JAR environment variable must be set
    - javap tool must be available (comes with JDK)
    - Python 3.6+

Output:
    Markdown files in ./javadoc/ directory
"""

import os
import sys
import subprocess
import zipfile
import shutil
import time
import concurrent.futures
from pathlib import Path
from collections import defaultdict

# --- Configuration ---
DOCS_OUTPUT_DIR = Path(__file__).parent / "javadoc"
HYTALE_SERVER_JAR = os.environ.get("HYTALE_SERVER_JAR")

if not HYTALE_SERVER_JAR:
    print("Error: HYTALE_SERVER_JAR environment variable is not set.")
    print("Please source set_env-*.sh before running this script.")
    sys.exit(1)

if not os.path.exists(HYTALE_SERVER_JAR):
    print(f"Error: Hytale Server JAR not found at: {HYTALE_SERVER_JAR}")
    sys.exit(1)

def clean_javadoc_dir():
    """Clean and recreate the javadoc output directory."""
    if DOCS_OUTPUT_DIR.exists():
        shutil.rmtree(DOCS_OUTPUT_DIR)
    DOCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Cleaned {DOCS_OUTPUT_DIR}")

def get_classes_from_jar(jar_path):
    """Extract list of Hytale API class names from JAR file."""
    classes = []
    print(f"📦 Reading classes from {jar_path}...")
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file_info in jar.infolist():
                if file_info.filename.endswith(".class"):
                    # Convert path to class name (e.g., com/example/Foo.class -> com.example.Foo)
                    class_name = file_info.filename.replace("/", ".").replace(".class", "")
                    
                    # Filter for Hytale specific classes only
                    # Exclude shaded libraries like fastutil, netty, etc.
                    if class_name.startswith("com.hypixel.hytale") or class_name.startswith("hytale."): 
                         classes.append(class_name)
    except Exception as e:
        print(f"❌ Error reading JAR file: {e}")
        sys.exit(1)
    
    print(f"✓ Found {len(classes)} Hytale API classes")
    return sorted(classes)

def run_javap(class_name):
    """Run javap to get class information."""
    try:
        # Run javap with private members (-p) and classpath
        result = subprocess.run(
            ["javap", "-p", "-cp", HYTALE_SERVER_JAR, class_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        # Suppress output for expected failures (missing dependencies etc)
        return None

def generate_markdown(class_name, javap_output):
    """Generate Markdown documentation from javap output."""
    lines = javap_output.strip().split('\n')
    if not lines:
        return None, []

    # Title
    content = f"# {class_name}\n\n"
    
    # Collect methods for index
    methods = []
    fields = []
    constructors = []
    
    content += "## Definition\n\n```java\n"
    
    in_class_body = False
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith("Compiled from"):
            continue
        
        content += line + "\n"
        
        # Parse members for index
        if "{" in line:
            in_class_body = True
        
        if in_class_body and "(" in line_stripped and ")" in line_stripped:
            if not line_stripped.startswith("static {}"):
                clean_line = line_stripped.replace(";", "").strip()
                if class_name.split(".")[-1] in clean_line:
                    constructors.append(clean_line)
                else:
                    methods.append(clean_line)
        elif in_class_body and "=" not in line_stripped and "(" not in line_stripped:
            if any(keyword in line_stripped for keyword in ["public", "private", "protected", "static", "final"]):
                clean_line = line_stripped.replace(";", "").strip()
                if clean_line and not clean_line.startswith("class") and not clean_line.startswith("interface"):
                    fields.append(clean_line)
    
    content += "```\n\n"
    
    # Add structured sections
    if fields:
        content += "## Fields\n\n"
        for field in fields:
            content += f"- `{field}`\n"
        content += "\n"
    
    if constructors:
        content += "## Constructors\n\n"
        for ctor in constructors:
            content += f"- `{ctor}`\n"
        content += "\n"
    
    if methods:
        content += "## Methods\n\n"
        for method in methods:
            content += f"- `{method}`\n"
        content += "\n"
    
    if not (fields or constructors or methods):
        content += "## Members\n\nNo public members found or unable to parse.\n\n"
        
    return content, methods

def write_class_doc(class_name, content):
    """Write class documentation to file."""
    # Determine file path based on package structure
    parts = class_name.split(".")
    
    # Create directory structure: com/hypixel/hytale/...
    class_dir = DOCS_OUTPUT_DIR.joinpath(*parts[:-1])
    try:
        class_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass  # Thread race condition safety
    
    file_path = class_dir / f"{parts[-1]}.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return file_path

def process_single_class(cls):
    """Worker function for parallel processing."""
    javap_out = run_javap(cls)
    if javap_out:
        md_content, methods = generate_markdown(cls, javap_out)
        if md_content:
            write_class_doc(cls, md_content)
            return cls, methods
    return cls, None

def create_indexes(classes, method_registry):
    """Create index files for easy navigation."""
    print("\n📝 Generating indexes...")
    
    # Root Index
    with open(DOCS_OUTPUT_DIR / "index.md", "w", encoding="utf-8") as f:
        f.write("# Hytale Server API Documentation\n\n")
        f.write(f"Generated from HytaleServer.jar using `javap` output.\n\n")
        f.write(f"**Total Classes:** {len(classes)}\n\n")
        f.write("## Navigation\n\n")
        f.write("- [Class Index](index.classes.md) - Browse by package\n")
        f.write("- [Method Index](index.methods.md) - Browse by class methods\n\n")
        f.write("## Quick Links\n\n")
        
        # Group by top-level package
        packages = defaultdict(int)
        for cls in classes:
            pkg = ".".join(cls.split(".")[:3]) if len(cls.split(".")) >= 3 else cls.split(".")[0]
            packages[pkg] += 1
        
        f.write("### Packages\n\n")
        for pkg in sorted(packages.keys()):
            count = packages[pkg]
            f.write(f"- `{pkg}` ({count} classes)\n")
        
    # Class Index
    with open(DOCS_OUTPUT_DIR / "index.classes.md", "w", encoding="utf-8") as f:
        f.write("# Class Index\n\n")
        f.write("All Hytale API classes organized by package.\n\n")
        
        current_package = ""
        for cls in classes:
            package = ".".join(cls.split(".")[:-1])
            simple_name = cls.split(".")[-1]
            
            if package != current_package:
                f.write(f"\n## {package}\n\n")
                current_package = package
            
            # Relative link
            link_path = cls.replace(".", "/") + ".md"
            f.write(f"- [{simple_name}]({link_path})\n")

    # Method Index 
    with open(DOCS_OUTPUT_DIR / "index.methods.md", "w", encoding="utf-8") as f:
        f.write("# Method Index\n\n")
        f.write("All classes with their public methods.\n\n")
        
        for cls in classes:
            if cls not in method_registry:
                continue
            
            methods = method_registry[cls]
            if not methods:
                continue

            link_path = cls.replace(".", "/") + ".md"
            f.write(f"### [{cls}]({link_path})\n\n")
            
            for method in methods:
                f.write(f"- `{method}`\n")
            f.write("\n")
    
    print("✓ Indexes created")

def main():
    """Main execution function."""
    print("=" * 80)
    print("Hytale API Documentation Extractor")
    print("=" * 80)
    print(f"JAR: {HYTALE_SERVER_JAR}")
    print(f"Output: {DOCS_OUTPUT_DIR}")
    print()
    
    clean_javadoc_dir()
    classes = get_classes_from_jar(HYTALE_SERVER_JAR)
    
    if not classes:
        print("❌ No Hytale classes found in JAR")
        sys.exit(1)
    
    method_registry = {}  # class -> [methods]

    print(f"\n🔨 Generating docs for {len(classes)} classes using {os.cpu_count() * 2} workers...")
    print()
    
    start_time = time.time()
    processed_count = 0
    success_count = 0
    total = len(classes)
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        future_to_class = {executor.submit(process_single_class, cls): cls for cls in classes}
        
        for future in concurrent.futures.as_completed(future_to_class):
            cls = future_to_class[future]
            try:
                processed_cls, methods = future.result()
                if methods is not None:
                    method_registry[processed_cls] = methods
                    success_count += 1
            except Exception as exc:
                print(f'\n❌ {cls} generated an exception: {exc}')
            
            processed_count += 1
            if processed_count % 100 == 0 or processed_count == total:
                elapsed = time.time() - start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                remaining = (total - processed_count) / rate if rate > 0 else 0
                # \r to overwrite line
                sys.stdout.write(
                    f"\r   Progress: {processed_count}/{total} "
                    f"({processed_count/total*100:.1f}%) - "
                    f"{rate:.1f} classes/sec - "
                    f"Est. remaining: {remaining:.0f}s"
                )
                sys.stdout.flush()

    print()  # New line after progress
    create_indexes(classes, method_registry)
    
    elapsed = time.time() - start_time
    print()
    print("=" * 80)
    print(f"✅ Documentation generation complete!")
    print(f"   Processed: {processed_count} classes")
    print(f"   Success: {success_count} classes")
    print(f"   Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"   Output: {DOCS_OUTPUT_DIR.absolute()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
