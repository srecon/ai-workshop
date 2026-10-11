import os
import re
import yaml
import hashlib
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from markitdown import MarkItDown, FileConversionException, UnsupportedFormatException

# ---- Fallback converter #1: mark-everything ----
try:
    import mark_everything
    MARK_EVERYTHING_AVAILABLE = True
except ImportError:
    MARK_EVERYTHING_AVAILABLE = False
    print("Warning: mark-everything not installed. Fallback #1 disabled.")
    print("Install it with: pip install mark-everything")

# ---- Fallback converter #2: unstructured ----
try:
    from unstructured.partition.pptx import partition_pptx
    from unstructured.partition.docx import partition_docx
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("Warning: unstructured not installed. Fallback #2 disabled.")
    print("Install it with: pip install 'unstructured[pptx,docx,pdf]'")

# Optional: For better NLP-based tagging
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("Warning: nltk not installed. Tag generation will use basic methods.")


class OKFGenerator:
    """Main class for generating OKF v0.2 compliant knowledge bundles."""

    def __init__(self, raw_dir="./raw_docs", bundle_dir="./knowledge", force_reprocess=False):
        self.raw_dir = raw_dir
        self.bundle_dir = bundle_dir
        self.state_file = os.path.join(bundle_dir, "file_tracking.yaml")
        self.conversion_state = {}
        self.md_converter = MarkItDown()
        self.supported_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.md', '.csv']

        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
                self.stop_words = set(stopwords.words('english'))
            except LookupError:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                self.stop_words = set(stopwords.words('english'))

        self.force_reprocess = force_reprocess
        self.file_relationships = defaultdict(list)

    # ------------------------------------------------------------------
    # Fallback-конвертер
    # ------------------------------------------------------------------
    def convert_with_fallback(self, file_path):
        """
        Пробует по очереди:
          1) MarkItDown
          2) mark-everything
          3) unstructured
        Возвращает строку Markdown.
        """
        # --- 1. Основной конвертер: MarkItDown ---
        try:
            result = self.md_converter.convert(file_path)
            return result.text_content
        except (FileConversionException, UnsupportedFormatException) as e:
            print(f"  ⚠ MarkItDown conversion failed for {file_path}: {e}")
        except Exception as e:
            print(f"  ⚠ MarkItDown unexpected error for {file_path}: {e}")

        # --- 2. Fallback: mark-everything ---
        if MARK_EVERYTHING_AVAILABLE:
            print(f"  ↻ Trying mark-everything for {file_path}...")
            try:
                md_text = self._call_mark_everything(file_path)
                if md_text and md_text.strip():
                    return md_text
                print("  ⚠ mark-everything returned empty content")
            except Exception as e:
                print(f"  ⚠ mark-everything failed: {e}")
        else:
            print("  ⚠ mark-everything is not installed, skipping this fallback")

        # --- 3. Fallback: unstructured ---
        if UNSTRUCTURED_AVAILABLE:
            print(f"  ↻ Trying unstructured for {file_path}...")
            try:
                md_text = self._call_unstructured(file_path)
                if md_text and md_text.strip():
                    return md_text
                print("  ⚠ unstructured returned empty content")
            except Exception as e:
                print(f"  ⚠ unstructured failed: {e}")
        else:
            print("  ⚠ unstructured is not installed, skipping this fallback")

        # --- Все конвертеры провалились ---
        raise RuntimeError(
            f"All converters (MarkItDown, mark-everything, unstructured) "
            f"failed for {file_path}"
        )

    def _call_mark_everything(self, file_path):
        """
        Вызывает mark-everything и извлекает текстовое содержимое.
        Возвращает строку Markdown.
        """
        import mark_everything

        result = None

        if hasattr(mark_everything, "convert"):
            result = mark_everything.convert(file_path)
        elif hasattr(mark_everything, "to_markdown"):
            result = mark_everything.to_markdown(file_path)
        elif hasattr(mark_everything, "markdown"):
            result = mark_everything.markdown(file_path)
        elif hasattr(mark_everything, "process"):
            result = mark_everything.process(file_path)
        elif hasattr(mark_everything, "Converter"):
            conv = mark_everything.Converter()
            if hasattr(conv, "convert"):
                result = conv.convert(file_path)

        if result is None:
            raise RuntimeError(
                "mark-everything is installed, but no known convert function was found."
            )

        # Отладочный вывод — покажет, что именно вернула библиотека
        print(f"  [DEBUG] mark_everything returned type: {type(result)}")
        try:
            attrs = [a for a in dir(result) if not a.startswith('_')]
            print(f"  [DEBUG] attributes: {attrs}")
        except Exception:
            pass

        # Извлекаем текст из ConversionResult
        if isinstance(result, str):
            return result

        if isinstance(result, bytes):
            return result.decode("utf-8", errors="replace")

        # Пробуем стандартные атрибуты
        for attr in ("text_content", "markdown", "text", "content"):
            if hasattr(result, attr):
                value = getattr(result, attr)
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")
                if isinstance(value, str):
                    return value

        # Крайний случай — str()
        return str(result)

    def _call_unstructured(self, file_path):
        """
        Использует библиотеку unstructured как последний fallback.
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pptx":
            elements = partition_pptx(filename=file_path)
        elif ext == ".docx":
            elements = partition_docx(filename=file_path)
        elif ext == ".pdf":
            elements = partition_pdf(filename=file_path)
        else:
            raise RuntimeError(f"unstructured does not support {ext}")

        # Склеиваем все элементы в Markdown-подобный текст
        parts = []
        for el in elements:
            text = str(el).strip()
            if text:
                parts.append(text)

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------
    def get_file_hash(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def load_conversion_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                try:
                    return yaml.safe_load(f) or {}
                except yaml.YAMLError:
                    return {}
        return {}

    def save_conversion_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.conversion_state, f, default_flow_style=False)

    # ------------------------------------------------------------------
    # Классификация и теги
    # ------------------------------------------------------------------
    def detect_document_type(self, content, file_name, rel_path):
        if 'api' in rel_path.lower() or 'endpoint' in rel_path.lower():
            return 'API Endpoint'
        elif 'table' in rel_path.lower() or 'dataset' in rel_path.lower():
            return 'BigQuery Table'
        elif 'metric' in rel_path.lower() or 'kpi' in rel_path.lower():
            return 'Metric'
        elif 'playbook' in rel_path.lower() or 'runbook' in rel_path.lower():
            return 'Playbook'
        elif 'reference' in rel_path.lower():
            return 'Reference'
        elif 'computation' in rel_path.lower() or 'compute' in rel_path.lower():
            return 'Attested Computation'

        if re.search(r'SELECT\s+.*\s+FROM\s+', content, re.IGNORECASE):
            return 'Attested Computation' if 'computation' in rel_path.lower() else 'Reference'
        elif re.search(r'^#\s+(?:Schema|Columns?|Fields?)', content, re.MULTILINE):
            return 'BigQuery Table'
        elif re.search(r'^(?:Step|Action|Procedure|Process)', content, re.MULTILINE):
            return 'Playbook'

        return 'Documentation Concept'

    def generate_auto_tags(self, content, file_name, doc_type):
        tags = set()
        tags.add(doc_type.lower().replace(' ', '_'))
        name_parts = re.sub(r'[^a-zA-Z0-9\s]', ' ', file_name).split()
        tags.update([part.lower() for part in name_parts if len(part) > 3])

        content_clean = re.sub(r'[^a-zA-Z\s]', ' ', content[:2000])
        words = content_clean.split()

        if NLTK_AVAILABLE and hasattr(self, 'stop_words'):
            try:
                tokens = word_tokenize(content_clean[:1000])
                filtered_words = [w.lower() for w in tokens
                                  if w.isalnum() and w.lower() not in self.stop_words and len(w) > 3]
                from collections import Counter
                common_words = Counter(filtered_words).most_common(5)
                tags.update([word for word, count in common_words if count > 1])
            except Exception:
                pass
        else:
            word_freq = {}
            for word in words:
                word_lower = word.lower()
                if len(word_lower) > 3 and word_lower not in {'this', 'that', 'with', 'from', 'have', 'are'}:
                    word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            for word, count in sorted_words[:5]:
                if count >= 2:
                    tags.add(word)

        if re.search(r'SELECT\s+.*\s+FROM\s+', content, re.IGNORECASE):
            tags.add('sql')
        if re.search(r'\{[^{}]+\}', content):
            tags.add('template')
        if re.search(r'#\S+', content):
            tags.add('code')

        return list(tags)[:10]

    # ------------------------------------------------------------------
    # Связи и чанки
    # ------------------------------------------------------------------
    def extract_relationships(self, content, source_path):
        relationships = []
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)

        for text, path in matches:
            if path.startswith('/'):
                target = path.lstrip('/')
                rel_path = os.path.relpath(target, os.path.dirname(source_path))
                if rel_path == '.':
                    rel_path = './'
            else:
                rel_path = path

            if not rel_path.startswith(('http://', 'https://')):
                rel_path = rel_path.split('#')[0].split('?')[0]
                if not rel_path.endswith('.md'):
                    rel_path = rel_path + '.md' if rel_path else ''

            relationships.append({
                'source': source_path,
                'target': rel_path,
                'text': text
            })

        return relationships

    def chunk_markdown_by_headings(self, md_text, token_target=1000):
        lines = md_text.split('\n')
        chunks = []
        current_chunk = []
        current_word_count = 0
        current_headings = []

        for line in lines:
            heading_match = re.match(r'^(#{1,4})\s+(.*)$', line)
            if heading_match:
                if current_word_count > token_target and current_chunk:
                    context = '\n'.join(current_headings[-2:]) if current_headings else ''
                    full_chunk = context + '\n' + '\n'.join(current_chunk)
                    chunks.append(full_chunk.strip())
                    current_chunk = [line]
                    current_word_count = len(line.split())
                    current_headings.append(line)
                else:
                    current_chunk.append(line)
                    current_word_count += len(line.split())
                    current_headings.append(line)
            else:
                current_chunk.append(line)
                current_word_count += len(line.split())

        if current_chunk:
            chunks.append('\n'.join(current_chunk).strip())

        final_chunks = []
        for chunk in chunks:
            if not re.search(r'^#{1,4}\s+', chunk, re.MULTILINE):
                first_line = chunk.split('\n')[0][:50]
                chunk = f"# {first_line}\n\n{chunk}"
            final_chunks.append(chunk)

        return final_chunks

    # ------------------------------------------------------------------
    # Сохранение OKF-концепта
    # ------------------------------------------------------------------
    def save_okf_concept(self, output_dir, source_name, index, content, ext_type, rel_path):
        os.makedirs(output_dir, exist_ok=True)
        slug = f"{source_name.lower().replace(' ', '_')}_part_{index}"
        file_path = os.path.join(output_dir, f"{slug}.md")

        title_match = re.search(r'^#{1,4}\s+(.*)$', content, re.MULTILINE)
        inferred_title = title_match.group(1) if title_match else f"{source_name} (Section {index})"

        clean_desc = re.sub(r'#+\s+', '', content[:200]).replace('\n', ' ').strip()
        clean_desc = clean_desc[:180] + "..." if len(clean_desc) > 180 else clean_desc

        doc_type = self.detect_document_type(content, source_name, rel_path)
        auto_tags = self.generate_auto_tags(content, source_name, doc_type)

        rel_path_with_index = os.path.join(os.path.dirname(rel_path), f"{slug}.md")
        relationships = self.extract_relationships(content, rel_path_with_index)

        frontmatter = {
            "type": doc_type,
            "title": inferred_title,
            "description": clean_desc,
            "resource": f"local://raw_docs/{rel_path}",
            "tags": auto_tags,
            "status": "draft",
            "generated": {
                "by": "reference_agent/markitdown-1.0",
                "at": datetime.now(timezone.utc).isoformat()
            },
            "sources": [
                {
                    "id": "source_document",
                    "resource": f"local://raw_docs/{rel_path}",
                    "title": f"Original source: {source_name}{ext_type}",
                    "last_modified": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                }
            ]
        }

        if doc_type == "Attested Computation" or "computation" in rel_path.lower():
            frontmatter.update({
                "runtime": self._detect_runtime(content),
                "parameters": self._extract_parameters(content),
                "executor": {
                    "resource": "references/skills/executor.md",
                    "receipt": ["job_id", "executed_code", "result"]
                },
                "attester": {
                    "resource": "references/attesters/validator.py"
                }
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            f.write("---\n\n")
            f.write(content)

        if relationships:
            self.file_relationships[rel_path_with_index].extend(relationships)

        return file_path

    def _detect_runtime(self, content):
        if re.search(r'SELECT\s+.*\s+FROM\s+', content, re.IGNORECASE):
            if 'dbt' in content.lower() or '{{' in content:
                return 'dbt'
            return 'bigquery'
        elif re.search(r'def\s+\w+\(', content):
            return 'python'
        return 'unknown'

    def _extract_parameters(self, content):
        parameters = []
        param_patterns = [
            r'@(\w+)',
            r'{{\s*var\(\'(\w+)\'\)\s*}}',
            r'\{(\w+)\}',
            r'<(\w+)>'
        ]

        found_params = set()
        for pattern in param_patterns:
            matches = re.findall(pattern, content)
            found_params.update(matches)

        for param in found_params:
            param_type = 'string'
            if re.search(r'year|date|time', param, re.IGNORECASE):
                param_type = 'integer'
            elif re.search(r'amount|total|sum|count', param, re.IGNORECASE):
                param_type = 'numeric'

            parameters.append({
                "name": param,
                "type": param_type,
                "required": True
            })

        return parameters[:5]

    # ------------------------------------------------------------------
    # Отслеживание изменений
    # ------------------------------------------------------------------
    def should_process_file(self, file_path):
        if self.force_reprocess:
            return True
        if file_path not in self.conversion_state:
            return True
        current_hash = self.get_file_hash(file_path)
        return current_hash != self.conversion_state[file_path]['hash']

    # ------------------------------------------------------------------
    # Граф знаний
    # ------------------------------------------------------------------
    def generate_knowledge_graph(self):
        if not self.file_relationships:
            return

        graph_data = {"nodes": set(), "edges": []}
        for source, rels in self.file_relationships.items():
            graph_data["nodes"].add(source)
            for rel in rels:
                if rel['target'] and not rel['target'].startswith(('http://', 'https://')):
                    graph_data["nodes"].add(rel['target'])
                    graph_data["edges"].append({
                        "source": source,
                        "target": rel['target'],
                        "label": rel['text'][:50]
                    })

        graph_path = os.path.join(self.bundle_dir, "knowledge_graph.json")
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump({
                "nodes": list(graph_data["nodes"]),
                "edges": graph_data["edges"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Generated knowledge graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")

    # ------------------------------------------------------------------
    # Основной процесс
    # ------------------------------------------------------------------
    def process_all(self):
        print(f"Starting OKF v0.2 generation...")
        print(f"Force reprocess: {self.force_reprocess}\n")

        if not os.path.exists(self.raw_dir):
            print(f"Error: Target directory '{self.raw_dir}' does not exist.")
            return

        self.conversion_state = self.load_conversion_state()

        processed_count = 0
        skipped_count = 0
        failed_count = 0

        for root, dirs, files in os.walk(self.raw_dir):
            for file in files:
                path = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                ext = ext.lower()

                if ext not in self.supported_extensions:
                    continue

                rel_path = os.path.relpath(path, self.raw_dir)
                rel_dir = os.path.dirname(rel_path)
                target_output_dir = os.path.join(self.bundle_dir, rel_dir, name)

                if not self.should_process_file(path):
                    print(f"Skipping (unchanged): {rel_path}")
                    skipped_count += 1
                    continue

                print(f"Processing: {rel_path}")
                try:
                    file_hash = self.get_file_hash(path)
                    raw_markdown = self.convert_with_fallback(path)

                    chunks = self.chunk_markdown_by_headings(raw_markdown)
                    generated_files = []

                    for i, chunk_content in enumerate(chunks):
                        output_path = self.save_okf_concept(
                            target_output_dir, name, i + 1, chunk_content, ext, rel_path
                        )
                        generated_files.append(output_path)

                    self.conversion_state[path] = {
                        'hash': file_hash,
                        'converted_at': datetime.now(timezone.utc).isoformat(),
                        'chunks_count': len(chunks),
                        'generated_files': generated_files,
                        'source_file': rel_path,
                        'doc_type': self.detect_document_type(raw_markdown, name, rel_path)
                    }

                    processed_count += 1
                    print(f"  ✓ Generated {len(chunks)} chunks for {rel_path}")

                except Exception as e:
                    failed_count += 1
                    print(f"  ✗ Failed to process file {rel_path}. Error: {e}")

        self.save_conversion_state()
        self.generate_knowledge_graph()
        self.generate_enhanced_indexes()

        print("\n" + "=" * 60)
        print("OKF v0.2 CONVERSION SUMMARY")
        print("=" * 60)
        print(f"Newly processed files: {processed_count}")
        print(f"Skipped (unchanged): {skipped_count}")
        print(f"Failed: {failed_count}")
        if self.force_reprocess:
            print("Mode: FORCE REPROCESS")
        print(f"Knowledge Graph: {os.path.join(self.bundle_dir, 'knowledge_graph.json')}")
        print("=" * 60)
        print("\nOKF v0.2 conversion pipeline successfully executed.")

    # ------------------------------------------------------------------
    # Индексы
    # ------------------------------------------------------------------
    def generate_enhanced_indexes(self):
        bundle_root = os.path.abspath(self.bundle_dir)

        for root, dirs, files in os.walk(bundle_root, topdown=False):
            if any(part.startswith('.') for part in root.split(os.sep)):
                continue

            markdown_entries = []
            subdirectory_entries = []

            for file in sorted(files):
                if file.endswith('.md') and file not in ['index.md', 'log.md']:
                    file_path = os.path.join(root, file)
                    metadata = self.parse_okf_frontmatter(file_path)

                    if metadata:
                        markdown_entries.append({
                            'file': file,
                            'title': metadata.get('title', file.replace('.md', '').replace('_', ' ').title()),
                            'description': metadata.get('description', 'No description provided.'),
                            'type': metadata.get('type', 'unknown'),
                            'status': metadata.get('status', 'stable'),
                            'tags': metadata.get('tags', [])
                        })

            for d in sorted(dirs):
                if d.startswith('.'):
                    continue

                child_idx_path = os.path.join(root, d, 'index.md')
                child_metadata = self.parse_okf_frontmatter(child_idx_path) if os.path.exists(child_idx_path) else {}

                sub_title = child_metadata.get('title', d.replace('_', ' ').title())
                sub_desc = child_metadata.get('description', f"Directory containing concepts related to {sub_title.lower()}.")

                subdirectory_entries.append({
                    'dir': f"{d}/index.md",
                    'title': sub_title,
                    'description': sub_desc
                })

            if markdown_entries or subdirectory_entries:
                current_folder_name = os.path.basename(root) if root != bundle_root else "Knowledge Bundle"
                index_path = os.path.join(root, 'index.md')

                index_title = f"{current_folder_name.replace('_', ' ').title()} Index"
                index_desc = f"Navigation index for {current_folder_name.replace('_', ' ')} concepts."

                yaml_frontmatter = {
                    'type': 'index',
                    'title': index_title,
                    'description': index_desc,
                }
                if root == bundle_root:
                    yaml_frontmatter['okf_version'] = '0.2'

                md_body = []

                if subdirectory_entries:
                    md_body.append("## 📁 Subdirectories\n")
                    for entry in subdirectory_entries:
                        md_body.append(f"* **[{entry['title']}]({entry['dir']})** - {entry['description']}")
                    md_body.append("")

                if markdown_entries:
                    md_body.append("## 📄 Concepts\n")
                    for entry in markdown_entries:
                        status_badge = f"`[{entry['status']}]`" if entry['status'] != 'stable' else ""
                        tags_str = f" `{', '.join(entry['tags'][:3])}`" if entry['tags'] else ""

                        md_body.append(
                            f"* **[{entry['title']}]({entry['file']})** {status_badge} "
                            f"`[{entry['type']}]`{tags_str} - {entry['description']}"
                        )

                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write("---\n")
                    yaml.dump(yaml_frontmatter, f, default_flow_style=False, sort_keys=False)
                    f.write("---\n\n")
                    f.write(f"# {index_title}\n\n")
                    f.write(f"*{index_desc}*\n\n")
                    f.write("\n".join(md_body))

    def parse_okf_frontmatter(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                data = yaml.safe_load(match.group(1))
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}


def main():
    force_reprocess = "--force" in sys.argv or "-f" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("OKF v0.2 Knowledge Bundle Generator")
        print("=" * 40)
        print("Usage: python okf_generator_v2.py [options]")
        print("Options:")
        print("  --force, -f    Force reprocess all files regardless of change status")
        print("  --help, -h     Show this help message")
        sys.exit(0)

    generator = OKFGenerator(
        raw_dir="./raw_docs",
        bundle_dir="./knowledge",
        force_reprocess=force_reprocess
    )
    generator.process_all()


if __name__ == "__main__":
    main()