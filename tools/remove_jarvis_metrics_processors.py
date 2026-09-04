#!/usr/bin/env python3
"""Remove Jarvis prompt Clearcut/session metrics processors without removing Jarvis.

The Jarvis prompt extension, prompter, keyboard, consent flow, and local/remote
rewrite feature code remain. This patch removes the two processor objects, their
helpers, their Dagger/runtime registration, and their Clearcut dependencies.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path('/mnt/data/meboard_work/buildtree')
SMALI_ROOTS = [ROOT / n for n in ('smali', 'smali_classes2', 'smali_classes3', 'smali_classes4')]
DELETE = {'hrd', 'hre', 'hrg', 'hrh'}
EXPECTED_INBOUND = {
    'hrd': {'hpc', 'cql', 'hre'},
    'hre': {'cql'},
    'hrg': {'hpc', 'cql', 'hrh'},
    'hrh': {'cql'},
}


def find_class(name: str) -> Path:
    hits = []
    for root in SMALI_ROOTS:
        hits.extend(root.rglob(name + '.smali'))
    if len(hits) != 1:
        raise SystemExit(f'{name}: expected one class, got {hits}')
    return hits[0]


def declared_name(path: Path) -> str:
    match = re.search(r'^\.class[^\n]* L([^;]+);', path.read_text(errors='ignore'), re.M)
    if not match:
        raise SystemExit(f'{path}: missing class declaration')
    return match.group(1)


def rg_files(needle: str) -> list[Path]:
    run = subprocess.run(
        ['rg', '-l', '-F', needle, *map(str, SMALI_ROOTS), '--glob', '*.smali'],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if run.returncode not in (0, 1):
        raise SystemExit(run.stderr)
    return [Path(line) for line in run.stdout.splitlines() if line]


def inbound(name: str) -> set[str]:
    own = find_class(name)
    return {declared_name(path) for path in rg_files(f'L{name};') if path != own}


def replace_method(text: str, signature: str, replacement: str, description: str) -> str:
    pattern = re.compile(rf'(?ms)^\.method[^\n]*{signature}\n.*?^\.end method\n?')
    result, count = pattern.subn(replacement.rstrip() + '\n', text, count=1)
    if count != 1:
        raise SystemExit(f'{description}: expected one method, got {count}')
    return result


def constructor_cases(target: str) -> dict[int, dict[str, int]]:
    token = f'L{target};-><init>'
    result: dict[int, dict[str, int]] = {}
    for path in rg_files(token):
        owner = declared_name(path)
        registers: dict[str, int | None] = {}
        for line in path.read_text(errors='ignore').splitlines():
            text = line.strip()
            if text.startswith('.method'):
                registers = {}
                continue
            match = re.match(
                r'const(?:/4|/16|/high16)?\s+([vp]\d+),\s+(-?0x[0-9a-f]+|-?\d+)',
                text,
            )
            if match:
                try:
                    registers[match.group(1)] = int(match.group(2), 0)
                except ValueError:
                    registers[match.group(1)] = None
                continue
            match = re.match(
                r'move(?:-object)?(?:/from16|/16)?\s+([vp]\d+),\s+([vp]\d+)',
                text,
            )
            if match:
                registers[match.group(1)] = registers.get(match.group(2))
                continue
            if token not in text:
                continue
            args_match = re.search(r'\{([^}]*)\}', text)
            if not args_match:
                raise SystemExit(f'{path}: constructor args missing')
            args = [item.strip() for item in args_match.group(1).split(',') if item.strip()]
            value = registers.get(args[-1])
            if value is None:
                continue
            owners = result.setdefault(value, {})
            owners[owner] = owners.get(owner, 0) + 1
    return result


def prune_cql_factories() -> None:
    path = find_class('cql')
    text = path.read_text()
    match = re.search(r'(?ms)^\.method public final a\(\)Ljava/lang/Object;\n.*?^\.end method', text, re.M)
    if not match:
        raise SystemExit('cql a() factory method missing')
    body = match.group(0)
    switch = re.search(
        r'(?ms)^\s*(:pswitch_data_0)\s*\n\s*\.packed-switch\s+0x0\s*\n'
        r'(.*?)^\s*\.end packed-switch',
        body,
        re.M,
    )
    if not switch:
        raise SystemExit('cql packed switch missing')
    labels = re.findall(r':pswitch_[0-9a-f]+', switch.group(2))
    mapping = {index: label for index, label in enumerate(labels)}
    if mapping.get(19) != ':pswitch_0':
        raise SystemExit(f'cql case 19 mapping changed: {mapping.get(19)}')

    data, count = re.subn(
        r'(?m)^(\s*):pswitch_0\s*$',
        r'\1:pswitch_1',
        switch.group(2),
        count=1,
    )
    if count != 1:
        raise SystemExit(f'cql case19 table count {count}')
    body = body[:switch.start(2)] + data + body[switch.end(2):]

    table_pos = body.rfind(':pswitch_data_0')
    case19 = re.search(r'(?ms)^\s*:pswitch_0\s*$.*?(?=^\s*:pswitch_1\s*$)', body[:table_pos], re.M)
    if not case19 or 'Lhre;' not in case19.group(0) or 'Lhrd;' not in case19.group(0):
        raise SystemExit('cql hrd/hre case19 branch layout changed')
    body = body[:case19.start()] + body[case19.end():]

    switch_instruction = re.search(r'(?m)^\s*packed-switch\s+v0,\s+:pswitch_data_0\s*$', body)
    first_label = re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$', body[switch_instruction.end():table_pos]) if switch_instruction else None
    if not switch_instruction or not first_label:
        raise SystemExit('cql default branch bounds missing')
    default_start = switch_instruction.end()
    default_end = switch_instruction.end() + first_label.start()
    default = body[default_start:default_end]
    if 'Lhrh;' not in default or 'Lhrg;' not in default:
        raise SystemExit('cql hrg/hrh default branch layout changed')
    body = body[:default_start] + '\n' + body[default_end:]
    text = text[:match.start()] + body + text[match.end():]
    path.write_text(text)
    print('cql: removed Jarvis helper factories for discriminators 19 and 20')


def patch_hpc() -> None:
    path = find_class('hpc')
    text = path.read_text()
    for field in ('o:Lpqq;', 'p:Lpqu;', 'q:Lpqt;', 'r:Lpqt;'):
        text, count = re.subn(rf'(?m)^\.field private(?: final)? {re.escape(field)}\n\n?', '', text, count=1)
        if count != 1:
            raise SystemExit(f'hpc field {field}: count {count}')

    constructor = '''.method public constructor <init>(Landroid/content/Context;Loep;Lgvs;)V
    .locals 1

    invoke-direct {p0}, Lgve;-><init>()V

    new-instance v0, Lhpb;

    invoke-direct {v0, p0}, Lhpb;-><init>(Lhpc;)V

    iput-object v0, p0, Lhpc;->s:Lmgp;

    iput-object p1, p0, Lhpc;->m:Landroid/content/Context;

    iput-object p2, p0, Lhpc;->n:Loep;

    iput-object p3, p0, Lhpc;->l:Lgvs;

    return-void
.end method'''
    text = replace_method(
        text,
        r'constructor <init>\(Landroid/content/Context;Loep;Lgvs;Lpqq;Lpqu;\)V',
        constructor,
        'hpc metrics-dependent constructor',
    )

    on_create = '''.method public final fG(Landroid/content/Context;Lptt;)V
    .locals 1

    const-string v0, "JarvisPromptExtension.onCreate"

    invoke-static {v0}, Landroid/os/Trace;->beginSection(Ljava/lang/String;)V

    :try_start_0
    invoke-super {p0, p1, p2}, Lgve;->fG(Landroid/content/Context;Lptt;)V

    iget-object p0, p0, Lhpc;->s:Lmgp;

    sget-object p1, Lncs;->a:Lncs;

    invoke-virtual {p0, p1}, Lmgp;->d(Ljava/util/concurrent/Executor;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    return-void

    :catchall_0
    move-exception p0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    throw p0
.end method'''
    text = replace_method(
        text,
        r'fG\(Landroid/content/Context;Lptt;\)V',
        on_create,
        'hpc onCreate metrics registration',
    )

    on_destroy = '''.method public final fH()V
    .locals 1

    const-string v0, "JarvisPromptExtension.onDestroy"

    invoke-static {v0}, Landroid/os/Trace;->beginSection(Ljava/lang/String;)V

    :try_start_0
    iget-object v0, p0, Lhpc;->s:Lmgp;

    invoke-virtual {v0}, Lmgp;->e()V

    invoke-super {p0}, Lgve;->fH()V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    return-void

    :catchall_0
    move-exception p0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    throw p0
.end method'''
    text = replace_method(text, r'fH\(\)V', on_destroy, 'hpc onDestroy metrics unregister')
    path.write_text(text)
    print('hpc: removed Jarvis metrics fields, dependencies, registration, and teardown')


def patch_eqt_factory() -> None:
    path = find_class('eqt')
    text = path.read_text()
    factory = '''.method public final v()Lhpc;
    .locals 5

    new-instance v1, Lhpc;

    new-instance v3, Lcom/google/android/libraries/inputmethod/genai/conversational/ConversationalRewritePrompterImpl;

    invoke-static {}, Lnck;->a()Lnck;

    move-result-object v0

    iget-object v0, v0, Lnck;->c:Lwzg;

    iget-object p0, p0, Leqt;->ja:Lytk;

    iget-object p0, p0, Lytk;->a:Ljava/lang/Object;

    move-object v2, p0

    check-cast v2, Landroid/content/Context;

    invoke-direct {v3, v2, v0}, Lcom/google/android/libraries/inputmethod/genai/conversational/ConversationalRewritePrompterImpl;-><init>(Landroid/content/Context;Ljava/util/concurrent/Executor;)V

    invoke-static {v2}, Lcom/google/android/libraries/inputmethod/module/ModuleManager;->getInstance(Landroid/content/Context;)Lcom/google/android/libraries/inputmethod/module/ModuleManager;

    move-result-object p0

    const-class v0, Lgvs;

    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/module/ModuleManager;->b(Ljava/lang/Class;)Lptg;

    move-result-object p0

    move-object v4, p0

    check-cast v4, Lgvs;

    invoke-direct/range {v1 .. v4}, Lhpc;-><init>(Landroid/content/Context;Loep;Lgvs;)V

    return-object v1
.end method'''
    text = replace_method(text, r'v\(\)Lhpc;', factory, 'eqt Jarvis factory')
    path.write_text(text)
    print('eqt: removed Jarvis Clearcut adapter/metrics-manager provider loads')


paths = {name: find_class(name) for name in DELETE}
for name, expected in EXPECTED_INBOUND.items():
    actual = inbound(name)
    if actual != expected:
        raise SystemExit(f'{name}: inbound {sorted(actual)} != {sorted(expected)}')
cases = constructor_cases('cql')
if cases.get(19) != {'hrd': 1} or cases.get(20) != {'hrg': 1}:
    raise SystemExit(f'cql Jarvis constructor cases changed: 19={cases.get(19)} 20={cases.get(20)}')
if any(case > 20 for case in cases):
    raise SystemExit(f'cql unexpected default-switch constructors: {sorted(c for c in cases if c > 20)}')

prune_cql_factories()
patch_hpc()
patch_eqt_factory()

bytes_removed = sum(path.stat().st_size for path in paths.values())
for name in sorted(paths):
    paths[name].unlink()
    print('deleted Jarvis metrics class', name)
for name in sorted(paths):
    refs = rg_files(f'L{name};')
    if refs:
        raise SystemExit(f'{name}: residual refs {[str(p.relative_to(ROOT)) for p in refs[:20]]}')
hpc = find_class('hpc').read_text(errors='ignore')
for residue in ('Lhpc;->o:Lpqq;', 'Lhpc;->p:Lpqu;', 'Lhpc;->q:Lpqt;', 'Lhpc;->r:Lpqt;'):
    if residue in hpc:
        raise SystemExit(f'hpc residual metrics field {residue}')
if '<init>(Landroid/content/Context;Loep;Lgvs;Lpqq;Lpqu;)V' in find_class('eqt').read_text(errors='ignore'):
    raise SystemExit('eqt old Jarvis metrics constructor call remains')

print(f'physically removed Jarvis prompt metrics processors: {len(paths)} classes / {bytes_removed} smali bytes')
