import os
import re
import csv
from pathlib import PurePath

#
# Search Directory
directory_to_search = (
    "/home/varacall/Desktop/CODE/deepfield-bootstrap/pipedream/ui/src/"
)

# temp file
temp_file = "mui-audit-output.txt"
# output
output_file = "mui-audit.txt"
output_file_csv = "mui-audit.csv"

import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]@material-ui"
)
style_guide_import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]style-guide/"
)

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
    results = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".js", ".mjs", ".jsx", ".ts", ".tsx")):
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Search import patterns
                path_to_track = "/".join(PurePath(full_path).parts[9:-1])
                clean_path = path_to_track + "/" + file
                matches = import_pattern.finditer(content)
                has_style_guide = (
                    False
                    if style_guide_import_pattern.search(content) is None
                    else True
                )

                for match in matches:
                    components = extract_components_from_import(match.group(0))
                    if clean_path not in results:
                        results[clean_path] = {
                            "file": file,
                            "path": path_to_track,
                            "components": [],
                            "has-style-guide": has_style_guide,
                        }
                    results[clean_path]["components"].extend(components)
    return results


def compare_with_notes(file_path):
    return ""


def write_results_to_file(results, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for file, components in results.items():
            f.write(f" {file}\n")
            for component in set(components):
                f.write(f" {component}\n")

            f.write("\n")


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
            components = elements["components"]
            file_name = elements["file"]
            path_to_track = elements["path"]
            has_style_guide = elements["has-style-guide"]

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
    results = search_files_for_imports(directory_to_search)
    write_results_to_file(results, output_file)
    print(f"Results written to {output_file}")
    write_results_to_csv(results, output_file_csv)
    print(f"CSV Results written to {output_file_csv}")
