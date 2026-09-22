#!/usr/bin/env python3
"""Extract requested times into a labeled sheet; optionally compare two videos.
Dependencies: Pillow, FFmpeg (PATH/--ffmpeg, or optional imageio-ffmpeg).
Sample labels indicate requested times, not measured source PTS.
"""
import argparse
import io
import math
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', required=True, type=Path)
    parser.add_argument('--compare', type=Path)
    parser.add_argument('--times', required=True, help='Comma-separated seconds, e.g. 1.8,4.7,4.85')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--ffmpeg', help='FFmpeg executable path')
    parser.add_argument('--width', type=int, default=640, help='Width per source column')
    args = parser.parse_args()
    try:
        times = [float(t.strip()) for t in args.times.split(',')]
    except ValueError:
        parser.error('--times must contain comma-separated numbers')
    if not times or any(not math.isfinite(t) or t < 0 for t in times):
        parser.error('Times must be finite and nonnegative')
    if not 160 <= args.width <= 1920:
        parser.error('--width must be between 160 and 1920')
    if len(times) > 48:
        parser.error('Use at most 48 times per sheet; split longer analyses')
    sources = [args.video] + ([args.compare] if args.compare else [])
    if any(not p.is_file() for p in sources):
        parser.error('Every video source must be an existing file')
    if args.out.resolve() in [p.resolve() for p in sources]:
        parser.error('Output must not overwrite a source video')
    if args.out.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
        parser.error('--out must end in .jpg, .jpeg, or .png')
    ffmpeg = args.ffmpeg or shutil.which('ffmpeg')
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            parser.error('Install FFmpeg or supply --ffmpeg; imageio-ffmpeg is an optional fallback')
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        parser.error('Pillow is required in this Python environment')
    width = args.width
    height = round(width * 9 / 16)
    label_height = 26
    cols = len(sources) if args.compare else 3
    rows = len(times) if args.compare else math.ceil(len(times) / cols)
    sheet = Image.new('RGB', (cols * width, rows * (height + label_height)), '#17191c')
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        for j, source in enumerate(sources):
            cmd = [str(ffmpeg), '-v', 'error', '-ss', str(t), '-i', str(source.resolve()),
                   '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']
            try:
                result = subprocess.run(cmd, capture_output=True, check=True, timeout=120)
                frame = Image.open(io.BytesIO(result.stdout)).convert('RGB')
            except (subprocess.SubprocessError, OSError) as exc:
                parser.error(f'Cannot extract {source.name} at {t:.4f}s: {exc}')
            frame = ImageOps.contain(frame, (width, height))
            col = j if args.compare else i % cols
            row = i if args.compare else i // cols
            x, y = col * width, row * (height + label_height)
            sheet.paste(frame, (x + (width-frame.width)//2, y+label_height+(height-frame.height)//2))
            label = ('REFERENCE' if j == 0 else 'REMAKE') if args.compare else 'SOURCE'
            draw.text((x+8, y+7), f'{label}  requested {t:.4f}s', fill='white')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out, **({'quality': 94} if args.out.suffix.lower() != '.png' else {}))
    print(f'{args.out.resolve()} | {len(times)} requested times | {len(sources)} source(s)')


if __name__ == '__main__':
    main()
