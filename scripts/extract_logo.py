import re
import base64
from pathlib import Path

def main():
    html_path = Path(r"C:\Users\julianag18\Downloads\pame.html")
    if not html_path.exists():
        print(f"Error: {html_path} does not exist.")
        return

    html_content = html_path.read_text(encoding="utf-8")
    
    # Search for base64 image in double quotes or single quotes
    match = re.search(r'src=["\']data:image/png;base64,([^"\']+)["\']', html_content)
    if match:
        img_data = base64.b64decode(match.group(1))
        dest_dir = Path(r"c:\Users\julianag18\Desktop\Proyecto de grado\proyecto_grado-main\dashboard\assets")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / "logo.png"
        dest_path.write_bytes(img_data)
        print(f"Logo successfully saved to {dest_path}")
    else:
        print("Error: Could not find base64 logo in HTML file.")

if __name__ == "__main__":
    main()
