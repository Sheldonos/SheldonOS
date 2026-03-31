#!/usr/bin/env python3
"""
Python wrapper for rendering Remotion videos with common options.
Usage: python render_video.py <composition_id> [options]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def render_video(
    composition_id: str,
    output_path: str = None,
    codec: str = "h264",
    quality: int = None,
    concurrency: int = None,
    image_format: str = "jpeg",
    scale: float = 1.0,
    crf: int = None,
):
    """Render a Remotion video with specified options."""
    
    cmd = ["npx", "remotion", "render", composition_id]
    
    if output_path:
        cmd.append(output_path)
    
    cmd.extend(["--codec", codec])
    
    if quality:
        cmd.extend(["--quality", str(quality)])
    
    if concurrency:
        cmd.extend(["--concurrency", str(concurrency)])
    
    cmd.extend(["--image-format", image_format])
    
    if scale != 1.0:
        cmd.extend(["--scale", str(scale)])
    
    if crf:
        cmd.extend(["--crf", str(crf)])
    
    print(f"🎥 Rendering video: {composition_id}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Video rendered successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error rendering video: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Render Remotion videos with common options"
    )
    parser.add_argument("composition_id", help="ID of the composition to render")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--codec",
        default="h264",
        choices=["h264", "h265", "vp8", "vp9", "prores"],
        help="Video codec (default: h264)",
    )
    parser.add_argument(
        "--quality", type=int, help="Quality setting (0-100, higher is better)"
    )
    parser.add_argument(
        "--concurrency", type=int, help="Number of parallel rendering threads"
    )
    parser.add_argument(
        "--image-format",
        default="jpeg",
        choices=["jpeg", "png"],
        help="Image format for frames (default: jpeg)",
    )
    parser.add_argument(
        "--scale", type=float, default=1.0, help="Scale factor (default: 1.0)"
    )
    parser.add_argument("--crf", type=int, help="CRF value for quality control")
    
    args = parser.parse_args()
    
    render_video(
        composition_id=args.composition_id,
        output_path=args.output,
        codec=args.codec,
        quality=args.quality,
        concurrency=args.concurrency,
        image_format=args.image_format,
        scale=args.scale,
        crf=args.crf,
    )


if __name__ == "__main__":
    main()
