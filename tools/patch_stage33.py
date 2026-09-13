#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, argparse

EXPECTED = {
 'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyboardView.smali':'44ae1d0068f87e108e087c3513fa5000359c15afc84e23f63a468f6c90626164',
 'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali':'e57780a62c762171d16afc08abb3cac7fe0ebf4423ade9b5d2233440bfcfb779',
 'smali/com/mekromn/meboard/MeboardThemeMode.smali':'076db780f9207a7d9265fff2ad899ab998aaaf03e0877266ad9598b244c2955d',
 'smali/com/mekromn/meboard/MeboardThemeMode$Listener.smali':'9895c515d44c6f3b4fe94118d2d507bea6f1ccc7ec67693c52e0cca834177186',
 'smali/com/mekromn/meboard/VoiceProviderChooser.smali':'8fc26c4db26490f873f1d822f7300bf0df39c65a1f0d8a73786e1831d20b6db7',
}

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(x,msg):
    if not x: raise RuntimeError(msg)
def replace(path:Path, old:str, new:str, count=1):
    s=path.read_text(); c=s.count(old)
    req(c==count, f'{path.name}: expected {count} matches, got {c}')
    path.write_text(s.replace(old,new,count))

def patch(root:Path):
    for rel,h in EXPECTED.items():
        p=root/rel; req(p.is_file(),f'missing {rel}'); req(sha(p)==h,f'input drift {rel}: {sha(p)}')

    theme=root/'smali/com/mekromn/meboard/MeboardThemeMode.smali'
    listener=root/'smali/com/mekromn/meboard/MeboardThemeMode$Listener.smali'
    chooser=root/'smali/com/mekromn/meboard/VoiceProviderChooser.smali'
    skv=root/'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyboardView.smali'
    key=root/'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali'

    insert = r'''
.method public static updatePreview(Landroid/view/View;Z)V
    .locals 3

    :try_start_0
    if-eqz p0, :cond_2

    const v0, 0x7f0b2a51
    invoke-virtual {p0, v0}, Landroid/view/View;->findViewById(I)Landroid/view/View;
    move-result-object v0
    invoke-static {v0, p1}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreviewView(Landroid/view/View;Z)V

    const v0, 0x7f0b2a52
    invoke-virtual {p0, v0}, Landroid/view/View;->findViewById(I)Landroid/view/View;
    move-result-object v0
    invoke-static {v0, p1}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreviewView(Landroid/view/View;Z)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :cond_2
    return-void
    :catch_0
    move-exception v0
    return-void
.end method

.method private static updatePreviewView(Landroid/view/View;Z)V
    .locals 3
    if-eqz p0, :cond_1
    instance-of v0, p0, Landroid/widget/ImageView;
    if-eqz v0, :cond_1
    check-cast p0, Landroid/widget/ImageView;
    if-eqz p1, :cond_0
    const/high16 v0, -0x1000000
    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setBackgroundColor(I)V
    const v0, 0x3f6147ae
    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setAlpha(F)V
    const/high16 v0, 0x33000000
    sget-object v1, Landroid/graphics/PorterDuff$Mode;->SRC_ATOP:Landroid/graphics/PorterDuff$Mode;
    invoke-virtual {p0, v0, v1}, Landroid/widget/ImageView;->setColorFilter(ILandroid/graphics/PorterDuff$Mode;)V
    goto :goto_0
    :cond_0
    invoke-virtual {p0}, Landroid/widget/ImageView;->clearColorFilter()V
    const/high16 v0, 0x3f800000
    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setAlpha(F)V
    const/4 v0, 0x0
    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setBackgroundColor(I)V
    :cond_1
    :goto_0
    return-void
.end method
'''
    s=theme.read_text(); marker='.method public static setPending(Landroid/view/View;Z)V'
    req(marker in s,'setPending marker missing'); theme.write_text(s.replace(marker,insert+'\n'+marker,1))

    replace(theme,'''    :goto_0\n    new-instance v7, Lcom/mekromn/meboard/MeboardThemeMode$Listener;\n''','''    :goto_0\n    invoke-static {v11, v7}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreview(Landroid/view/View;Z)V\n\n    new-instance v7, Lcom/mekromn/meboard/MeboardThemeMode$Listener;\n''')
    replace(theme,'''    invoke-static {p1}, Lcom/mekromn/meboard/MeboardGlass;->applyTree(Landroid/view/View;)V\n\n    invoke-virtual {v0, p1}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;\n''','''    invoke-static {p1, v1}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreview(Landroid/view/View;Z)V\n\n    invoke-virtual {v0, p1}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;\n''')
    replace(theme,'''    sget-object v0, Lcom/mekromn/meboard/MeboardThemeMode;->a:Ljava/util/WeakHashMap;\n\n    invoke-virtual {v0, p0}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;\n''','''    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;\n    move-result-object v0\n    invoke-static {v0}, Lcom/mekromn/meboard/MeboardGlass;->enabled(Landroid/content/Context;)Z\n    move-result v0\n    invoke-static {p0, v0}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreview(Landroid/view/View;Z)V\n    sget-object v0, Lcom/mekromn/meboard/MeboardThemeMode;->a:Ljava/util/WeakHashMap;\n    invoke-virtual {v0, p0}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;\n''')
    replace(listener,'''    invoke-static {v1, v0}, Lcom/mekromn/meboard/MeboardThemeMode;->setPending(Landroid/view/View;Z)V\n\n    :cond_1\n''','''    invoke-static {v1, v0}, Lcom/mekromn/meboard/MeboardThemeMode;->setPending(Landroid/view/View;Z)V\n    invoke-static {v1, v0}, Lcom/mekromn/meboard/MeboardThemeMode;->updatePreview(Landroid/view/View;Z)V\n\n    :cond_1\n''')

    replace(skv,'''    invoke-super {p0}, Lcom/google/android/libraries/inputmethod/widgets/AdditionalPaddingFrameLayout;->onAttachedToWindow()V\n\n    .line 2\n''','''    invoke-super {p0}, Lcom/google/android/libraries/inputmethod/widgets/AdditionalPaddingFrameLayout;->onAttachedToWindow()V\n    invoke-static {p0}, Lcom/mekromn/meboard/MeboardGlass;->applyBody(Landroid/view/View;)V\n\n    .line 2\n''')
    replace(skv,'''    :cond_0\n    iget-object p0, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyboardView;->M:Ljava/util/ArrayList;\n''','''    :cond_0\n    if-nez p2, :meboard_visibility_no_glass\n    invoke-static {p0}, Lcom/mekromn/meboard/MeboardGlass;->applyBody(Landroid/view/View;)V\n    :meboard_visibility_no_glass\n    iget-object p0, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyboardView;->M:Ljava/util/ArrayList;\n''')

    s=chooser.read_text(); marker='.method public static showChooser(Landroid/view/View;)Z'
    method=r'''
.method public static prepareVoiceKey(Landroid/view/View;)V
    .locals 1
    :try_start_0
    invoke-static {p0}, Lcom/mekromn/meboard/VoiceProviderChooser;->isVoiceKey(Landroid/view/View;)Z
    move-result v0
    if-eqz v0, :cond_0
    const/4 v0, 0x1
    invoke-virtual {p0, v0}, Landroid/view/View;->setLongClickable(Z)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0
    :cond_0
    return-void
    :catch_0
    move-exception v0
    return-void
.end method

'''
    req(marker in s,'showChooser marker missing'); chooser.write_text(s.replace(marker,method+marker,1))

    replace(key,'''    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V\n\n    .line 8\n''','''    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V\n    invoke-static {p0}, Lcom/mekromn/meboard/VoiceProviderChooser;->prepareVoiceKey(Landroid/view/View;)V\n\n    .line 8\n''')
    replace(key,'''    iget-boolean v0, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->o:Z\n\n    .line 7\n    .line 8\n    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->setLongClickable(Z)V\n\n    .line 9\n''','''    iget-boolean v0, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->o:Z\n\n    .line 7\n    .line 8\n    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->setLongClickable(Z)V\n    invoke-static {p0}, Lcom/mekromn/meboard/VoiceProviderChooser;->prepareVoiceKey(Landroid/view/View;)V\n\n    .line 9\n''')

    req('prepareVoiceKey' in chooser.read_text(),'mic long-click preparation missing')
    req('updatePreview(Landroid/view/View;Z)V' in theme.read_text(),'preview update missing')
    req(skv.read_text().count('MeboardGlass;->applyBody(Landroid/view/View;)V')==2,'expected 2 safe glass runtime hooks')
    req(key.read_text().count('prepareVoiceKey(Landroid/view/View;)V')==2,'expected 2 mic preparation hooks')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args(); patch(a.root.resolve()); print('Stage33 patch PASS')
