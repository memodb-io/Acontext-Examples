"""
Main entry point demonstrating Acontext.

This script shows how to:
1. create and get artifacts
"""

import os
from dotenv import load_dotenv
from acontext import AcontextClient
from pathlib import Path


def main():
    # Load environment variables
    load_dotenv()

    # Initialize clients
    acontext_api_key = os.getenv("ACONTEXT_API_KEY")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")

    if not acontext_api_key:
        raise ValueError("ACONTEXT_API_KEY environment variable is required")
    
    with AcontextClient(api_key=acontext_api_key, base_url=acontext_base_url) as acontext_client:
        
        # Create a sample markdown file
        markdown_path = Path(__file__).parent / "retro.md"
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        print(f"Using markdown file: {markdown_path}")

        # Use existing PNG file
        png_path = Path(__file__).parent / "rounded_white.png"
        if not png_path.exists():
            raise FileNotFoundError(f"PNG file not found: {png_path}")
        print(f"Using PNG file: {png_path}")
        
        # Create markdown artifact
        disk = acontext_client.disks.create()
        print("\nCreating markdown artifact...")
        with open(markdown_path, "rb") as f:
            markdown_artifact = acontext_client.artifacts.upsert(
                disk_id=disk.id,
                file=(markdown_path.name, f, "text/markdown"),
                file_path="/notes/",
                meta={"source": "example markdown"},
            )
        print(f"✓ Created markdown artifact: {markdown_artifact.filename}")
        
        # Create PNG artifact
        print("\nCreating PNG artifact...")
        with open(png_path, "rb") as f:
            png_artifact = acontext_client.artifacts.upsert(
                disk_id=disk.id,
                file=(png_path.name, f, "image/png"),
                file_path="/images/",
                meta={"source": "example png"},
            )
        print(f"✓ Created PNG artifact: {png_artifact.filename}")
        
        # Get artifacts
        print("\nRetrieving artifacts...")
        markdown_artifact_retrieved = acontext_client.artifacts.get(
            disk_id=disk.id,
            file_path="/notes/",
            filename="retro.md",
        )
        print(f"✓ Retrieved markdown artifact: {markdown_artifact_retrieved.artifact.filename}")
        
        png_artifact_retrieved = acontext_client.artifacts.get(
            disk_id=disk.id,
            file_path="/images/",
            filename="rounded_white.png",
        )
        print(f"✓ Retrieved PNG artifact: {png_artifact_retrieved.artifact.filename}")
        

if __name__ == "__main__":
    main()
