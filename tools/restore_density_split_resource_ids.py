#!/usr/bin/env python3
"""Restore density-split resource IDs and split-backed XML references.

Gboard's xxhdpi configuration split owns drawable entries with fixed 0x7f08....
IDs.  Decoding the base APK alone turns references to those split-only entries
into @null.  Merely copying the bitmap files into a monolithic APK is not
sufficient: without the split public.xml entries AAPT assigns unrelated IDs,
and keyboard-definition XML later resolves a null popup icon as the literal
resource name "0" and crashes LatinIME.

This exact-build pass:
  * merges every missing density-split public resource ID without replacing the
    base table;
  * verifies every copied split resource exists; and
  * restores all split-backed references that the base-only decode lost.
"""
from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')
DENSITY = Path('/mnt/data/meboard_work/decoded/density')

# Exact 194-entry repair map, compressed only to keep the public replay script
# reviewable. Decoding this constant yields the same explicit
# (file, line, attribute, replacement, target-ID) tuples used during diagnosis.
_REPAIRS_B85 = "c-p<&O>Y}F5C-7?qO(ww!|z)IG^c)~D0&M5V<qjjM&;VD<2L#Cl>w2QLxAvQIs^M?`2mL<&TyA{|9<zhKHr?4mVcMSdA)h_>yN*`d-v1rZ*PBj^YhyuZq28(nQZKK`tH;HdAIlbUH#kLe)s*?K1asv_GF!<*I)Xu2f2W8cH0<dM>#TXa&(b#8Ri1Y1;(Xe&K~DRM{IP-z+BMfGRm=)8T~jnnFy5F=q$_yT}~;O<R^nkjEgV_2h%bxjB{afbdGTe=CnqaRnxq3QI{)9iBMG2ymC>OQwpYwb9v`j-em`K)}kKU#WKMjX?fRFNFe8Z<D4-thn676)@DvHXB|2`wpvQTJ+Cyr!(?llJLe6|!L2PDodcpd*^RlCP2Tv<;?o@G14{)9b3vCwtAdY=BbZAnoZHOQ+_|L}q3AQr1zj%catY;n35vmtb9Qp>9OEp^1zj%cayoP8P1Kyb#syt2>T)`B7nWse?!t1Y9NB(OI4_?cUOs;LL#s(F4W6HlBTnpv?(!4HoNW8fJnF2i86uzasAK;p=ki}}?$?ihKJ;ei?)dQc&`cESGvOouk6-$PO=b%<JeSkjKg;=LY{pCKPG8R>PNe<r@!|31@pgDnTc7qzuLEHY#}dO5gn1lu408~ckm=fpIfOXLLeA2izV8e<(DGYLcN`QqpP^-5*fNKl0L85YmbL|Q0_3obI*et~_1y(!jkK*;(Ma1X=8Q(#R?G>f?e&qjCE;|sK71x4?9@kzR>|>7PS$a(HCm8T<ZMFIHJY_!$siaJj%^IH2$rI7sXg?qeAtQR*qxXW#}VY5m{TAp>Ws%5;qe^XVQ+jHxc1bYOdy28N<@EIa&g9%^+{(qC#B)6R|jh#H`Z_!$blNW{#=i29NG<HKYmLlPi3r?O`b^o5GHwyZBA0?hZ~j^`r(EZg?_kViDdiX<_Oo;>SW<As5-&P9%GvmWsk9K(HYreY;?6sM2%ExTGq&=syVMYHWxL<=J6^OGAp_mgPoQNE4to)-LWQbeLDhUx3ayD;s{n;KQWCD>ckF9M2I8*(1wjEh%dg5Iq2cTi5&n5a>yx0kcvhGTV6@8!3L?suxUXvh+rb)>##wpLA07dbfOI!bCQnZt*}#X8DA>n^ZD+yiq<UhhjtrK?vULXA4H?q9nrT=-3cVwMl&bsIN-4WJk2x5D>+H>ICXK3trZhZpZX1>D4agkDZ=S<oH|wG%ep#A$B9;WSyv}0IaxM++9iP`n?KF*lFxX%gRN^kPn#2E^R!)lF|zr?Z}g}*SvG&#B^y$5f=-^kzVrEO{d{|Ozx*-yVu5v}Aw!mfEze$JK>7OmE*-Skfe71!UQb`3Wto*AE5cS}F(k-Ju*Kfb#If~mXAWT#_2TNdEL<<FPG8p?;l8dq(tTZXl8z(Y*EJ_7InsR{dkHOGFYI(}!s~^du1$Eou+y~(uNQW@HsSTcPS+;9UK}RgW|bpLtB5e*+pL8-9&)fYIWvbK2iqnhbB59>nVGn)?5>JSkdtN0Z0g@9MW3&O7a+Qo6|L9pTpr7__fEsgZcDicVO|lVpox(p=J3@xk!86b0#J;tM&}{SYhYy-gKt4IEQsIlW*Bz+aeh!mF@nJ;Mle|62rl)DCRQVaO(TsMHqB`TF{%bJsRl8BLl8gw2U)h70{"
REPAIRS = [
    tuple(item)
    for item in json.loads(zlib.decompress(base64.b85decode(_REPAIRS_B85)))
]

def parse_public_line(line: str) -> tuple[int, str, str] | None:
    match = re.search(
        r'<public type="([^"]+)" name="([^"]+)" id="0x([0-9a-f]+)"',
        line,
    )
    if not match:
        return None
    return int(match.group(3), 16), match.group(1), match.group(2)


def merge_density_public_ids() -> int:
    base = ROOT / 'res/values/public.xml'
    split = DENSITY / 'res/values/public.xml'
    if not base.is_file() or not split.is_file():
        raise SystemExit(f'missing public table: base={base.is_file()} density={split.is_file()}')

    base_text = base.read_text()
    existing: dict[int, tuple[str, str]] = {}
    for line in base_text.splitlines():
        parsed = parse_public_line(line)
        if parsed:
            rid, rtype, name = parsed
            existing[rid] = (rtype, name)

    additions: list[tuple[int, str]] = []
    for line in split.read_text().splitlines():
        parsed = parse_public_line(line)
        if not parsed:
            continue
        rid, rtype, name = parsed
        name = name.replace('APKTOOL_DUMMY_0x', 'APKTOOL_RENAMED_0x')
        current = existing.get(rid)
        if current is not None:
            if current != (rtype, name):
                raise SystemExit(
                    f'density public ID collision 0x{rid:08x}: base={current}, split={(rtype, name)}'
                )
            continue
        resource_glob = list((ROOT / 'res').glob(f'{rtype}*/{name}.*'))
        if rtype == 'style':
            # The only density style is already present in the base table.
            raise SystemExit(f'unexpected missing density style 0x{rid:08x} {name}')
        if not resource_glob:
            # Value resources (the xxhdpi split contributes one integer) live
            # inside values*.xml rather than in a type-named file directory.
            value_hits = []
            value_pattern = re.compile(
                rf'<{re.escape(rtype)}\b[^>]*\bname="{re.escape(name)}"'
            )
            for values_file in (ROOT / 'res').glob('values*/*.xml'):
                if value_pattern.search(values_file.read_text(errors='ignore')):
                    value_hits.append(values_file)
            if len(value_hits) != 1:
                raise SystemExit(
                    f'density resource source missing/ambiguous for 0x{rid:08x} '
                    f'{rtype}/{name}: files={resource_glob}, values={value_hits}'
                )
        additions.append(
            (rid, f'    <public type="{rtype}" name="{name}" id="0x{rid:08x}" />')
        )
        existing[rid] = (rtype, name)

    if len(additions) != 114:
        raise SystemExit(f'expected 114 missing density public entries, found {len(additions)}')
    additions.sort()
    marker = '</resources>'
    if base_text.count(marker) != 1:
        raise SystemExit('base public.xml has an unexpected resources terminator')
    payload = '\n'.join(line for _, line in additions) + '\n'
    base.write_text(base_text.replace(marker, payload + marker))
    print(f'merged {len(additions)} fixed density public IDs')
    return len(additions)


def restore_references() -> int:
    changed = 0
    by_file: dict[str, list[tuple[int, str, str, int]]] = {}
    for rel, line, attr, replacement, rid in REPAIRS:
        by_file.setdefault(rel, []).append((line, attr, replacement, rid))

    for rel, repairs in sorted(by_file.items()):
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f'missing split-reference source XML: {path}')
        lines = path.read_text().splitlines()
        for line_no, attr, replacement, rid in sorted(repairs):
            if not (1 <= line_no <= len(lines)):
                raise SystemExit(f'{rel}:{line_no}: line outside file')
            line = lines[line_no - 1]
            pattern = re.compile(rf'((?:android:)?{re.escape(attr)}=")@null(")')
            line2, count = pattern.subn(rf'\1{replacement}\2', line, count=1)
            if count != 1:
                raise SystemExit(
                    f'{rel}:{line_no}: expected one {attr}="@null" for 0x{rid:08x}; got {line!r}'
                )
            lines[line_no - 1] = line2
            changed += 1
        path.write_text('\n'.join(lines) + '\n')

    if changed != 194:
        raise SystemExit(f'expected 194 restored references, changed {changed}')
    print(f'restored {changed} split-backed XML references in {len(by_file)} files')
    return changed


def verify_source_state() -> None:
    public = (ROOT / 'res/values/public.xml').read_text()
    for _, _, _, replacement, rid in REPAIRS:
        name = replacement.split('/', 1)[1]
        expected = f'<public type="drawable" name="{name}" id="0x{rid:08x}" />'
        if expected not in public:
            raise SystemExit(f'public ID missing after merge: {expected}')
    for rel, line_no, attr, replacement, _ in REPAIRS:
        line = (ROOT / rel).read_text().splitlines()[line_no - 1]
        if f'{attr}="{replacement}"' not in line and f'android:{attr}="{replacement}"' not in line:
            raise SystemExit(f'{rel}:{line_no}: restored source reference missing')
    print('density split source-state verification passed')


def main() -> None:
    merge_density_public_ids()
    restore_references()
    verify_source_state()


if __name__ == '__main__':
    main()
