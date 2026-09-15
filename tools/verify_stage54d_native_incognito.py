#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
def req(x,m):
    if not x: raise SystemExit('FAIL: '+m)
inc=(root/'smali_classes2/com/mekromn/meboard/IncognitoToggleAction.smali').read_text()
mlq=(root/'smali/mlq.smali').read_text()
mlr=(root/'smali/mlr.smali').read_text()
sk=(root/'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali').read_text()
pbv=(root/'smali_classes2/pbv.smali').read_text()
fjo=(root/'smali_classes2/fjo.smali').read_text()
clip=(root/'smali_classes2/com/mekromn/meboard/ClipboardTimeoutPreference.smali').read_text()
clipsum=(root/'smali_classes2/com/mekromn/meboard/ClipboardTimeoutSummaryProvider.smali').read_text()
req('0x1000000' in inc,'no no-personalized-learning flag')
req('Look;->i()V' in inc,'native InputBundle.reactivateIme missing')
req('Lowq;->e(Landroid/view/inputmethod/EditorInfo;Landroid/view/inputmethod/EditorInfo;ZZZ)V' in inc,'InputSessionNotification publish missing')
req('Toast;' not in inc and 'Incognito mode on' not in inc and 'Incognito mode off' not in inc,'toast remains')
req('.method public final hn(Landroid/view/inputmethod/EditorInfo;Landroid/view/inputmethod/EditorInfo;ZZ)V' in mlq,'mlq input-view update missing')
req('Lmlq;->d(Landroid/view/inputmethod/EditorInfo;ZZ)V' in mlq,'mlq native header delegate missing')
req('0x7f080715' in mlr,'stock native incognito icon definition missing')
for x in ['0x7f0b0603','0x7f0b0604','0x7f0b0608','0x7f0b060a','0x7f08071a','0x7f0803f7']:
    req(x in sk,'key/icon marker missing '+x)
req('Lcom/mekromn/meboard/CustomLongPressKeys;->type(Lpvi;)I' in pbv,'Stage54c long-press path missing')
req('ClipboardRetentionConfig;->getMillis' in fjo,'clipboard retention hook missing')
for x in ['1 hour','3 hours','6 hours','12 hours','24 hours']:
    req(x in clip,'clipboard UI regression '+x)
req('Current: ' in clipsum,'clipboard current-summary regression')
joined='\n'.join(p.read_text(errors='replace') for p in root.rglob('*.smali'))
for x in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;']:
    req(x in joined,'Moonshine regression '+x)
print('PASS Stage54d static gates')
