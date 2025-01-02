import os
import re
import json


#
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
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".js", ".mjs", ".jsx", ".ts", ".tsx")):
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Search import patterns
                matches = import_pattern.finditer(content)
                file_path = full_path.split('deepfield-bootstrap/')[1]
                for match in matches:
                    components = extract_components_from_import(match.group(0))
                    if file_path not in results:
                        results[file_path] = []
                    results[file_path].extend(components)
        for file in results:
            results[file] = sorted(set(results[file]))
    return results


def write_results_to_json(results, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)


def write_results_to_txt_file(results, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        for file, components in results.items():
            f.write(f" {file}\n")
            for component in set(components):
                f.write(f" {component}\n")

            f.write("\n")

if __name__ == "__main__":
    results = search_files_for_imports(directory_to_search)
    write_results_to_json(results, output_file)
