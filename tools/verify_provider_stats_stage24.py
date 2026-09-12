#!/usr/bin/env python3
"""Independent preservation checks for Stage-24 provider-statistics excision.

The interpreter executes only the reviewed provider-setup prefix and models
external calls. It is NOT Android execution and cannot certify device behavior.
It compares retained operations, lock balance, exits, and live boundary registers.
"""
from __future__ import annotations
import argparse, collections, itertools, json, re
from pathlib import Path

TARGET = 'smali_classes2/com/google/android/gms/learning/dynamite/training/InAppTrainingServiceImpl.smali'
HELPER = 'smali/qqg.smali'
M = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')


def check(ok, msg):
    if not ok:
        raise ValueError(msg)


def method_map(text):
    return {s.splitlines()[0].split()[-1]:s for s in M.findall(text)}


def parse(body):
    code = []
    labels = {}
    catches = []
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        match = re.fullmatch(r'\.catch(all)?(?: (\S+))? \{(:\w+) \.\. (:\w+)\} (:\w+)', s)
        if match:
            catches.append((match[3], match[4], match[5], None if match[1] else match[2]))
        elif s.startswith(':'):
            check(s not in labels, 'Duplicate label')
            labels[s] = len(code)
        elif not s.startswith('.'):
            code.append(s)
    return code, labels, [(labels[a],labels[b],labels[h],t) for a,b,h,t in catches]


def register_index(name, locals_count=43):
    return int(name[1:]) + (locals_count if name.startswith('p') else 0)


def registers(s):
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    if '{' in s:
        spec = s[s.index('{')+1:s.index('}')]
        if ' .. ' in spec:
            a,b = spec.split(' .. ')
            return list(range(register_index(a), register_index(b)+1))
        return [register_index(r) for r in re.findall(r'\b[vp]\d+\b', spec)]
    return [register_index(r) for r in re.findall(r'\b[vp]\d+\b', s.split(', L')[0])]


def uses_defs(s):
    op = s.split()[0]
    rr = registers(s)
    pair = lambda i: {i, i+1}
    if op.startswith('invoke') or op == 'filled-new-array':
        return set(rr), set()
    if op.startswith(('return', 'throw', 'monitor', 'if-')):
        return (pair(rr[0]) if 'wide' in op and rr else set(rr)), set()
    if op.startswith('goto') or op == 'nop':
        return set(), set()
    if op == 'check-cast':
        return {rr[0]}, {rr[0]}
    if op.startswith(('move-result','move-exception','const','new-instance','sget')):
        return set(), pair(rr[0]) if 'wide' in op else {rr[0]}
    if op.startswith('move'):
        return (pair(rr[1]),pair(rr[0])) if 'wide' in op else ({rr[1]},{rr[0]})
    if op.startswith('iget'):
        return {rr[1]}, pair(rr[0]) if 'wide' in op else {rr[0]}
    if op.startswith('iput'):
        return ((pair(rr[0]) | {rr[1]}) if 'wide' in op else set(rr)), set()
    if op.startswith('sput'):
        return (pair(rr[0]) if 'wide' in op else set(rr)), set()
    if op == 'new-array':
        return {rr[1]}, {rr[0]}
    if op.startswith('aput'):
        return set(rr), set()
    if op in ('and-int/lit8','add-int/lit8'):
        return {rr[1]}, {rr[0]}
    raise ValueError('Unhandled liveness opcode: ' + s)


def live_at_boundaries(body):
    c, labels, catches = parse(body)
    data = [uses_defs(s) for s in c]
    edges = []
    exception_edges = []
    for i,s in enumerate(c):
        op = s.split()[0]
        if op.startswith('goto'):
            following = [labels[s.split()[-1]]]
        elif op.startswith('if-'):
            following = [i+1, labels[s.split()[-1]]]
        elif op.startswith(('return','throw')):
            following = []
        else:
            following = [i+1]
        edges.append([j for j in following if j < len(c)])
        # Conservative exceptional edges retain the pre-instruction register
        # state, not the normal result of a throwing write.
        exception_edges.append([h for a,b,h,t in catches if a <= i < b])
    live = [set() for _ in c]
    changed = True
    while changed:
        changed = False
        for i in reversed(range(len(c))):
            use,defs = data[i]
            normal = set().union(*(live[j] for j in edges[i])) if edges[i] else set()
            thrown = set().union(*(live[j] for j in exception_edges[i])) if exception_edges[i] else set()
            new = use | (normal - defs) | thrown
            if new != live[i]:
                live[i] = new
                changed = True
    return {label: live[labels[label]] for label in (':goto_a', ':goto_32')}


class Fault(Exception):
    def __init__(self, typ, site):
        self.value = ('exception',typ,site)
        super().__init__(typ)


def matches(actual, caught):
    if caught is None or actual == caught:
        return True
    if caught == 'Ljava/lang/Exception;':
        return actual != 'Ljava/lang/Error;'
    return False


def simulate(body, scenario, needed):
    c,labels,catches = parse(body)
    r = {43+i: ('param',i) for i in range(16)}
    r[43] = {'k':'resource_token','b':'app_context','d':'config'}
    state = {'initialised': scenario['cached']}
    trace = []
    reporting = []
    depth = 0
    result = None
    exception = None
    clocks = 0
    ip = 0
    steps = 0
    boundary_by_index = {labels[n]:n for n in needed}

    def get(reg):
        idx = register_index(reg)
        check(idx in r, 'Uninitialised register read: ' + reg)
        return r[idx]

    def put(reg, value, wide=False):
        idx = register_index(reg)
        r[idx] = value
        if wide:
            r[idx+1] = ('wide-high',value)

    def fail(site):
        if scenario.get('fault_site') == site:
            raise Fault(scenario['fault_type'],site)

    while ip < len(c):
        if ip in boundary_by_index:
            name = boundary_by_index[ip]
            return {'boundary':name,'trace':trace,'monitor_depth':depth,
                    'initialised':state['initialised'],
                    'live_registers':{str(i):r.get(i,('undefined',)) for i in sorted(needed[name])}}, reporting, clocks
        steps += 1
        check(steps < 1000, 'Prefix execution limit')
        s = c[ip]
        op = s.split()[0]
        try:
            if op.startswith('move-result'):
                put(s.split()[1],result,'wide' in op)
            elif op == 'move-exception':
                put(s.split()[1],exception)
            elif op.startswith('move'):
                d,src = s.split(' ',1)[1].split(', ')
                put(d,get(src),'wide' in op)
            elif op.startswith('const-string'):
                d,v = s.split(' ',1)[1].split(', ',1)
                put(d,json.loads(v))
            elif op == 'const-class':
                d,v = s.split(' ',1)[1].split(', ')
                put(d,('class',v))
            elif op.startswith('const'):
                d,v = s.split(' ',1)[1].split(', ')
                put(d,int(v,0),'wide' in op)
            elif op == 'iget-object':
                m = re.fullmatch(r'iget-object (\w+), (\w+), L[^;]+;->(\w+):.*',s)
                put(m[1],get(m[2])[m[3]])
            elif op == 'sget-object':
                d,v = s.split(' ',1)[1].split(', ')
                put(d,'monitor' if v == 'Llrz;->a:Ljava/lang/Object;' else v)
            elif op == 'sget-boolean':
                put(s.split()[1].rstrip(','),int(state['initialised']))
            elif op == 'sput-boolean':
                state['initialised'] = bool(get(s.split()[1].rstrip(',')))
            elif op == 'new-instance':
                d,typ = s.split(' ',1)[1].split(', ')
                put(d,{'type':typ})
            elif op == 'new-array':
                d,n,_ = s.split(' ',1)[1].split(', ')
                put(d,[None]*get(n))
            elif op == 'aput-object':
                v,a,n = s.split(' ',1)[1].split(', ')
                get(a)[get(n)] = get(v)
            elif op == 'monitor-enter':
                check(get(s.split()[1]) == 'monitor','Wrong monitor')
                depth += 1
            elif op == 'monitor-exit':
                check(get(s.split()[1]) == 'monitor','Wrong monitor')
                depth -= 1
                check(depth >= 0, 'Monitor underflow')
            elif op.startswith('goto'):
                ip = labels[s.split()[-1]]
                continue
            elif op.startswith('if-'):
                args = s.split(' ',1)[1].split(', ')
                val = get(args[0])
                zero = val is None or val == 0
                check(op in ('if-eqz','if-nez'),'Unsupported provider branch')
                take = zero if op == 'if-eqz' else not zero
                if take:
                    ip = labels[args[-1]]
                    continue
            elif op.startswith('invoke'):
                m = re.fullmatch(r'\S+ \{(.*?)\}, (.+)',s)
                spec, method = m.groups()
                if ' .. ' in spec:
                    a,b = spec.split(' .. ')
                    args = [r[i] for i in range(register_index(a),register_index(b)+1)]
                else:
                    args = [get(q) for q in spec.split(', ')] if spec else []
                if method == 'Ltid;->d()V':
                    trace.append(('resource_enter',args[0]))
                elif method == 'Llgy;->e(Ltiv;)V':
                    trace.append(('local_event',args[0],args[1]))
                elif method == 'Llgp;->be()Z':
                    result = int(scenario['enabled'])
                elif method.startswith('Llcw;->ax('):
                    trace.append(('check_context',args[0]))
                    fail('check_context')
                elif method.startswith('Lkvz;->c('):
                    trace.append(('check_services',*args))
                    fail('check_services')
                elif method == 'Landroid/os/SystemClock;->uptimeMillis()J':
                    clocks += 1
                    result = 1000+clocks
                elif method.startswith('Llet;->d('):
                    trace.append(('load_module',args[0],args[2]))
                    fail('load_module')
                    result = {'e': 'dynamite_context' if scenario['dynamite'] else None}
                elif method.startswith('Landroid/content/Context;->createPackageContext('):
                    trace.append(('fallback_context',*args))
                    fail('create_context')
                    result = 'fallback_context' if scenario['fallback'] else None
                elif method.startswith('Llrz;->a('):
                    trace.append(('install_provider',*args))
                    fail('install_dynamite' if args[0] == 'dynamite_context' else 'install_fallback')
                elif method.startswith('Landroid/content/Context;->getClassLoader('):
                    result = 'stats_classloader'
                elif method.startswith('Lqqg;-><init>('):
                    args[0].update({'klass':args[1],'value':args[2]})
                elif method == 'Lqqg;->o(J)Lqqg;':
                    result = {'klass':'long','value':args[0]}
                elif method.startswith('Ljava/lang/ClassLoader;->loadClass('):
                    result = ('stats_class',args[1])
                elif method.startswith('Llcw;->bd('):
                    reporting.append(('report',args[1],args[2]))
                    fail('report')
                    result = None
                elif method in ('Llep;->getMessage()Ljava/lang/String;', 'Ljava/lang/Object;->toString()Ljava/lang/String;'):
                    result = str(args[0])
                elif method == 'Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;':
                    result = str(args[0])
                elif method == 'Ljava/lang/String;->concat(Ljava/lang/String;)Ljava/lang/String;':
                    result = args[0]+args[1]
                elif method.startswith('Landroid/util/Log;->'):
                    if not str(args[1]).startswith('Failed to report request stats: '):
                        trace.append(('log',*args))
                    result = 0
                elif method == 'Lkvx;-><init>()V':
                    args[0]['exception'] = ('exception','Lkvx;','missing_fallback')
                else:
                    raise ValueError('Unmodelled provider call: '+method)
            elif op == 'throw':
                ex = get(s.split()[1])
                if isinstance(ex,dict):
                    ex = ex['exception']
                raise Fault(ex[1],ex[2])
            else:
                raise ValueError('Unmodelled provider opcode: '+s)
        except Fault as f:
            exception = f.value
            handlers = [h for a,b,h,t in catches if a <= ip < b and matches(exception[1],t)]
            check(bool(handlers),'Unhandled exception in reviewed prefix')
            ip = handlers[0]
            continue
        ip += 1
    raise ValueError('Provider prefix did not reach a comparison boundary')


def scenario_tests(old, new):
    old_live = live_at_boundaries(old)
    new_live = live_at_boundaries(new)
    check(old_live == new_live, 'Common-suffix live registers changed')
    needed = old_live
    check(not ({15,16,19,20} & set().union(*needed.values())), 'Removed timestamps remain live at retained boundary')
    faults = [(None,None)]
    for site,types in {
        'check_context':['Ljava/lang/RuntimeException;'],
        'check_services':['Lkvx;','Lkvy;','Ljava/lang/RuntimeException;'],
        'load_module':['Llep;','Ljava/lang/RuntimeException;'],
        'create_context':['Landroid/content/pm/PackageManager$NameNotFoundException;','Ljava/lang/RuntimeException;'],
        'install_dynamite':['Lkvx;','Ljava/lang/RuntimeException;'],
        'install_fallback':['Lkvx;','Ljava/lang/RuntimeException;'],
        'report':['Ljava/lang/Exception;'],
    }.items():
        faults.extend((site,t) for t in types)
    total = 0
    original_report_paths = 0
    seen_exits = collections.Counter()
    for enabled,cached,dynamite,fallback in itertools.product((False,True),repeat=4):
        for site,typ in faults:
            scenario = dict(enabled=enabled,cached=cached,dynamite=dynamite,fallback=fallback,fault_site=site,fault_type=typ)
            before,reports,clocks = simulate(old,scenario,needed)
            after,new_reports,new_clocks = simulate(new,scenario,needed)
            check(before == after, 'Provider behavior mismatch: '+repr(scenario)+'\n'+repr(before)+'\n'+repr(after))
            check(after['monitor_depth'] == 0, 'Monitor leaked')
            check(not new_reports and new_clocks == 0,'Reporting/collection still executes')
            total += 1
            original_report_paths += bool(reports)
            seen_exits[after['boundary']] += 1
    # Sensitivity: changing fallback provider identity must change observable trace.
    wrong = new.replace('const-string v0, "com.google.android.gms.common.security.ProviderInstallerImpl"',
                        'const-string v0, "wrong.ProviderInstallerImpl"',1)
    scenario = dict(enabled=True,cached=True,dynamite=False,fallback=True,fault_site=None,fault_type=None)
    check(simulate(wrong,scenario,needed)[0] != simulate(new,scenario,needed)[0], 'Mutation check insensitive')
    return {'matched_scenarios':total,'original_reporting_paths_exercised':original_report_paths,
            'exit_counts':dict(seen_exits),'live_registers_at_boundaries':{k:sorted(v) for k,v in needed.items()},
            'new_reporting_calls':0,'new_uptime_captures':0,'monitor_balanced_in_all_scenarios':True,
            'wrong_provider_identity_mutation_detected':True,
            'scope':'bounded provider-prefix interpreter; external calls modelled, not Android runtime'}


def verify(before:Path,after:Path):
    b = {p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a = {p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    check(a.keys() == b.keys(),'Class set changed')
    changed = {p for p in a if a[p] != b[p]}
    check(changed == {TARGET,HELPER}, 'Unexpected changed-class set')
    bm,am = method_map(b[TARGET]),method_map(a[TARGET])
    check(bm.keys() == am.keys(),'Training class method signature changed')
    edited = [sig for sig in bm if bm[sig] != am[sig]]
    check(len(edited) == 1, 'Expected one edited provider-prefix method')
    old,new = bm[edited[0]],am[edited[0]]
    check(old.splitlines()[0:2] == new.splitlines()[0:2], 'Method signature/register layout changed')
    check(old[old.index('    :goto_5\n'):] == new[new.index('    :goto_5\n'):], 'Retained provider/local-runner tail changed')
    bhelp,ahelp = method_map(b[HELPER]),method_map(a[HELPER])
    check(set(bhelp)-set(ahelp) == {'o(J)Lqqg;'} and not set(ahelp)-set(bhelp), 'Helper method set mismatch')
    check(all(ahelp[s] == bhelp[s] for s in ahelp),'Retained helper methods changed')
    for p in changed:
        outside = lambda t: re.sub(r'\s+',' ',M.sub('',t)).strip()
        check(outside(a[p]) == outside(b[p]), 'Class declaration or fields changed')
    for p,text in a.items():
        check('reportRequestStats2' not in text and 'Failed to report request stats: ' not in text and 'Lqqg;->o(J)Lqqg;' not in text, 'Reporting residue '+p)
    scenarios = scenario_tests(old,new)
    count = 0
    for p in before.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0] == 'build':
            continue
        q = after/rel
        check(q.is_file() and p.read_bytes() == q.read_bytes(), 'Non-code file changed: '+str(rel))
        count += 1
    return {'passed':True,'unchanged_class_files':len(a)-2,
            'other_methods_in_changed_classes_exact':len(am)-1+len(ahelp),
            'provider_scenarios':scenarios,'shared_reflection_helper_preserved':a['smali/lcw.smali']==b['smali/lcw.smali'],
            'native_config_builder_preserved':a['smali_classes2/sal.smali']==b['smali_classes2/sal.smali'],
            'non_smali_files_compared':count,'runtime_tested':False,'privacy_final':False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('before',type=Path);ap.add_argument('after',type=Path);ap.add_argument('--json',type=Path)
    args=ap.parse_args();result=verify(args.before,args.after);out=json.dumps(result,indent=2)+'\n'
    if args.json:
        args.json.write_text(out)
    print(out)


if __name__=='__main__':
    main()
