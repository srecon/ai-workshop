import os
import re
import yaml
from markitdown import MarkItDown

def chunk_markdown_by_headings(md_text, token_target=1000):
    """
    Splits long Markdown text into atomic chunks based on headers (#, ##, ###).
    Attempts to group sections together up to an approximate word/token boundary.
    """
    lines = md_text.split('\n')
    chunks = []
    current_chunk = []
    current_word_count = 0

    for line in lines:
        if re.match(r'^#{1,4}\s+', line) and current_word_count > token_target:
            chunks.append("\n".join(current_chunk).strip())
            current_chunk = []
            current_word_count = 0

        current_chunk.append(line)
        current_word_count += len(line.split())

    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())

    return [c for c in chunks if c.strip()]

def save_okf_concept(output_dir, source_name, index, content, ext_type, rel_path):
    """
    Saves a text segment as an atomic OKF file with compliant YAML frontmatter.
    Preserves the relative directory structure inside the bundle folder.
    """
    os.makedirs(output_dir, exist_ok=True)
    slug = f"{source_name.lower().replace(' ', '_')}_part_{index}"
    file_path = os.path.join(output_dir, f"{slug}.md")

    title_match = re.search(r'^#{1,4}\s+(.*)$', content, re.MULTILINE)
    inferred_title = title_match.group(1) if title_match else f"{source_name} (Section {index})"

    clean_desc = re.sub(r'#+\s+', '', content[:180]).replace('\n', ' ').strip() + "..."

    frontmatter = {
        "type": "documentation_concept",
        "title": inferred_title,
        "description": clean_desc,
        "resource": f"local://raw_docs/{rel_path}",
        "tags": [ext_type.replace('.', ''), "migrated_docs"]
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False)
        f.write("---\n\n")
        f.write(content)

def process_all():
    # Updated paths to reflect your specific directory layout
    raw_dir = "./raw_docs"
    bundle_dir = "./knowledge"

    md_converter = MarkItDown()

    if not os.path.exists(raw_dir):
        print(f"Error: Target directory '{raw_dir}' does not exist.")
        return

    supported_extensions = ['.pdf', '.docx', '.pptx']

    # Use os.walk to recursively search all subdirectories like base/raw_docs/PB
    for root, dirs, files in os.walk(raw_dir):
        for file in files:
            path = os.path.join(root, file)
            name, ext = os.path.splitext(file)
            ext = ext.lower()

            if ext not in supported_extensions:
                continue

            # Calculate the relative path from base/raw_docs to maintain structure
            rel_path = os.path.relpath(path, raw_dir)
            rel_dir = os.path.dirname(rel_path)

            # Place the processed files in a matching directory structure under base/knowledge
            target_output_dir = os.path.join(bundle_dir, rel_dir, name)

            print(f"Converting: {rel_path}")
            try:
                result = md_converter.convert(path)
                raw_markdown = result.text_content

                chunks = chunk_markdown_by_headings(raw_markdown)

                for i, chunk_content in enumerate(chunks):
                    save_okf_concept(target_output_dir, name, i + 1, chunk_content, ext, rel_path)

            except Exception as e:
                print(f"Failed to process file {rel_path}. Error trace: {e}")

if __name__ == "__main__":
    process_all()
    print("\nOKF Markdown conversion pipeline successfully executed.")
