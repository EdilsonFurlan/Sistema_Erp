import os
import sys

# Add project root to path to import encaixe.utils
sys.path.append(os.getcwd())

try:
    from encaixe.utils import read_mld_file
except ImportError:
    # Try appending the current directory if running from outside
    sys.path.append(os.path.join(os.getcwd(), 'encaixe'))
    from encaixe.utils import read_mld_file

def test_read():
    file_path = "teste.mld"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found in {os.getcwd()}")
        return

    print(f"Reading {file_path}...")
    try:
        content = read_mld_file(file_path)
        print("Success!")
        print(f"Version: {content['version']}")
        print(f"Thumbnail Size: {len(content['thumbnail'])} bytes")
        print(f"Data Keys: {list(content['data'].keys())}")
        
        # Optional: Save thumb to verify
        with open("test_thumb.png", "wb") as f:
            f.write(content['thumbnail'])
        print("Saved test_thumb.png")
        
    except Exception as e:
        print(f"Failed to read file: {e}")

if __name__ == "__main__":
    test_read()
