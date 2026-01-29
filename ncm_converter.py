#!/usr/bin/env python3
"""
NCM Converter - Decrypt NetEase Cloud Music NCM files

Usage:
    Place this script in the same folder as your NCM files and run it.
    Converted files will be saved in the same folder.

Requirements:
    pip install pycryptodome mutagen requests pillow

Tested on:
    Python 3.13, 3.14
"""

import struct
import base64
import json
import os
import sys
import binascii
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from Crypto.Cipher import AES
    from mutagen.flac import FLAC, Picture
    from mutagen.mp3 import MP3
    from mutagen.id3 import APIC, ID3
    import requests
    from PIL import Image
except ImportError:
    print("Error: Missing required libraries.")
    print("Install with: pip install pycryptodome mutagen requests pillow")
    input("Press Enter to exit...")
    sys.exit(1)


def get_worker_count():
    cpu_count = os.cpu_count() or 4
    if cpu_count >= 4:
        return cpu_count - 2
    return max(1, cpu_count - 1)


def verify_output(file_path, audio_format):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
        if audio_format == 'flac':
            return header == b'fLaC'
        elif audio_format == 'mp3':
            return header[:3] == b'ID3' or header[:2] == b'\xff\xfb' or header[:2] == b'\xff\xfa'
        return False
    except:
        return False


def decrypt_ncm(file_path):
    file_path = Path(file_path)
    
    try:
        core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
        meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")
        unpad = lambda s: s[0:-(s[-1] if type(s[-1]) == int else ord(s[-1]))]
        
        with open(file_path, 'rb') as f:
            header = f.read(8)
            if binascii.b2a_hex(header) != b'4354454e4644414d':
                return {'success': False, 'file': file_path.name, 'error': 'Invalid NCM header'}
            f.seek(2, 1)
            
            key_len = struct.unpack('<I', f.read(4))[0]
            key_data = bytearray(f.read(key_len))
            for i in range(len(key_data)):
                key_data[i] ^= 0x64
            
            cryptor = AES.new(core_key, AES.MODE_ECB)
            key_data = unpad(cryptor.decrypt(bytes(key_data)))[17:]
            
            box = list(range(256))
            j = 0
            for i in range(256):
                j = (j + box[i] + key_data[i % len(key_data)]) & 0xff
                box[i], box[j] = box[j], box[i]
            
            key_stream = [0] * 256
            for i in range(256):
                key1 = (i + 1) & 0xff
                key2 = (key1 + box[key1]) & 0xff
                idx = (box[key1] + box[key2]) & 0xff
                key_stream[i] = box[idx]
            
            meta_len = struct.unpack('<I', f.read(4))[0]
            if meta_len > 0:
                meta_data = bytearray(f.read(meta_len))
                for i in range(len(meta_data)):
                    meta_data[i] ^= 0x63
                meta_data = base64.b64decode(bytes(meta_data)[22:])
                cryptor = AES.new(meta_key, AES.MODE_ECB)
                meta_data = unpad(cryptor.decrypt(meta_data)).decode('utf-8')[6:]
                meta_data = json.loads(meta_data)
            else:
                meta_data = {'format': 'mp3', 'musicName': file_path.stem, 'artist': [], 'album': 'Unknown', 'musicId': 0}
            
            f.seek(5, 1)
            
            image_space = struct.unpack('<I', f.read(4))[0]
            img_len = struct.unpack('<I', f.read(4))[0]
            image_data = f.read(img_len) if img_len > 0 else None
            if image_space > img_len:
                f.seek(image_space - img_len, 1)
            
            audio_format = meta_data.get('format', 'mp3')
            output_path = file_path.with_suffix(f'.{audio_format}')
            
            with open(output_path, 'wb') as out:
                stream_index = 0
                while True:
                    chunk = bytearray(f.read(0x8000))
                    if not chunk:
                        break
                    for i in range(len(chunk)):
                        chunk[i] ^= key_stream[stream_index]
                        stream_index = (stream_index + 1) & 0xff
                    out.write(chunk)
        
        if not verify_output(output_path, audio_format):
            output_path.unlink(missing_ok=True)
            return {'success': False, 'file': file_path.name, 'error': 'Output verification failed'}
        
        cover_info = "None"
        try:
            music_id = meta_data.get('musicId')
            cover_data = None
            
            if music_id:
                api_url = f"https://music.163.com/api/song/detail/?ids=[{music_id}]"
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('songs'):
                        cover_url = data['songs'][0]['album']['picUrl']
                        try:
                            cover_data = requests.get(cover_url, timeout=5).content
                        except:
                            cover_data = requests.get(f"{cover_url}?param=3000y3000", timeout=5).content
            
            if not cover_data and image_data:
                cover_data = image_data
                cover_info = "Embedded"
            
            if cover_data:
                img = Image.open(BytesIO(cover_data))
                mime = f"image/{img.format.lower()}" if img.format else "image/jpeg"
                
                if audio_format == 'flac':
                    audio = FLAC(str(output_path))
                    audio.clear_pictures()
                    pic = Picture()
                    pic.type = 3
                    pic.mime = mime
                    pic.data = cover_data
                    audio.add_picture(pic)
                    audio.save()
                elif audio_format == 'mp3':
                    audio = MP3(str(output_path), ID3=ID3)
                    if audio.tags is None:
                        audio.add_tags()
                    audio.tags.add(APIC(encoding=3, mime=mime, type=3, data=cover_data))
                    audio.save()
                
                if cover_info != "Embedded":
                    cover_info = f"{img.size[0]}x{img.size[1]}"
                else:
                    cover_info = f"Embedded {img.size[0]}x{img.size[1]}"
        except:
            cover_info = "Failed"
        
        artist_data = meta_data.get('artist', [])
        if artist_data and isinstance(artist_data[0], list):
            artist = artist_data[0][0] if artist_data[0] else 'Unknown'
        elif artist_data and isinstance(artist_data[0], str):
            artist = artist_data[0]
        else:
            artist = 'Unknown'
        
        return {
            'success': True,
            'file': file_path.name,
            'output': output_path.name,
            'title': meta_data.get('musicName', 'Unknown'),
            'artist': artist,
            'album': meta_data.get('album', 'Unknown'),
            'format': audio_format.upper(),
            'cover': cover_info
        }
        
    except Exception as e:
        return {'success': False, 'file': file_path.name, 'error': str(e)}


def main():
    script_dir = Path(__file__).parent.resolve()
    files = list(script_dir.glob('*.ncm')) + list(script_dir.glob('*.NCM'))
    files = list(set(files))
    
    if not files:
        print("No NCM files found.")
        return
    
    worker_count = get_worker_count()
    print(f"Found {len(files)} NCM files. ({worker_count} threads)")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(decrypt_ncm, f): f for f in files}
        
        for future in as_completed(futures):
            result = future.result()
            
            if result['success']:
                success_count += 1
                print(f"{result['title']} - {result['artist']}.{result['format'].lower()} - Success")
                print(f"Cover: {result['cover']}")
            else:
                fail_count += 1
                print(f"{result['file']} - Failed: {result['error']}")
            print("-" * 50)
    
    print(f"Total: {len(files)} | Success: {success_count} | Fail: {fail_count}")


if __name__ == "__main__":
    main()
