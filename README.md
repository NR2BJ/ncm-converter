# NCM Converter

Convert NetEase Cloud Music (.ncm) files to FLAC and MP3 with album art — both as a Python CLI tool and a free online web app.

**[Try it online → ncm.nr2bj.com](https://ncm.nr2bj.com/)**

## Features

- **NCM to FLAC / MP3 conversion** — Decrypt and convert `.ncm` files to standard audio formats
- **High-resolution album art** — Fetches original album cover from NetEase API (网易云音乐)
- **Automatic metadata tagging** — Preserves title, artist, album, and embeds cover art
- **Batch conversion** — Process multiple NCM files at once with multithreading
- **Web version** — Browser-based converter at [ncm.nr2bj.com](https://ncm.nr2bj.com/), no installation needed
- **100% client-side** — Web version processes files locally in your browser, nothing is uploaded
- **Drag & drop** — Simple drag-and-drop interface on the web version

## Web Version

The online converter runs entirely in your browser — no server upload, no installation required.

- Supports `.ncm` file drag & drop or file picker
- Converts to FLAC or MP3
- Embeds high-quality album artwork
- Works on desktop and mobile browsers

**→ [ncm.nr2bj.com](https://ncm.nr2bj.com/)**

## Python CLI

### Requirements

```
pip install pycryptodome mutagen requests pillow
```

### Usage

Place the converter script in a folder with your `.ncm` files and run:

```bash
python ncm_converter.py
```

Converted FLAC/MP3 files with embedded album art will appear in the same directory.

### How It Works

1. Decrypts the NCM container format using AES
2. Extracts the original audio stream (FLAC or MP3)
3. Fetches album cover art from the NetEase Cloud Music API
4. Tags the output file with metadata (title, artist, album, cover)

## What is an NCM File?

NCM (`.ncm`) is a proprietary encrypted audio format used by **NetEase Cloud Music** (网易云音乐 / 넷이즈 클라우드 뮤직). NCM files cannot be played by standard music players. This tool decrypts and converts them to standard FLAC or MP3 format while preserving audio quality and metadata.

## Keywords

`ncm` `ncm converter` `ncm to mp3` `ncm to flac` `netease cloud music` `网易云音乐` `ncm decoder` `ncm decrypt` `ncm file converter` `music converter` `ncm 변환기` `ncm 파일 변환` `넷이즈 클라우드 뮤직` `album art` `batch converter` `python`

## License

MIT
