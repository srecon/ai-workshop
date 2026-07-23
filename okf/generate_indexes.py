import os
import re
import yaml

def parse_okf_frontmatter(file_path):
    """Parses the YAML frontmatter from an OKF Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            frontmatter_text = match.group(1)
            data = yaml.safe_load(frontmatter_text)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"Warning: Failed to parse frontmatter in {file_path}. Error: {e}")
    return {}

def generate_okf_indexes(bundle_root):
    """Recursively generates an index.md file for every directory containing OKF concepts."""
    bundle_root = os.path.abspath(bundle_root)

    # Walk bottom-up so child directory index.md files exist before parents index them
    for root, dirs, files in os.walk(bundle_root, topdown=False):
        # Don't index hidden directories
        if any(part.startswith('.') for part in root.split(os.sep)):
            continue

        markdown_entries = []
        subdirectory_entries = []

        # 1. Parse child Markdown files in the current folder
        for file in sorted(files):
            if file.endswith('.md') and file != 'index.md' and file != 'log.md':
                file_path = os.path.join(root, file)
                metadata = parse_okf_frontmatter(file_path)

                title = metadata.get('title', file.replace('.md', '').replace('_', ' ').title())
                description = metadata.get('description', 'No description provided.')
                doc_type = metadata.get('type', 'unknown')

                markdown_entries.append({
                    'file': file,
                    'title': title,
                    'description': description,
                    'type': doc_type
                })

        # 2. Parse child subdirectories in the current folder
        for d in sorted(dirs):
            if d.startswith('.'):
                continue

            child_idx_path = os.path.join(root, d, 'index.md')
            child_metadata = parse_okf_frontmatter(child_idx_path) if os.path.exists(child_idx_path) else {}

            sub_title = child_metadata.get('title', d.replace('_', ' ').title())
            sub_desc = child_metadata.get('description', f"Directory containing concepts related to {sub_title.lower()}.")

            subdirectory_entries.append({
                'dir': f"{d}/index.md",
                'title': sub_title,
                'description': sub_desc
            })

        # 3. Write out the index.md file if this directory contains any entries
        if markdown_entries or subdirectory_entries:
            current_folder_name = os.path.basename(root) if root != bundle_root else "Root Knowledge"
            index_path = os.path.join(root, 'index.md')

            index_title = f"{current_folder_name.replace('_', ' ').title()} Index"
            index_desc = f"Navigation index for {current_folder_name.replace('_', ' ')} concepts."

            yaml_frontmatter = {
                'type': 'index',
                'title': index_title,
                'description': index_desc,
            }

            md_body = []
            if subdirectory_entries:
                md_body.append("## Subdirectories\n")
                for entry in subdirectory_entries:
                    md_body.append(f"* **[{entry['title']}]({entry['dir']})** - {entry['description']}")
                md_body.append("")

            if markdown_entries:
                md_body.append("## Concepts\n")
                for entry in markdown_entries:
                    md_body.append(f"* **[{entry['title']}]({entry['file']})** `[{entry['type']}]` - {entry['description']}")

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(yaml_frontmatter, f, default_flow_style=False, sort_keys=False)
                f.write("---\n\n")
                f.write(f"# {index_title}\n\n")
                f.write("\n".join(md_body))

            print(f"Generated Map: {os.path.relpath(index_path, bundle_root)}")

if __name__ == "__main__":
    # Pointing directly to your active knowledge folder location
    TARGET_BUNDLE_DIR = "./knowledge"

    if os.path.exists(TARGET_BUNDLE_DIR):
        print(f"Compiling OKF directory structure inside: {TARGET_BUNDLE_DIR}\n")
        generate_okf_indexes(TARGET_BUNDLE_DIR)
        print("\nStructure successfully mapped.")
    else:
        print(f"Error: Path '{TARGET_BUNDLE_DIR}' could not be located.")
