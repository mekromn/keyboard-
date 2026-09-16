#!/usr/bin/env python3
"""Rebuild the Meboard custom theme color sheets with the exact user-supplied palette.

Operates on an already-decoded Stage 54i tree. Contains no signing material.
"""
from pathlib import Path
import argparse,re

def vi(v:int)->bytes:
    out=bytearray()
    while True:
        b=v&0x7f; v>>=7
        if v: out.append(b|0x80)
        else: out.append(b); return bytes(out)
def fld_var(no,v): return vi((no<<3)|0)+vi(v)
def fld_len(no,b): return vi((no<<3)|2)+vi(len(b))+b
def style_entry(name,argb):
    value=fld_var(1,argb & 0xffffffff)
    entry=fld_len(1,name.encode())+fld_len(2,value)
    return fld_len(2,entry)

BASE=[
('default_keyboard_background_primary_color',0xFF000000),
('default_keyboard_background_secondary_color',0xFF0D0D0D),
('default_generic_accent_color',0xFF5E97F6),
('default_generic_accent_color_pressed',0xFF5E97F6),
('default_action_key_background_color',0xFF5E97F6),
('default_action_key_background_color_hovered',0xFF5E97F6),
('default_action_key_background_color_pressed',0xFF5E97F6),
('default_action_key_background_color_contrast',0xFF5E97F6),
('default_action_key_background_color_pressed_contrast',0xFF5E97F6),
('default_label_color',0xFFFFFFFF),
('color_label_secondary',0xFF999999),
('color_label_dynamic',0xFF5E97F6),
('color_state_label_candidate_selected',0xFFFFFFFF),
('color_state_label_candidate',0xFF999999),
('default_bordered_key_color',0xFF4C4C4C),
('default_bordered_key_color_hovered',0xFF3A3A3A),
('default_bordered_key_color_pressed',0xFF3A3A3A),
('default_bordered_key_dark_color',0xFF0D0D0D),
('default_bordered_key_dark_color_pressed',0xFF3A3A3A),
('default_transparent_key_color_pressed',0x333A3A3A),
('default_borderless_space_bar_color',0xFF999999),
('default_borderless_space_bar_color_pressed',0xFFFFFFFF),
('color_keyboard_separator',0xFF3A3A3A),
('color_keyboard_top_separator',0xFF3A3A3A),
('color_generic_extension_background_activated',0xFF3A3A3A),
('color_generic_extension_background',0xFF0D0D0D),
('color_keyboard_editing_overlay',0xFF000000),
('color_keyboard_editing_button',0xFFFFFFFF),
('color_expression_corpus_selector_background_active',0x335E97F6),
('color_jarvis_background_active',0x335E97F6),
]
BORDER=[
('default_keyboard_background_secondary_color',0xFF0D0D0D),
('default_keyboard_background_primary_color',0xFF000000),
('default_bordered_key_color',0xFF4C4C4C),
('default_bordered_key_color_hovered',0xFF3A3A3A),
('default_bordered_key_color_pressed',0xFF3A3A3A),
('default_bordered_key_dark_color',0xFF0D0D0D),
('default_bordered_key_dark_color_pressed',0xFF3A3A3A),
]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded_tree',type=Path); a=ap.parse_args()
    theme=a.decoded_tree/'assets/theme'
    (theme/'style_sheet_meboard.binarypb').write_bytes(b''.join(style_entry(k,v) for k,v in BASE))
    (theme/'style_sheet_meboard_border.binarypb').write_bytes(b''.join(style_entry(k,v) for k,v in BORDER))
    yml=a.decoded_tree/'apktool.yml'; s=yml.read_text()
    s=re.sub(r'(versionCode:\s*)175940520',r'\g<1>175940521',s,count=1)
    s=re.sub(r'versionName:\s*18\.0\.3\.954559732-meboard54i','versionName: 18.0.3.954559732-meboard54j',s,count=1)
    yml.write_text(s)
if __name__=='__main__': main()
