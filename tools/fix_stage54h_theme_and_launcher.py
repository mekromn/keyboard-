#!/usr/bin/env python3
"""Stage 54h resource/theme repair helper.

Run against a decoded Stage 54g tree. Supply the original Meboard launcher PNG.
This intentionally does not contain signing material.
"""
from pathlib import Path
from PIL import Image
import argparse,re

def vi(v:int)->bytes:
    out=bytearray()
    while True:
        b=v&0x7f; v>>=7
        if v: out.append(b|0x80)
        else: out.append(b); return bytes(out)
def fld_var(no,v): return vi((no<<3)|0)+vi(v)
def fld_len(no,b): return vi((no<<3)|2)+vi(len(b))+b

def build_metadata():
    data=b''
    for name in [
        'style_sheet_color_common.binarypb',
        'style_sheet_non_dynamic_color.binarypb',
        'style_sheet_color_rules.binarypb',
        'style_sheet_google_blue_rules.binarypb',
        'style_sheet_meboard.binarypb']:
        data += fld_len(2,name.encode())
    border=fld_var(1,1)
    for name in ['style_sheet_color_rules_border.binarypb','style_sheet_meboard_border.binarypb']:
        border += fld_len(2,name.encode())
    return data+fld_len(3,border)

def style_entry(name,argb):
    value=fld_var(1,argb & 0xffffffff)
    entry=fld_len(1,name.encode())+fld_len(2,value)
    return fld_len(2,entry)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('decoded_tree',type=Path)
    ap.add_argument('launcher_png',type=Path)
    a=ap.parse_args(); work=a.decoded_tree
    src=Image.open(a.launcher_png).convert('RGBA')
    for den,n in {'mdpi':108,'hdpi':162,'xhdpi':216,'xxhdpi':324,'xxxhdpi':432}.items():
        d=work/f'res/mipmap-{den}'
        for stem in ('APKTOOL_RENAMED_0x7f110001','APKTOOL_RENAMED_0x7f110002'):
            for ext in ('webp','png'):
                p=d/f'{stem}.{ext}'
                if p.exists(): p.unlink()
        scale=min(n/src.width,n/src.height)
        w,h=max(1,round(src.width*scale)),max(1,round(src.height*scale))
        resized=src.resize((w,h),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',(n,n),(0,0,0,255)); bg.alpha_composite(resized,((n-w)//2,(n-h)//2))
        bg.convert('RGB').save(d/'APKTOOL_RENAMED_0x7f110001.png',optimize=True)
        Image.new('RGBA',(n,n),(0,0,0,0)).save(d/'APKTOOL_RENAMED_0x7f110002.png',optimize=True)
    yml=work/'apktool.yml'; s=yml.read_text()
    s=re.sub(r'(versionCode:\s*)175940518',r'\g<1>175940519',s,count=1)
    s=s.replace('versionName: 18.0.3.954559732-release-arm64-v8a','versionName: 18.0.3.954559732-meboard54h')
    yml.write_text(s)
    theme=work/'assets/theme'
    (theme/'theme_package_metadata_meboard.binarypb').write_bytes(build_metadata())
    vals=[
        ('default_keyboard_background_secondary_color',0xFF353A42),
        ('default_keyboard_background_primary_color',0xFF000000),
        ('default_bordered_key_color',0xFF4B4C4F),
        ('default_bordered_key_color_hovered',0xFF626366),
        ('default_bordered_key_color_pressed',0xFF626366),
        ('default_bordered_key_dark_color',0xFF404245),
        ('default_bordered_key_dark_color_pressed',0xFF626366)]
    (theme/'style_sheet_meboard_border.binarypb').write_bytes(b''.join(style_entry(k,v) for k,v in vals))
if __name__=='__main__': main()
