import os
import re
import csv
from pathlib import PurePath

#
# Search Directory
directory_to_search="/home/varacall/Desktop/CODE/deepfield-bootstrap/pipedream/ui/src/"

# temp file
temp_file="mui-audit-output.txt"
# output
output_file="mui-audit.txt"
output_file_csv="mui-audit.csv"

import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]@material-ui/core")

def extract_components_from_import(line):

    line = re.sub(r"s+", " ", line)
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
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
		
                # Search import patterns
                print(PurePath(file_path).parts)
                matches = import_pattern.finditer(content)
                for match in matches:
                    components = extract_components_from_import(match.group(0))
                    if file not in results:
                        results[file] = []
                    results[file].extend(components)
    return results


def write_results_to_file(results, output_file):
    

    with open(output_file, "w", encoding="utf-8") as f:
        for file, components in results.items():
            f.write(f" {file}\n")
            for component in set(components):
                f.write(f" {component}\n")

            f.write("\n")
            
def write_results_to_csv(results, output_file):
    mui5 = ['skeleton', 'list', 'menuitem', 'grey', 'accordion']
    with open(output_file, "w", newline='') as csvfile:
        cwriter = csv.writer(csvfile, delimiter=",")
        for file_name, components in results.items():
            c_list = "\n".join([s for s in set(components)])
            webb_list = []
            mui_list=[]
            for s in set(components):
               if s.lower() in mui5:
                   mui_list.append(s)
               else: webb_list.append(s)
            webb_list="\n".join(webb_list)
            mui_list="\n".join(mui_list)
            cwriter.writerow([file_name, webb_list, mui_list])
        

if __name__ == "__main__":
    results = search_files_for_imports(directory_to_search)
    write_results_to_file(results, output_file)
    write_results_to_csv(results, output_file_csv)
    print(f"Results written to {output_file}")
