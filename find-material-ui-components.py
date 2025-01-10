from collections import defaultdict
import os
import re
import json
import argparse
import csv
from pathlib import PurePath

# output
output_file_json = "mui-audit.json"
output_file_csv = "mui-audit.csv"

import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]@material-ui"
)
style_guide_import_pattern = re.compile(
    r"import\s+(\{[^\}]*\}|[a-zA-Z0-0_]+)\s+from\s+['\"]style-guide/"
)
mui5_alternatives = [
    "skeleton",
    "menuitem",
    "accordion",
    "accordiondetails",
    "accordionsummary",
    "fade",
    "list",
    "listitem",
    "listitemtext",
    "listitemicon",
    "listsubheader",
    "grid",
    "makestyles",
    "withstyles",
    "circularprogress",
    "togglebutton",
    "togglebuttongroup",
    "radiogroup",
    "formcontrol",
    # ~colors
    "grey",
    "deeppurple"
    # ~icons
    "inputadornment",
    "arrowforward",
    "arrowdropdown",
    "arrowupward",
    "autorenew",
    "accountcircle",
    "barchart",
    "collapse",
    "deleteoutline",
    "donutlarge",
    "email",
    "erroroutline",
    "expandmore",
    "flashon",
    "lockopen",
    "keyboardarrowdown",
    "showchart",
    "tablechartoutlined",
    "subdirectoryarrowleft",
    "verifieduseroutlined",
    "verticalsplit",
    "slide",
    "stoptwotone",
]


def remove_empty_results(item):
    return item is not None and item != "" and item != " "


def extract_components_from_import(line):
    line = re.sub(r"\s+", " ", line)
    match = re.search(r"import\s+\{?([^}]*)\}?\s+from", line)
    if match:
        components = list(filter(remove_empty_results, match.group(1).split(",")))
        return [component.strip() for component in components]
    return []


def search_files_for_imports(directory):
    scan_dir = args.directory + "/ui/src"
    results = {}
    component_counts = defaultdict(int)  # track frequency of components
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
                        "imports": unique_components,
                        "name": file_name,
                        "path": pd_path.replace("pipedream/", ""),
                        "count": len(unique_components),
                        "has_style_guide": has_style_guide,
                    }
                    for component in unique_components:
                        component_counts[component] += 1
    metadata = {
        "component_frequency": sorted(
            [
                {"name": comp, "frequency": freq}
                for comp, freq in component_counts.items()
            ],
            key=lambda x: x["frequency"],
            reverse=True,
        )
    }
    return results, metadata


def write_results_to_json(results, metadata, output_file):
    data = {"files": results, "metadata": metadata}
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Finished writing JSON Results ✔️")


def get_m_col(row, index, max_index, compare_val):
    loop = max_index - index
    text = row[index] if loop == 0 else None
    for l in range(loop):
        text = row[index + l] if text is None else text + " " + row[index + l]

    return text if compare_val == "" else compare_val + "\n" + text


def get_manual_results_initial():
    manual_results = []
    with open("documents/ManualReviewInitial.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=",", quotechar="|")
        current_file = None
        copy_manual_review = {
            "component": current_file,
            "mui": "",
            "webb": "",
            "notes": "",
        }

        manual_review = copy_manual_review.copy()
        for row in spamreader:
            if len(row) < 7:
                # special comments
                comments = " ".join(row)
                manual_review["notes"] = manual_review["notes"] + "\n" + comments
            else:
                component = row[0]

                # keep getting values
                if component == "":
                    manual_review["webb"] = get_m_col(row, 1, 3, manual_review["webb"])
                    manual_review["mui"] = get_m_col(row, 4, 5, manual_review["mui"])
                    manual_review["notes"] = get_m_col(
                        row, 7, 7, manual_review["notes"]
                    )

                else:
                    # terminate
                    manual_results.append(manual_review)

                    # and then start to get new values
                    current_file = component
                    manual_review = copy_manual_review.copy()
                    manual_review["component"] = current_file
                    manual_review["webb"] = get_m_col(row, 1, 3, manual_review["webb"])
                    manual_review["mui"] = get_m_col(row, 4, 5, manual_review["mui"])
                    manual_review["notes"] = get_m_col(
                        row, 7, 7, manual_review["notes"]
                    )

        manual_results.append(manual_review)
    return manual_results


def write_results_to_csv(results, metadata, output_file):
    with open("metadata_" + output_file, "w", newline="") as csvfile:
        cwriter = csv.writer(csvfile, delimiter=",")
        cwriter.writerow(
            [
                "Name",
                "Frequency",
            ]
        )
        for elements in metadata["component_frequency"]:
            name = elements["name"]
            freq = elements["frequency"]

            cwriter.writerow([name, freq])

    manual_results = get_manual_results_initial()
    with open(output_file, "w", newline="") as csvfile:
        cwriter = csv.writer(csvfile, delimiter=",")
        cwriter.writerow(
            [
                "Parent Path",
                "File Name",
                "Exists in Webb UI",
                "MUI 5",
                "Total Components",
                "Includes Style Guide",
                "Additional Details",
            ]
        )
        for _, elements in results.items():
            components = elements["imports"]
            file_name = elements["name"]
            path_to_track = elements["path"]
            has_style_guide = elements["has_style_guide"]
            total_components = elements["count"]

            manual_details = next(
                (item for item in manual_results if item["component"] == path_to_track),
                None,
            )
            notes = None
            m_mui = None
            m_webb = None
            if manual_details is not None:
                notes = manual_details["notes"]
                m_mui = manual_details["mui"]
                m_webb = manual_details["webb"]

            webb_list = []
            mui_list = []
            # evaluate which components do not exist in webb ui
            for s in set(components):
                sl = s.lower()
                if sl is not None and sl != "":
                    if m_mui is not None and any(sl in s for s in m_mui):
                        matching = [s for s in m_mui if sl in s]
                        mui_list.append(matching)
                    elif sl in mui5_alternatives:
                        mui_list.append(s)
                    elif m_webb is not None and any(sl in s for s in m_webb):
                        matching = [s for s in m_webb if sl in s]
                        webb_list.append(m_webb)
                    else:
                        webb_list.append(s)
            webb_list = "\n".join(webb_list)
            mui_list = "\n".join(mui_list)
            notes = (
                notes
                if m_webb is None
                else notes + "\n\n Webb UI Related Notes:\n" + m_webb
            )
            cwriter.writerow(
                [
                    path_to_track,
                    file_name,
                    webb_list,
                    mui_list,
                    total_components,
                    has_style_guide,
                    notes,
                ]
            )
    print(f"Finished writing CSV Results ✔️")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan for Material UI imports in a directory"
    )
    parser.add_argument("directory", type=str, help="Your pipedream directory")
    args = parser.parse_args()
    results, metadata = search_files_for_imports(args.directory)

    write_results_to_json(results, metadata, output_file_json)
    write_results_to_csv(results, metadata, output_file_csv)
