from collections import defaultdict
import os
import re
import json

# Search Directory
directory_to_search="/home/nreynold/repos/deepfield-bootstrap/pipedream/ui/src/"

# temp file
temp_file="mui-audit-output.txt"
# output
output_file="mui-audit.json"

import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]@material-ui"
)

def extract_components_from_import(line):
    line = re.sub(r"\s+", " ", line)
    match = re.search(r"import\s+\{?([^}]*)\}?\s+from", line)
    if match:
        components = match.group(1).split(",")
        return [component.strip() for component in components]
    return []


def search_files_for_imports(directory):
    results = {}
    component_counts = defaultdict(int) # track frequency of components
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".js", ".mjs", ".jsx", ".ts", ".tsx")):
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Search import patterns
                matches = import_pattern.finditer(content)
                file_path = full_path.split('deepfield-bootstrap/')[1]
                components = []
                for match in matches:
                    components.extend(extract_components_from_import(match.group(0)))
                if components:
                    # remove duplicates and sort
                    unique_components = sorted(set(components))
                    results[file_path] = {
                        "imports":unique_components,
                        "count": len(unique_components)
                    }
                    for component in unique_components:
                        component_counts[component] += 1
    metadata = {
        "component_frequency" : sorted(
            [{"name": comp, "frequency": freq} for comp, freq in component_counts.items()],
            key=lambda x: x["frequency"],
            reverse=True
        )
    }
    return results, metadata


def write_results_to_json(results, metadata, output_file):
    
    data = {
        "files": results,
        "metadata": metadata
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def write_results_to_txt_file(results, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        for file, components in results.items():
            f.write(f" {file}\n")
            for component in set(components):
                f.write(f" {component}\n")

            f.write("\n")


if __name__ == "__main__":
    results, metadata = search_files_for_imports(directory_to_search)
    write_results_to_json(results, metadata, output_file)
