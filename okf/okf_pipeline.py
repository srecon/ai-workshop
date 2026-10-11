#!/usr/bin/env python3
"""
OKF v0.2 Pipeline - Unified execution script for knowledge bundle generation.

This pipeline orchestrates the complete OKF v0.2 generation process:
1. okf_generator_v2.py - Converts source documents to OKF concepts
2. index_generator_v2.py - Generates indexes and knowledge graph

Usage:
    python okf_pipeline.py [options]

Options:
    --force, -f        Force reprocess all files (passed to both generators)
    --skip-generator   Skip concept generation, only build indexes
    --skip-index       Skip index generation, only convert concepts
    --graph-only       Only generate knowledge graph (skip indexes)
    --stats            Show statistics without generating files
    --help, -h         Show this help message
    --clean            Reset tracking state before processing

Environment:
    RAW_DIR            Source documents directory (default: ./raw_docs)
    BUNDLE_DIR         Output knowledge bundle directory (default: ./knowledge)
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import datetime

class OKFPipeline:
    """
    Orchestrates the OKF v0.2 generation pipeline.
    
    Implements the Pipeline pattern for sequential execution of
    generation and indexing stages with proper error handling.
    """
    
    def __init__(self, raw_dir="./raw_docs", bundle_dir="./knowledge", force=False):
        """
        Initialize the pipeline with configuration.
        
        Args:
            raw_dir: Source documents directory
            bundle_dir: Output knowledge bundle directory
            force: Force reprocess all files
        """
        self.raw_dir = os.path.abspath(raw_dir)
        self.bundle_dir = os.path.abspath(bundle_dir)
        self.force = force
        self.start_time = None
        self.end_time = None
        
        # Script paths
        self.generator_script = Path(__file__).parent / "okf_generator_v2.py"
        self.index_script = Path(__file__).parent / "index_generator_v2.py"
        
        # Track execution status
        self.results = {
            'generator': {'status': 'pending', 'time': None, 'error': None},
            'index': {'status': 'pending', 'time': None, 'error': None}
        }
        
    def _check_scripts(self):
        """Validate that required scripts exist and are executable."""
        missing_scripts = []
        
        if not self.generator_script.exists():
            missing_scripts.append(str(self.generator_script))
        if not self.index_script.exists():
            missing_scripts.append(str(self.index_script))
            
        if missing_scripts:
            print(f"❌ Error: Required scripts not found:\n  {chr(10).join(missing_scripts)}")
            print("\nMake sure the following files exist in the same directory:")
            print("  - okf_generator_v2.py")
            print("  - index_generator_v2.py")
            return False
            
        return True
    
    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.bundle_dir, exist_ok=True)
        
        # Create subdirectories for better organization
        subdirs = ['concepts', 'indexes', 'logs']
        for subdir in subdirs:
            os.makedirs(os.path.join(self.bundle_dir, subdir), exist_ok=True)
    
    def _clean_tracking(self):
        """Clean tracking state file."""
        tracking_file = os.path.join(self.bundle_dir, "file_tracking.yaml")
        if os.path.exists(tracking_file):
            os.remove(tracking_file)
            print("🧹 Cleaned tracking state")
    
    def _run_script(self, script_path, args, description):
        """
        Execute a Python script with arguments.
        
        Args:
            script_path: Path to script
            args: List of arguments
            description: Human-readable description
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"▶️  {description}")
        print(f"{'='*60}")
        
        cmd = [sys.executable, str(script_path)] + args
        print(f"$ {' '.join(cmd)}\n")
        
        try:
            # Run with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Print output in real-time
            for line in process.stdout:
                print(line, end='')
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                print(f"\n✅ {description} completed successfully")
                return True
            else:
                print(f"\n❌ {description} failed with code {return_code}")
                return False
                
        except FileNotFoundError:
            print(f"❌ Script not found: {script_path}")
            return False
        except Exception as e:
            print(f"❌ Error executing {description}: {e}")
            return False
    
    def run_generator(self):
        """
        Run the OKF concept generator.
        
        Returns:
            bool: True if successful
        """
        args = []
        if self.force:
            args.append("--force")
            
        # Add bundle directory argument if specified
        if self.bundle_dir != "./knowledge":
            args.append("--bundle-dir")
            args.append(self.bundle_dir)
            
        success = self._run_script(
            self.generator_script,
            args,
            "OKF Concept Generator"
        )
        
        self.results['generator'] = {
            'status': 'success' if success else 'failed',
            'time': datetime.now().isoformat()
        }
        
        return success
    
    def run_index_generator(self, graph_only=False, stats_only=False):
        """
        Run the OKF index generator.
        
        Args:
            graph_only: Only generate knowledge graph
            stats_only: Only show statistics
            
        Returns:
            bool: True if successful
        """
        args = []
        if graph_only:
            args.append("--graph")
        elif stats_only:
            args.append("--stats")
            
        # Add bundle directory argument if specified
        if self.bundle_dir != "./knowledge":
            args.append("--bundle-dir")
            args.append(self.bundle_dir)
            
        success = self._run_script(
            self.index_script,
            args,
            "OKF Index Generator"
        )
        
        self.results['index'] = {
            'status': 'success' if success else 'failed',
            'time': datetime.now().isoformat()
        }
        
        return success
    
    def _print_summary(self):
        """Print execution summary."""
        print("\n" + "="*60)
        print("📊 PIPELINE EXECUTION SUMMARY")
        print("="*60)
        
        for stage, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"\n{status_icon} {stage.title()}:")
            print(f"   Status: {result['status']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
                
        print("\n" + "="*60)
        print(f"📁 Output directory: {self.bundle_dir}")
        
        # Check for generated files
        knowledge_graph = os.path.join(self.bundle_dir, "knowledge_graph.json")
        if os.path.exists(knowledge_graph):
            print(f"✓ Knowledge graph: {knowledge_graph}")
        
        index_file = os.path.join(self.bundle_dir, "index.md")
        if os.path.exists(index_file):
            print(f"✓ Root index: {index_file}")
            
        print(f"✓ Log directory: {os.path.join(self.bundle_dir, 'logs')}")
        print("="*60)
    
    def run(self, skip_generator=False, skip_index=False, 
            graph_only=False, stats_only=False, clean=False):
        """
        Execute the complete pipeline.
        
        Args:
            skip_generator: Skip concept generation
            skip_index: Skip index generation
            graph_only: Only generate knowledge graph
            stats_only: Only show statistics
            clean: Reset tracking state before processing
            
        Returns:
            bool: True if all stages successful
        """
        self.start_time = datetime.now()
        
        print("🚀 OKF v0.2 Pipeline")
        print("="*60)
        print(f"  Raw directory:   {self.raw_dir}")
        print(f"  Bundle directory: {self.bundle_dir}")
        print(f"  Force reprocess:  {self.force}")
        print(f"  Start time:      {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Validate
        if not self._check_scripts():
            return False
            
        # Prepare
        self._ensure_directories()
        
        if clean:
            self._clean_tracking()
        
        # Execute stages
        success = True
        
        # Stage 1: Concept Generation
        if not skip_generator and not stats_only:
            success = self.run_generator()
            if not success:
                print("\n⚠️  Generator stage failed, but continuing with index generation...")
        
        # Stage 2: Index Generation
        if not skip_index and not graph_only:
            index_success = self.run_index_generator(graph_only, stats_only)
            success = success and index_success
        
        # Stage 3: Special modes
        if graph_only and not skip_index:
            success = self.run_index_generator(graph_only=True)
        
        if stats_only:
            success = self.run_index_generator(stats_only=True)
        
        # Summary
        self.end_time = datetime.now()
        elapsed = (self.end_time - self.start_time).total_seconds()
        
        self._print_summary()
        print(f"\n⏱️  Total execution time: {elapsed:.2f} seconds")
        
        return success

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="OKF v0.2 Pipeline - Automated knowledge bundle generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with force reprocess
  python okf_pipeline.py --force
  
  # Only generate indexes from existing concepts
  python okf_pipeline.py --skip-generator
  
  # Only generate concepts (skip indexing)
  python okf_pipeline.py --skip-index
  
  # Generate only knowledge graph
  python okf_pipeline.py --graph-only
  
  # Show statistics without generating files
  python okf_pipeline.py --stats
  
  # Clean tracking state and rebuild everything
  python okf_pipeline.py --clean --force
  
  # Use custom directories
  python okf_pipeline.py --raw-dir ./my_docs --bundle-dir ./my_knowledge
        """
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reprocess all files'
    )
    
    parser.add_argument(
        '--skip-generator',
        action='store_true',
        help='Skip concept generation, only build indexes'
    )
    
    parser.add_argument(
        '--skip-index',
        action='store_true',
        help='Skip index generation, only convert concepts'
    )
    
    parser.add_argument(
        '--graph-only',
        action='store_true',
        help='Only generate knowledge graph (skip indexes)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics without generating files'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Reset tracking state before processing'
    )
    
    parser.add_argument(
        '--raw-dir',
        default='./raw_docs',
        help='Source documents directory (default: ./raw_docs)'
    )
    
    parser.add_argument(
        '--bundle-dir',
        default='./knowledge',
        help='Output knowledge bundle directory (default: ./knowledge)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.graph_only and args.skip_index:
        print("⚠️  Warning: --graph-only implies --skip-index")
        args.skip_index = True
    
    if args.stats and (args.skip_generator or args.skip_index):
        print("⚠️  Warning: --stats overrides other skip options")
        args.skip_generator = True
        args.skip_index = True
    
    # Create and run pipeline
    pipeline = OKFPipeline(
        raw_dir=args.raw_dir,
        bundle_dir=args.bundle_dir,
        force=args.force
    )
    
    success = pipeline.run(
        skip_generator=args.skip_generator,
        skip_index=args.skip_index,
        graph_only=args.graph_only,
        stats_only=args.stats,
        clean=args.clean
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()