from collections import defaultdict
import os
import re
import json
import argparse
import csv
from pathlib import PurePath

# output
output_file_json="mui-audit.json"
output_file_csv = "mui-audit.csv"

import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]@material-ui"
)
style_guide_import_pattern = re.compile(r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]style-guide/")
mui5_alternatives = [
    "skeleton",
    "list",
    "menuitem",
    "grey",
    "accordion",
    "listitem",
    "listitemtext",
    "listitemicon",
    "grid",
]

def extract_components_from_import(line):
    line = re.sub(r"\s+", " ", line)
    match = re.search(r"import\s+\{?([^}]*)\}?\s+from", line)
    if match:
        components = match.group(1).split(",")
        return [component.strip() for component in components]
    return []


def search_files_for_imports(directory):
    scan_dir = args.directory + "/ui/src"
    results = {}
    component_counts = defaultdict(int) # track frequency of components
    for root, _, files in os.walk(scan_dir):
        for file in files:
            if file.endswith((".js", ".mjs", ".jsx", ".ts", ".tsx")):
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Search import patterns
                matches = import_pattern.finditer(content)
                path_obj = PurePath(full_path)
                file_path = path_obj.relative_to(directory).parent.__fspath__()
                file_name = path_obj.name
                pd_path = "pipedream/" + file_path + "/" + file_name
                components = []
                for match in matches:
                    components.extend(extract_components_from_import(match.group(0)))
                if components:
                    # remove duplicates and sort
                    unique_components = sorted(set(components))
                    # check style guide 
                    has_style_guide = (
                        False
                        if style_guide_import_pattern.search(content) is None
                        else True
                    )
                    results[pd_path] = {
                        "imports":unique_components,
                        "name": file_name,
                        "path": pd_path,
                        "count": len(unique_components),
                        "has_style_guide": has_style_guide
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

def write_results_to_csv(results, output_file):
    with open(output_file, "w", newline="") as csvfile:
        cwriter = csv.writer(csvfile, delimiter=",")
        cwriter.writerow(
            [
                "Parent Path",
                "File Name",
                "Exists in Webb UI",
                "MUI 5",
                "Includes Style Guide",
            ]
        )
        for _, elements in results.items():
            components = elements["imports"]
            file_name = elements["name"]
            path_to_track = elements["path"]
            has_style_guide = elements["has_style_guide"]

            webb_list = []
            mui_list = []
            # evaluate which components do not exist in webb ui
            for s in set(components):
                if s.lower() in mui5_alternatives:
                    mui_list.append(s)
                else:
                    webb_list.append(s)
            webb_list = "\n".join(webb_list)
            mui_list = "\n".join(mui_list)
            cwriter.writerow(
                [path_to_track, file_name, webb_list, mui_list, has_style_guide]
            )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scan for Material UI imports in a directory")
    parser.add_argument("directory", type=str, help="Your pipedream directory")
    args = parser.parse_args()
    results, metadata = search_files_for_imports(args.directory)
    write_results_to_json(results, metadata, output_file_json)
    write_results_to_csv(results, output_file_csv)
