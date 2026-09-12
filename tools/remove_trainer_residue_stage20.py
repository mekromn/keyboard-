#!/usr/bin/env python3
"""Delete three unconsumed trainer settings end-to-end from pinned Meboard Stage 19.
No flag is replaced by false/empty text; no no-op implementation is introduced.
All edits are planned and checked before writing. Device runtime remains untested.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

INPUT_SHA = 'c06c75a38f61baf442f0ed040d03dcd41cec1c45a528184ae7ca4d3be77611d4'
# Each tuple is (consumer-facing accessor, flag accessor, supplier, selector, flag).
CHAINS = (
 ('Z()Ljava/lang/String;', 'ad()Ljava/lang/String;', 'lhi', 6, 'TrainerFeature__http_federated_compute_protocol_base_uri'),
 ('X()Ljava/lang/String;', 'Z()Ljava/lang/String;', 'lhi', 11, 'TrainerFeature__droid_guard_reduced_configuration_flow_name'),
 ('aJ()Z', 'ar()Z', 'lhg', 20, 'TrainerFeature__droid_guard_enabled'),
)
METHOD = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
EXPECTED = {'smali/lhk.smali': '3f26c771b433f7bfcecc9702c94a91df77e8232321fa5117b336586ca94f111a', 'smali/lgp.smali': 'b23e6ae1ccbf5d5353f7df4132ffc00c98a0b3aea21e4b537c9e341e68929b2b', 'smali/aamv.smali': '95318584b40b7b6686fdbc4bb8b5fe48560c52ec5316e205d9ddea4279d2aee3', 'smali/aams.smali': 'dba86f7ae591ebb518cb112bad20a90e46b63db2b0450ce6e94f25149880e0f2', 'smali_classes2/lhg.smali': 'ca590e8e3af798685187fa5876ce7beb99a0d9c604ee0980581cf7f3fb9f764d', 'smali_classes2/lhi.smali': '9b858799741f901f5704c8aefd29a6d25a8280537718e6b05de5aa113e5f23eb'}


def require(ok: bool, message: str) -> None:
    if not ok: raise ValueError(message)


def digest(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def methods(text: str) -> dict[str,str]:
    out = {m.splitlines()[0].split()[-1]:m for m in METHOD.findall(text)}
    require(len(out)==len(METHOD.findall(text)), 'duplicate method signature')
    return out


def remove_methods(text: str, signatures: set[str]) -> str:
    found=set()
    def repl(match):
        sig=match[0].splitlines()[0].split()[-1]
        if sig not in signatures:return match[0]
        found.add(sig)
        return ''
    result=METHOD.sub(repl,text)
    require(found==signatures, f'missing method declarations: {signatures-found}')
    return result


def supplier_selectors(text: str, supplier: str) -> list[tuple[str,int]]:
    """All constructor uses must have a literal selector in straight-line accessors."""
    calls=[]
    for sig,body in methods(text).items():
        needle=f'L{supplier};-><init>(I)V'
        if needle not in body:continue
        lines=[line.strip() for line in body.splitlines()
               if line.strip() and not line.lstrip().startswith(('.line ', '#'))]
        for index,line in enumerate(lines):
            hit=re.search(r'invoke-direct \{[vp]\d+, ([vp]\d+)\}, '+re.escape(needle),line)
            if hit:
                require(index>0,'constructor at method start')
                constant=re.fullmatch(r'const(?:/4|/16)? '+re.escape(hit[1])+r', (-?0x[0-9a-f]+|-?\d+)',lines[index-1])
                require(constant is not None,f'nonliteral immediate selector in {sig}')
                calls.append((sig,int(constant[1],0)))
    return calls


def prune_supplier(text: str, supplier: str) -> str:
    old=methods(text)['a()Ljava/lang/Object;']
    table=re.search(r'(?ms)(^\s*:pswitch_data_0\s*\n)\s*\.packed-switch 0x0\n(.*?)^\s*\.end packed-switch',old)
    require(table is not None,'packed table missing')
    labels=re.findall(r':pswitch_[0-9a-f]+',table[2])
    require(len(labels)==20,'unexpected supplier selector count')
    if supplier=='lhi':
        removed={6,11};gone={labels[i] for i in removed}
        replacement=table[1]+'    .sparse-switch\n'+''.join(
            f'        0x{i:x} -> {label}\n' for i,label in enumerate(labels) if i not in removed
        )+'    .end sparse-switch'
        body=old[:table.start()]+replacement+old[table.end():]
        body,n=re.subn(r'(?m)^(\s*)packed-switch p0, :pswitch_data_0$',r'\1sparse-switch p0, :pswitch_data_0',body)
        require(n==1,'supplier switch rewrite count')
        stop=re.search(r'(?m)^\s*:pswitch_data_0\s*$',body).start()
        code_labels=list(re.finditer(r'(?m)^\s*(:pswitch_[0-9a-f]+)\s*$',body[:stop]))
        spans=[(m.start(),code_labels[i+1].start() if i+1<len(code_labels) else stop)
               for i,m in enumerate(code_labels) if m[1] in gone]
        require(len(spans)==2,'expected two supplier bodies')
        for a,b in reversed(spans):body=body[:a]+body[b:]
    else:
        # Default selector 20 has exactly one producer, the removed aJ accessor.
        # Drop its body. The original retained selector-19 body is already next;
        # it becomes the natural default. Its instructions remain byte-for-byte.
        require(labels[-1]==':pswitch_0','expected original last retained case')
        first=re.search(r'(?m)^\s*:pswitch_0\s*$',old)
        switch=re.search(r'(?m)^\s*packed-switch p0, :pswitch_data_0\s*$',old)
        require(first is not None and switch is not None,'missing default boundaries')
        fragment=old[switch.end():first.start()]
        require('Laams;->ar()Z' in fragment,'unexpected default body')
        body=old[:switch.end()]+'\n'+old[first.start():]
        # Remove only the last table entry (19); valid selector 19 now falls through.
        pos=body.index('.packed-switch 0x0')
        tail,n=re.subn(r'(?m)^\s*:pswitch_0\s*\n','',body[pos:],count=1)
        require(n==1,'selector-19 table entry missing')
        body=body[:pos]+tail
    return text.replace(old,body,1)


def apply(root:Path, report:Path, dry_run:bool=False) -> dict:
    texts={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    require(len(texts)==21762,'input class count differs from Stage 19')
    for path,expected in EXPECTED.items():
        require(path in texts and digest(texts[path])==expected,f'input drift: {path}')
    # Confirm both interfaces have only the reviewed implementation.
    for interface,impl in [('lgp','smali/lhk.smali'),('aams','smali/aamv.smali')]:
        implementors={p for p,t in texts.items() if re.search(r'^\.implements L'+interface+r';$',t,re.M)}
        require(implementors=={impl},f'unknown implementation of {interface}: {implementors}')
    for upper,lower,supplier,selector,flag in CHAINS:
        for p,t in texts.items():
            require(not any(f'L{owner};->{upper}' in t for owner in ['lhk','lgp']),f'new upper caller: {p}')
            if f'Laams;->{lower}' in t or f'Laamv;->{lower}' in t:
                require(p==f'smali_classes2/{supplier}.smali',f'new lower caller: {p}')
            if f'L{supplier};-><init>(I)V' in t:
                require(p=='smali/lhk.smali',f'new supplier producer: {p}')
        producers=supplier_selectors(texts['smali/lhk.smali'],supplier)
        require([sig for sig,value in producers if value==selector]==[upper],f'new selector producer: {supplier}/{selector}')
    changed=dict(texts)
    upper_sigs={r[0] for r in CHAINS};lower_sigs={r[1] for r in CHAINS}
    for cls,sigs in [('lhk',upper_sigs),('lgp',upper_sigs),('aamv',lower_sigs),('aams',lower_sigs)]:
        path=f'smali/{cls}.smali';changed[path]=remove_methods(changed[path],sigs)
    for cls in ['lhg','lhi']:
        path=f'smali_classes2/{cls}.smali';changed[path]=prune_supplier(changed[path],cls)
    for upper,lower,supplier,selector,flag in CHAINS:
        for p,t in changed.items():
            require(not any(f'L{owner};->{upper}' in t for owner in ['lhk','lgp']),f'residual upper call: {p}')
            require(not any(f'L{owner};->{lower}' in t for owner in ['aams','aamv']),f'residual lower call: {p}')
            require(flag not in t,f'residual flag: {p}')
            require('federatedcompute-pa.googleapis.com' not in t,f'residual endpoint: {p}')
        require(selector not in [value for _,value in supplier_selectors(changed['smali/lhk.smali'],supplier)],'removed selector still constructed')
    delta=sorted(p for p in texts if texts[p]!=changed[p])
    require(set(delta)==set(EXPECTED),'unexpected file scope')
    result={'input_apk_sha256':INPUT_SHA,'classes_before':len(texts),'classes_after':len(changed),
      'modified_files':delta,'untouched_class_files':len(texts)-len(delta),
      'deleted_methods':{c:sorted(upper_sigs if c in ['lgp','lhk'] else lower_sigs) for c in ['lgp','lhk','aams','aamv']},
      'deleted_method_count':12,'removed_supplier_branches':{'lhi':[6,11],'lhg':[20]},
      'removed_flags':[r[4] for r in CHAINS],'net_smali_bytes_removed':sum(len(texts[p].encode())-len(changed[p].encode()) for p in delta),
      'before_hashes':{p:digest(texts[p]) for p in delta},'after_hashes':{p:digest(changed[p]) for p in delta},
      'dry_run':dry_run,'runtime_tested':False,'privacy_final':False}
    if not dry_run:
        for p in delta:(root/p).write_text(changed[p])
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
