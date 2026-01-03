import os
import shutil
import argparse
import glob

def remove_item(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                print(f"Directory removed: {path}")
            except Exception as e:
                print(f"Error removing {path}: {e}")
        else:
            try:
                os.remove(path)
                print(f"File removed: {path}")
            except Exception as e:
                print(f"Error removing {path}: {e}")
    else:
        pass # Silent if not found

def cleanup_temp():
    print("--- Cleaning Temporary Files (Build Artifacts) ---")
    
    # 1. Manim / Build Directories
    dirs_to_clean = [
        "media",        # Manim default output
        "out_temp",     # Our custom temp output
        "videos",       # Potential Manim output
        "build",        # Python build
        "dist"          # Python dist
    ]
    
    for d in dirs_to_clean:
        remove_item(d)

    # 2. Intermediate Files
    files_to_clean = [
        "current_input.json",
        "manual_output.mp4"
    ]
    for f in files_to_clean:
        remove_item(f)
        
    # 3. Python Cache (__pycache__) - BFS/Walk
    print("Scanning for __pycache__...")
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            path = os.path.join(root, "__pycache__")
            remove_item(path)

def cleanup_cache():
    print("\n--- Cleaning Data Cache ---")
    remove_item("cache")

def cleanup_output():
    print("\n--- Cleaning Final Output ---")
    remove_item("out")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup generated files")
    parser.add_argument("--cache", action="store_true", help="Remove cached data (./cache)")
    parser.add_argument("--output", action="store_true", help="Remove generated videos (./out)")
    parser.add_argument("--all", action="store_true", help="Remove everything including cache and output")
    
    args = parser.parse_args()
    
    # Default behavior: Clean temp only
    cleanup_temp()
    
    if args.cache or args.all:
        cleanup_cache()
        
    if args.output or args.all:
        cleanup_output()
        
    print("\nCleanup complete.")
