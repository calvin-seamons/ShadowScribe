"""
Setup script for Query Rewriter testing environment.

Checks dependencies and downloads the SmolLM2 model if needed.
"""

import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required packages are installed"""
    required = {
        "transformers": "transformers",
        "torch": "torch",
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {module} is installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {module} is NOT installed")
    
    return missing


def install_packages(packages):
    """Install missing packages using uv"""
    if not packages:
        return True
    
    print(f"\nInstalling missing packages: {packages}")
    
    try:
        cmd = ["uv", "pip", "install"] + packages
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install packages: {e}")
        print(e.stderr)
        return False


def download_model():
    """Pre-download the SmolLM2 model to avoid download during tests"""
    print("\nPre-downloading SmolLM2-1.7B-Instruct model...")
    print("This may take a few minutes on first run.\n")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        model_name = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
        
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✅ Tokenizer downloaded")
        
        print("Downloading model (this is the big one)...")
        # Just download, don't load to GPU
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        )
        print("✅ Model downloaded")
        
        # Clean up to free memory
        del model
        del tokenizer
        
        import gc
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return False


def main():
    print("=" * 60)
    print("Query Rewriter Testing Environment Setup")
    print("=" * 60)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print("\n2. Installing missing packages...")
        if not install_packages(missing):
            print("\n⚠️  Could not install packages automatically.")
            print("Please run manually:")
            print(f"  uv pip install {' '.join(missing)}")
            sys.exit(1)
    else:
        print("\n2. All dependencies installed ✅")
    
    # Download model
    print("\n3. Checking model availability...")
    if download_model():
        print("\n✅ Setup complete!")
        print("\nYou can now run tests with:")
        print("  uv run python query_rewriter_tests/run_tests.py --quick")
        print("\nOr test the rewriter directly:")
        print("  uv run python query_rewriter_tests/query_rewriter.py")
    else:
        print("\n⚠️  Model download failed. Tests may still work but will")
        print("download the model on first run.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
