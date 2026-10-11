import os
import re
import yaml
import json  # <-- Added this import
from datetime import datetime, timezone
from collections import defaultdict

class OKFIndexGenerator:
    """Generates OKF v0.2 compliant index.md files with rich metadata."""
    
    def __init__(self, bundle_root="./knowledge"):
        self.bundle_root = os.path.abspath(bundle_root)
        self.knowledge_graph = defaultdict(list)
        self.stats = {
            'total_dirs': 0,
            'total_concepts': 0,
            'total_indexes': 0,
            'deprecated_concepts': 0
        }
        
    def parse_okf_frontmatter(self, file_path):
        """Parses the YAML frontmatter from an OKF Markdown file with v0.2 support."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Handle frontmatter with optional whitespace
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                frontmatter_text = match.group(1)
                data = yaml.safe_load(frontmatter_text)
                if isinstance(data, dict):
                    # Parse verified field - can be single mapping or list
                    if 'verified' in data:
                        if isinstance(data['verified'], dict):
                            data['verified'] = [data['verified']]
                    
                    # Add file path to metadata for context
                    data['_file_path'] = file_path
                    return data
        except Exception as e:
            print(f"  ⚠️  Warning: Failed to parse frontmatter in {os.path.basename(file_path)}. Error: {e}")
        return {}
    
    def get_trust_tier(self, metadata):
        """Derive trust tier from verified field per OKF v0.2 §5.3."""
        if 'verified' not in metadata:
            return 'unverified'
        
        if not isinstance(metadata['verified'], list):
            return 'unverified'
        
        # Check if any human has verified
        for verification in metadata['verified']:
            if isinstance(verification, dict):
                verifier = verification.get('by', '')
                if verifier.startswith('human:'):
                    return 'human-reviewed'
        
        # If there are non-human verifiers
        if metadata['verified']:
            return 'machine-confirmed'
        
        return 'unverified'
    
    def get_status_badge(self, status, stale_after=None):
        """Generate status badge with staleness indicator."""
        if not status or status == 'stable':
            badge = '✅ Stable'
        elif status == 'draft':
            badge = '📝 Draft'
        elif status == 'deprecated':
            badge = '⚠️ Deprecated'
        else:
            badge = f'❓ {status.title()}'
        
        # Check staleness
        if stale_after:
            try:
                stale_date = datetime.fromisoformat(stale_after) if 'T' in stale_after else datetime.strptime(stale_after, '%Y-%m-%d')
                if datetime.now(timezone.utc) > stale_date.replace(tzinfo=timezone.utc):
                    badge += ' 🕐 Stale'
            except (ValueError, TypeError):
                pass
        
        return badge
    
    def format_trust_indicator(self, trust_tier):
        """Format trust tier as visual indicator."""
        indicators = {
            'human-reviewed': '👤 Reviewed',
            'machine-confirmed': '🤖 Confirmed',
            'unverified': '❓ Unverified'
        }
        return indicators.get(trust_tier, trust_tier)
    
    def get_concept_age(self, generated_at):
        """Calculate concept age from generated.at field."""
        if not generated_at:
            return None
        
        try:
            gen_time = datetime.fromisoformat(generated_at) if 'T' in generated_at else datetime.strptime(generated_at, '%Y-%m-%d %H:%M:%S')
            age_days = (datetime.now(timezone.utc) - gen_time.replace(tzinfo=timezone.utc)).days
            if age_days < 1:
                return "Today"
            elif age_days < 7:
                return f"{age_days} day{'s' if age_days > 1 else ''} ago"
            elif age_days < 30:
                weeks = age_days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif age_days < 365:
                months = age_days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = age_days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
        except (ValueError, TypeError):
            return None
    
    def extract_relationships(self, content):
        """Extract cross-document links from markdown content."""
        relationships = []
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)
        
        for text, path in matches:
            if not path.startswith(('http://', 'https://')):
                # Clean up path
                path = path.split('#')[0].split('?')[0]
                if not path.endswith('.md'):
                    path = path + '.md' if path else ''
                relationships.append({
                    'text': text,
                    'target': path
                })
        
        return relationships
    
    def generate_knowledge_graph(self):
        """Generate comprehensive knowledge graph from all parsed concepts."""
        graph_data = {
            'nodes': [],
            'edges': [],
            'statistics': {
                'total_concepts': 0,
                'total_relationships': 0,
                'by_type': defaultdict(int),
                'by_status': defaultdict(int),
                'by_trust': defaultdict(int)
            }
        }
        
        concept_map = {}
        
        # First pass: collect all concepts
        for root, dirs, files in os.walk(self.bundle_root):
            if any(part.startswith('.') for part in root.split(os.sep)):
                continue
            
            for file in files:
                if file.endswith('.md') and file not in ['index.md', 'log.md']:
                    file_path = os.path.join(root, file)
                    metadata = self.parse_okf_frontmatter(file_path)
                    
                    if metadata:
                        rel_path = os.path.relpath(file_path, self.bundle_root)
                        
                        # Check if concept is deprecated
                        status = metadata.get('status', 'stable')
                        if status == 'deprecated':
                            self.stats['deprecated_concepts'] += 1
                        
                        node = {
                            'id': rel_path,
                            'title': metadata.get('title', file.replace('.md', '').replace('_', ' ').title()),
                            'type': metadata.get('type', 'unknown'),
                            'status': status,
                            'trust_tier': self.get_trust_tier(metadata),
                            'description': metadata.get('description', ''),
                            'tags': metadata.get('tags', []),
                            'generated_at': metadata.get('generated', {}).get('at')
                        }
                        graph_data['nodes'].append(node)
                        concept_map[rel_path] = metadata
                        graph_data['statistics']['total_concepts'] += 1
                        graph_data['statistics']['by_type'][node['type']] += 1
                        graph_data['statistics']['by_status'][status] += 1
                        graph_data['statistics']['by_trust'][node['trust_tier']] += 1
        
        # Second pass: extract relationships by reading file content
        for rel_path, metadata in concept_map.items():
            file_path = os.path.join(self.bundle_root, rel_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Skip frontmatter
                    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                    relationships = self.extract_relationships(content)
                    
                    for rel in relationships:
                        if rel['target'] and rel['target'] in concept_map:
                            graph_data['edges'].append({
                                'source': rel_path,
                                'target': rel['target'],
                                'label': rel['text'][:50]  # Truncate long labels
                            })
                            graph_data['statistics']['total_relationships'] += 1
            except Exception as e:
                pass
        
        return graph_data
    
    def generate_enhanced_indexes(self):
        """Generate enhanced index.md files with OKF v0.2 metadata."""
        print(f"🔍 Scanning knowledge bundle: {self.bundle_root}\n")
        
        # First, walk to find all directories
        directories = []
        for root, dirs, files in os.walk(self.bundle_root):
            if any(part.startswith('.') for part in root.split(os.sep)):
                continue
            directories.append(root)
        
        # Process directories bottom-up (children first)
        for root in sorted(directories, key=lambda x: len(x.split(os.sep)), reverse=True):
            self._process_directory(root)
        
        # Generate global knowledge graph
        print("\n🕸️  Generating knowledge graph...")
        graph_data = self.generate_knowledge_graph()
        graph_path = os.path.join(self.bundle_root, 'knowledge_graph.json')
        
        with open(graph_path, 'w', encoding='utf-8') as f:
            # Convert defaultdict to dict for JSON serialization
            graph_data['statistics']['by_type'] = dict(graph_data['statistics']['by_type'])
            graph_data['statistics']['by_status'] = dict(graph_data['statistics']['by_status'])
            graph_data['statistics']['by_trust'] = dict(graph_data['statistics']['by_trust'])
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Knowledge graph saved to: {graph_path}")
        print(f"  • {graph_data['statistics']['total_concepts']} concepts")
        print(f"  • {graph_data['statistics']['total_relationships']} relationships")
        print(f"  • {len(graph_data['statistics']['by_type'])} concept types")
        
        # Print summary statistics
        print("\n📊 Bundle Statistics:")
        print(f"  • Total directories: {self.stats['total_dirs']}")
        print(f"  • Total concepts: {self.stats['total_concepts']}")
        print(f"  • Deprecated concepts: {self.stats['deprecated_concepts']}")
        print(f"  • Index files generated: {self.stats['total_indexes']}")
        
        if graph_data['statistics']['by_type']:
            print("\n  Concept Types:")
            for type_name, count in sorted(graph_data['statistics']['by_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    • {type_name}: {count}")
        
        if graph_data['statistics']['by_trust']:
            print("\n  Trust Distribution:")
            for tier, count in graph_data['statistics']['by_trust'].items():
                print(f"    • {tier}: {count}")
    
    def _process_directory(self, root):
        """Process a single directory and generate its index.md."""
        markdown_entries = []
        subdirectory_entries = []
        
        # Check if directory contains OKF concepts
        has_concepts = False
        
        # 1. Parse child Markdown files in the current folder
        try:
            files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
        except OSError:
            return
        
        for file in sorted(files):
            if file.endswith('.md') and file not in ['index.md', 'log.md']:
                file_path = os.path.join(root, file)
                metadata = self.parse_okf_frontmatter(file_path)
                
                if metadata:
                    has_concepts = True
                    self.stats['total_concepts'] += 1
                    
                    # Extract v0.2 metadata
                    title = metadata.get('title', file.replace('.md', '').replace('_', ' ').title())
                    description = metadata.get('description', 'No description provided.')
                    doc_type = metadata.get('type', 'unknown')
                    status = metadata.get('status', 'stable')
                    stale_after = metadata.get('stale_after')
                    generated = metadata.get('generated', {})
                    tags = metadata.get('tags', [])
                    sources = metadata.get('sources', [])
                    
                    # Determine trust tier
                    trust_tier = self.get_trust_tier(metadata)
                    
                    # Format status badge
                    status_badge = self.get_status_badge(status, stale_after)
                    
                    # Get concept age
                    age = self.get_concept_age(generated.get('at'))
                    
                    # Extract relationships for knowledge graph
                    if metadata.get('_file_path'):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                                relationships = self.extract_relationships(content)
                                for rel in relationships:
                                    if rel['target']:
                                        self.knowledge_graph[os.path.relpath(file_path, self.bundle_root)].append(rel)
                        except Exception:
                            pass
                    
                    markdown_entries.append({
                        'file': file,
                        'title': title,
                        'description': description,
                        'type': doc_type,
                        'status': status,
                        'stale_after': stale_after,
                        'trust_tier': trust_tier,
                        'tags': tags[:5],  # Show top 5 tags
                        'sources_count': len(sources),
                        'age': age,
                        'status_badge': status_badge
                    })
        
        # 2. Parse child subdirectories in the current folder
        try:
            dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        except OSError:
            return
        
        for d in sorted(dirs):
            if d.startswith('.'):
                continue
            
            child_idx_path = os.path.join(root, d, 'index.md')
            child_metadata = self.parse_okf_frontmatter(child_idx_path) if os.path.exists(child_idx_path) else {}
            
            sub_title = child_metadata.get('title', d.replace('_', ' ').title())
            sub_desc = child_metadata.get('description', f"Directory containing concepts related to {sub_title.lower()}.")
            sub_status = child_metadata.get('status', 'stable')
            sub_trust = self.get_trust_tier(child_metadata)
            
            subdirectory_entries.append({
                'dir': f"{d}/index.md",
                'title': sub_title,
                'description': sub_desc,
                'status': sub_status,
                'trust_tier': sub_trust
            })
        
        # 3. Write out the index.md file if this directory contains any entries
        if markdown_entries or subdirectory_entries:
            self.stats['total_dirs'] += 1
            self.stats['total_indexes'] += 1
            
            current_folder_name = os.path.basename(root) if root != self.bundle_root else "Knowledge Bundle"
            index_path = os.path.join(root, 'index.md')
            
            index_title = f"{current_folder_name.replace('_', ' ').title()} Index"
            index_desc = f"Navigation index for {current_folder_name.replace('_', ' ')} concepts."
            
            # Build OKF v0.2 compliant frontmatter
            yaml_frontmatter = {
                'type': 'index',
                'title': index_title,
                'description': index_desc,
                'generated': {
                    'by': 'okf_index_generator/1.0',
                    'at': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Add OKF version to root index
            if root == self.bundle_root:
                yaml_frontmatter['okf_version'] = '0.2'
                yaml_frontmatter['statistics'] = {
                    'total_concepts': self.stats['total_concepts'],
                    'total_directories': len([d for d in os.walk(self.bundle_root)]),
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
            
            md_body = []
            
            # Subdirectories section with trust indicators
            if subdirectory_entries:
                md_body.append("## 📁 Subdirectories\n")
                for entry in subdirectory_entries:
                    trust_icon = self.format_trust_indicator(entry['trust_tier'])
                    status_marker = '📝' if entry['status'] == 'draft' else '⚠️' if entry['status'] == 'deprecated' else '✅'
                    md_body.append(
                        f"* **[{entry['title']}]({entry['dir']})** {status_marker} "
                        f"[{trust_icon}] - {entry['description']}"
                    )
                md_body.append("")
            
            # Concepts section with rich metadata
            if markdown_entries:
                md_body.append("## 📄 Concepts\n")
                
                # Group concepts by type for better organization
                concepts_by_type = defaultdict(list)
                for entry in markdown_entries:
                    concepts_by_type[entry['type']].append(entry)
                
                # Display concepts with full metadata
                for concept_type, concepts in sorted(concepts_by_type.items()):
                    # Add type header if multiple types
                    if len(concepts_by_type) > 1:
                        md_body.append(f"### {concept_type}\n")
                    
                    for entry in concepts:
                        # Build rich entry line
                        parts = []
                        
                        # Title with link
                        parts.append(f"**[{entry['title']}]({entry['file']})**")
                        
                        # Status badge
                        parts.append(entry['status_badge'])
                        
                        # Trust indicator
                        trust_icon = self.format_trust_indicator(entry['trust_tier'])
                        parts.append(f"[{trust_icon}]")
                        
                        # Age if available
                        if entry['age']:
                            parts.append(f"(updated {entry['age']})")
                        
                        # Tags if available
                        if entry['tags']:
                            tags_str = ' '.join([f'`{tag}`' for tag in entry['tags']])
                            parts.append(f"🏷️ {tags_str}")
                        
                        # Sources count
                        if entry['sources_count'] > 0:
                            parts.append(f"📚 {entry['sources_count']} source(s)")
                        
                        # Description
                        desc = entry['description']
                        if len(desc) > 100:
                            desc = desc[:100] + "..."
                        parts.append(f"- {desc}")
                        
                        md_body.append("  * " + " ".join(parts))
                    md_body.append("")
            
            # Add a summary section for the directory
            if markdown_entries:
                md_body.append("---\n")
                md_body.append(f"*📊 {len(markdown_entries)} concepts in this directory*")
                
                # Count by status
                status_counts = defaultdict(int)
                for entry in markdown_entries:
                    status_counts[entry['status']] += 1
                
                if status_counts:
                    summary_parts = []
                    for status, count in status_counts.items():
                        if status == 'stable':
                            summary_parts.append(f"✅ {count} stable")
                        elif status == 'draft':
                            summary_parts.append(f"📝 {count} draft")
                        elif status == 'deprecated':
                            summary_parts.append(f"⚠️ {count} deprecated")
                    md_body.append(f"*{', '.join(summary_parts)}*")
            
            # Write the index file
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(yaml_frontmatter, f, default_flow_style=False, sort_keys=False)
                f.write("---\n\n")
                f.write(f"# {index_title}\n\n")
                f.write(f"*{index_desc}*\n\n")
                f.write("\n".join(md_body))
            
            rel_path = os.path.relpath(index_path, self.bundle_root)
            if rel_path == '.':
                rel_path = 'index.md (root)'
            print(f"  ✓ Generated: {rel_path}")

def main():
    """Main entry point with command-line arguments."""
    import sys
    import json  # <-- Added this import here too (though it's already at top)
    
    # Parse arguments
    target_dir = "./knowledge"
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        target_dir = sys.argv[1]
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("OKF v0.2 Index Generator")
        print("=" * 40)
        print("Usage: python index_generator.py [bundle_path] [options]")
        print("Options:")
        print("  --help, -h     Show this help message")
        print("  --graph        Only generate knowledge graph (skip index generation)")
        print("  --stats        Show statistics without generating files")
        print(f"\nDefault bundle path: {target_dir}")
        sys.exit(0)
    
    # Check if directory exists
    if not os.path.exists(target_dir):
        print(f"❌ Error: Path '{target_dir}' could not be located.")
        sys.exit(1)
    
    # Initialize generator
    generator = OKFIndexGenerator(target_dir)
    
    # Handle special modes
    if "--stats" in sys.argv:
        print(f"📊 Statistics for: {target_dir}\n")
        # Quick stats without full generation
        concept_count = 0
        for root, dirs, files in os.walk(target_dir):
            if any(part.startswith('.') for part in root.split(os.sep)):
                continue
            for file in files:
                if file.endswith('.md') and file not in ['index.md', 'log.md']:
                    concept_count += 1
        print(f"Total concepts: {concept_count}")
        
        # Count by type
        types = defaultdict(int)
        for root, dirs, files in os.walk(target_dir):
            if any(part.startswith('.') for part in root.split(os.sep)):
                continue
            for file in files:
                if file.endswith('.md') and file not in ['index.md', 'log.md']:
                    metadata = generator.parse_okf_frontmatter(os.path.join(root, file))
                    if metadata:
                        types[metadata.get('type', 'unknown')] += 1
        
        print("\nConcept types:")
        for type_name, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {type_name}: {count}")
        sys.exit(0)
    
    # Run the generator
    print(f"🚀 Starting OKF v0.2 index generation for: {target_dir}\n")
    
    if "--graph" in sys.argv:
        print("🕸️  Generating knowledge graph only...")
        graph_data = generator.generate_knowledge_graph()
        graph_path = os.path.join(target_dir, 'knowledge_graph.json')
        with open(graph_path, 'w', encoding='utf-8') as f:
            # Convert defaultdict to dict for JSON
            graph_data['statistics']['by_type'] = dict(graph_data['statistics']['by_type'])
            graph_data['statistics']['by_status'] = dict(graph_data['statistics']['by_status'])
            graph_data['statistics']['by_trust'] = dict(graph_data['statistics']['by_trust'])
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Graph saved to: {graph_path}")
        print(f"  • {graph_data['statistics']['total_concepts']} concepts")
        print(f"  • {graph_data['statistics']['total_relationships']} relationships")
    else:
        # Full generation
        generator.generate_enhanced_indexes()
        print("\n✅ OKF v0.2 structure successfully indexed!")

if __name__ == "__main__":
    main()