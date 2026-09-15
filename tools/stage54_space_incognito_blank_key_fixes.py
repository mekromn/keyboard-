from pathlib import Path
import hashlib
root=Path('/mnt/data/stage54c_work')
# Exact Stage53 source guards for touched stock files.
expected={
 'smali/mhe.smali':'9d07ae0798cf72c609b0d5f5a5845ce180a3314dcecd99efeab74c3bbba4c460',
 'smali_classes2/pbv.smali':'bea83a88891847083e56018b057d8c72550b695fd7026b3f28cba377dac7d29b',
 'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali':'f7f6e54cf484d4d5bef8ab4df2ef2f4c1a2cd5d77f8b01fe090bf2f7c2761795',
}
for rel,h in expected.items():
 p=root/rel; g=hashlib.sha256(p.read_bytes()).hexdigest()
 if g!=h: raise SystemExit(f'drift {rel}: {g} != {h}')

# 1) Spacebar long press: nothing selected -> Select All; selection exists -> Copy.
p=root/'smali_classes2/pbv.smali'; s=p.read_text()
old='''    move-object v1, p0\n\n    .line 32\n    check-cast v1, Lpvi;\n\n    .line 33\n    .line 34\n    invoke-virtual {v1, v0}, Lpvi;->k(Lpmy;)Lcom/google/android/libraries/inputmethod/metadata/ActionDef;\n'''
new='''    move-object v1, p0\n\n    .line 32\n    check-cast v1, Lpvi;\n\n    # Meboard: Space long-press is a two-state text action.\n    # No selection -> Select All. Existing selection -> Copy current selection.\n    invoke-virtual {v1}, Lpvi;->m()Lcom/google/android/libraries/inputmethod/metadata/SoftKeyDef;\n    move-result-object v2\n    if-eqz v2, :meboard_space_longpress_normal\n    sget-object v3, Lpmy;->a:Lpmy;\n    invoke-virtual {v2, v3}, Lcom/google/android/libraries/inputmethod/metadata/SoftKeyDef;->h(Lpmy;)Lcom/google/android/libraries/inputmethod/metadata/ActionDef;\n    move-result-object v2\n    if-eqz v2, :meboard_space_longpress_normal\n    invoke-virtual {v2}, Lcom/google/android/libraries/inputmethod/metadata/ActionDef;->b()Lpnu;\n    move-result-object v2\n    if-eqz v2, :meboard_space_longpress_normal\n    iget v2, v2, Lpnu;->c:I\n    const/16 v3, 0x3e\n    if-ne v2, v3, :meboard_space_longpress_normal\n    iget-object v2, v1, Lpvi;->r:Lpvj;\n    check-cast v2, Lpvf;\n    iget-object v2, v2, Lpvf;->b:Landroid/content/Context;\n    invoke-static {v2}, Lcom/mekromn/meboard/SpacebarSelectionAction;->handle(Landroid/content/Context;)Z\n    move-result v2\n    if-eqz v2, :meboard_space_longpress_normal\n    # Consume the key gesture so release cannot also insert a space.\n    invoke-virtual {v1}, Lpvi;->C()V\n    return-void\n\n    :meboard_space_longpress_normal\n    .line 33\n    .line 34\n    invoke-virtual {v1, v0}, Lpvi;->k(Lpmy;)Lcom/google/android/libraries/inputmethod/metadata/ActionDef;\n'''
if s.count(old)!=1: raise SystemExit('space longpress anchor mismatch')
p.write_text(s.replace(old,new))

# 2) HEADER_MENU (four-square grid) gets LONG_PRESS incognito toggle; PRESS remains stock.
p=root/'smali/mhe.smali'; s=p.read_text()
old='''    :goto_1\n    if-nez v4, :cond_5\n'''
new='''    :goto_1\n    # Meboard: long-press the stable four-square HEADER_MENU key to toggle session incognito.\n    # PRESS remains untouched. Insert LONG_PRESS before stock access-point actions.\n    sget-object v6, Lmif;->d:Lmif;\n    if-ne p0, v6, :meboard_incognito_action_done\n    new-instance v6, Lpmz;\n    invoke-direct {v6}, Lpmz;-><init>()V\n    invoke-virtual {v6}, Lpmz;->k()V\n    sget-object v7, Lpmy;->b:Lpmy;\n    iput-object v7, v6, Lpmz;->a:Lpmy;\n    const/4 v7, 0x1\n    iput-boolean v7, v6, Lpmz;->e:Z\n    new-instance v7, Lcom/mekromn/meboard/IncognitoToggleActionRunnable;\n    invoke-direct {v7, v0}, Lcom/mekromn/meboard/IncognitoToggleActionRunnable;-><init>(Landroid/content/Context;)V\n    const v1, -0x9c47\n    const/4 v2, 0x0\n    invoke-virtual {v6, v1, v2, v7}, Lpmz;->q(ILpnt;Ljava/lang/Object;)V\n    invoke-virtual {v6}, Lpmz;->c()Lcom/google/android/libraries/inputmethod/metadata/ActionDef;\n    move-result-object v6\n    invoke-virtual {v5, v6}, Lppo;->t(Lcom/google/android/libraries/inputmethod/metadata/ActionDef;)V\n    :meboard_incognito_action_done\n    if-nez v4, :cond_5\n'''
if s.count(old)!=1: raise SystemExit('HEADER_MENU anchor mismatch')
p.write_text(s.replace(old,new))

# 3) Blank Shift / Emoji visual fallback. Hook after the key def/render update, before listeners.
p=root/'smali/com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali'; s=p.read_text()
old='''    :goto_2\n    iget-object p2, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->m:Ljava/util/concurrent/CopyOnWriteArrayList;\n'''
new='''    :goto_2\n    # Meboard: restore only genuinely missing Shift/Caps and Emoji key glyphs.\n    invoke-static {p0}, Lcom/mekromn/meboard/BlankKeyIconFix;->apply(Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;)V\n\n    iget-object p2, p0, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->m:Ljava/util/concurrent/CopyOnWriteArrayList;\n'''
if s.count(old)!=1: raise SystemExit('SoftKeyView hook anchor mismatch')
p.write_text(s.replace(old,new))

# Space helper in DEX2.
q=root/'smali_classes2/com/mekromn/meboard/SpacebarSelectionAction.smali'; q.parent.mkdir(parents=True,exist_ok=True)
q.write_text(r'''.class public final Lcom/mekromn/meboard/SpacebarSelectionAction;
.super Ljava/lang/Object;
.source "Meboard"

.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static handle(Landroid/content/Context;)Z
    .locals 4
    :unwrap
    instance-of v0, p0, Landroid/inputmethodservice/InputMethodService;
    if-nez v0, :service
    instance-of v0, p0, Landroid/content/ContextWrapper;
    if-eqz v0, :fail
    move-object v0, p0
    check-cast v0, Landroid/content/ContextWrapper;
    invoke-virtual {v0}, Landroid/content/ContextWrapper;->getBaseContext()Landroid/content/Context;
    move-result-object v0
    if-eqz v0, :fail
    if-eq v0, p0, :fail
    move-object p0, v0
    goto :unwrap

    :service
    check-cast p0, Landroid/inputmethodservice/InputMethodService;
    invoke-virtual {p0}, Landroid/inputmethodservice/InputMethodService;->getCurrentInputConnection()Landroid/view/inputmethod/InputConnection;
    move-result-object v0
    if-eqz v0, :fail
    const/4 v1, 0x0
    invoke-interface {v0, v1}, Landroid/view/inputmethod/InputConnection;->getSelectedText(I)Ljava/lang/CharSequence;
    move-result-object v2
    if-eqz v2, :select_all
    invoke-interface {v2}, Ljava/lang/CharSequence;->length()I
    move-result v2
    if-lez v2, :select_all
    const v2, 0x1020021  # android.R.id.copy
    invoke-interface {v0, v2}, Landroid/view/inputmethod/InputConnection;->performContextMenuAction(I)Z
    move-result v3
    if-eqz v3, :fail
    const/4 v0, 0x1
    return v0

    :select_all
    const v2, 0x102001f  # android.R.id.selectAll
    invoke-interface {v0, v2}, Landroid/view/inputmethod/InputConnection;->performContextMenuAction(I)Z
    move-result v3
    if-eqz v3, :fail
    const/4 v0, 0x1
    return v0

    :fail
    const/4 v0, 0x0
    return v0
.end method
''')

# Session incognito action. Lowq.f() is the stock live InputSessionNotification incognito bit.
q=root/'smali/com/mekromn/meboard/IncognitoToggleActionRunnable.smali'; q.parent.mkdir(parents=True,exist_ok=True)
q.write_text(r'''.class public final Lcom/mekromn/meboard/IncognitoToggleActionRunnable;
.super Ljava/lang/Object;
.source "Meboard"
.implements Ljava/lang/Runnable;
.field private final context:Landroid/content/Context;
.method public constructor <init>(Landroid/content/Context;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/mekromn/meboard/IncognitoToggleActionRunnable;->context:Landroid/content/Context;
    return-void
.end method
.method public final run()V
    .locals 1
    iget-object v0, p0, Lcom/mekromn/meboard/IncognitoToggleActionRunnable;->context:Landroid/content/Context;
    invoke-static {v0}, Lcom/mekromn/meboard/IncognitoToggleAction;->toggle(Landroid/content/Context;)Z
    return-void
.end method
''')

q=root/'smali/com/mekromn/meboard/IncognitoToggleAction.smali'
q.write_text(r'''.class public final Lcom/mekromn/meboard/IncognitoToggleAction;
.super Ljava/lang/Object;
.source "Meboard"
.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method
.method public static toggle(Landroid/content/Context;)Z
    .locals 9
    move-object v0, p0
    :unwrap
    instance-of v1, v0, Landroid/inputmethodservice/InputMethodService;
    if-nez v1, :service
    instance-of v1, v0, Landroid/content/ContextWrapper;
    if-eqz v1, :fail
    move-object v1, v0
    check-cast v1, Landroid/content/ContextWrapper;
    invoke-virtual {v1}, Landroid/content/ContextWrapper;->getBaseContext()Landroid/content/Context;
    move-result-object v1
    if-eqz v1, :fail
    if-eq v1, v0, :fail
    move-object v0, v1
    goto :unwrap

    :service
    check-cast v0, Landroid/inputmethodservice/InputMethodService;
    invoke-virtual {v0}, Landroid/inputmethodservice/InputMethodService;->getCurrentInputEditorInfo()Landroid/view/inputmethod/EditorInfo;
    move-result-object v1
    if-eqz v1, :fail
    invoke-static {}, Lowq;->f()Z
    move-result v4
    xor-int/lit8 v4, v4, 0x1
    iget v2, v1, Landroid/view/inputmethod/EditorInfo;->imeOptions:I
    const/high16 v3, 0x1000000
    if-eqz v4, :disable
    or-int/2addr v2, v3
    goto :write
    :disable
    not-int v3, v3
    and-int/2addr v2, v3
    :write
    iput v2, v1, Landroid/view/inputmethod/EditorInfo;->imeOptions:I

    # Publish through Gboard's stock InputSessionNotification path so live consumers see the toggle.
    invoke-static {}, Lpyo;->b()Lpyo;
    move-result-object v2
    const-class v3, Lowq;
    invoke-virtual {v2, v3}, Lpyo;->a(Ljava/lang/Class;)Lpyk;
    move-result-object v2
    check-cast v2, Lowq;
    const/4 v5, 0x0
    const/4 v6, 0x0
    move-object v7, v1
    move-object v8, v1
    if-eqz v2, :publish
    iget-boolean v5, v2, Lowq;->d:Z
    iget-boolean v6, v2, Lowq;->g:Z
    iget-object v3, v2, Lowq;->b:Landroid/view/inputmethod/EditorInfo;
    if-eqz v3, :keep_b
    move-object v7, v3
    :keep_b
    iget-object v3, v2, Lowq;->c:Landroid/view/inputmethod/EditorInfo;
    if-eqz v3, :keep_c
    move-object v8, v3
    :keep_c
    :publish
    # Keep both stored EditorInfo copies consistent with the active session flag.
    if-eqz v7, :skip_v7
    iget v2, v7, Landroid/view/inputmethod/EditorInfo;->imeOptions:I
    const/high16 v3, 0x1000000
    if-eqz v4, :v7_clear
    or-int/2addr v2, v3
    goto :v7_write
    :v7_clear
    not-int v3, v3
    and-int/2addr v2, v3
    :v7_write
    iput v2, v7, Landroid/view/inputmethod/EditorInfo;->imeOptions:I
    :skip_v7
    if-eqz v8, :skip_v8
    iget v2, v8, Landroid/view/inputmethod/EditorInfo;->imeOptions:I
    const/high16 v3, 0x1000000
    if-eqz v4, :v8_clear
    or-int/2addr v2, v3
    goto :v8_write
    :v8_clear
    not-int v3, v3
    and-int/2addr v2, v3
    :v8_write
    iput v2, v8, Landroid/view/inputmethod/EditorInfo;->imeOptions:I
    :skip_v8
    invoke-static {v7, v8, v5, v4, v6}, Lowq;->e(Landroid/view/inputmethod/EditorInfo;Landroid/view/inputmethod/EditorInfo;ZZZ)V

    if-eqz v4, :toast_off
    const-string v2, "Incognito mode on"
    goto :toast
    :toast_off
    const-string v2, "Incognito mode off"
    :toast
    const/4 v3, 0x0
    invoke-static {p0, v2, v3}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v2
    invoke-virtual {v2}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x1
    return v0
    :fail
    const-string v0, "Incognito toggle unavailable"
    const/4 v1, 0x0
    invoke-static {p0, v0, v1}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x0
    return v0
.end method
''')

# Visual-only fallback for the two proven blank keys. It never changes key actions.
q=root/'smali/com/mekromn/meboard/BlankKeyIconFix.smali'
q.write_text(r'''.class public final Lcom/mekromn/meboard/BlankKeyIconFix;
.super Ljava/lang/Object;
.source "Meboard"
.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method
.method public static apply(Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;)V
    .locals 7
    const v0, 0x7f0b03e3
    invoke-virtual {p0, v0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->findViewById(I)Landroid/view/View;
    move-result-object v0
    instance-of v1, v0, Landroid/widget/ImageView;
    if-eqz v1, :done
    check-cast v0, Landroid/widget/ImageView;
    invoke-virtual {v0}, Landroid/widget/ImageView;->getDrawable()Landroid/graphics/drawable/Drawable;
    move-result-object v1
    if-nez v1, :done
    invoke-virtual {p0}, Lcom/google/android/libraries/inputmethod/widgets/SoftKeyView;->getContentDescription()Ljava/lang/CharSequence;
    move-result-object v1
    if-eqz v1, :done
    invoke-interface {v1}, Ljava/lang/CharSequence;->toString()Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v1}, Ljava/lang/String;->toLowerCase()Ljava/lang/String;
    move-result-object v1
    const/4 v2, -0x1
    const-string v3, "shift"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-nez v3, :shift
    const-string v3, "caps"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-nez v3, :shift
    const-string v3, "emoji"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-eqz v3, :done
    const/4 v2, 0x1
    goto :set
    :shift
    const/4 v2, 0x0
    :set
    new-instance v3, Lcom/mekromn/meboard/BlankKeyIconDrawable;
    invoke-direct {v3, v2}, Lcom/mekromn/meboard/BlankKeyIconDrawable;-><init>(I)V
    invoke-virtual {v0, v3}, Landroid/widget/ImageView;->setImageDrawable(Landroid/graphics/drawable/Drawable;)V
    const/4 v4, 0x0
    invoke-virtual {v0, v4}, Landroid/widget/ImageView;->setVisibility(I)V
    :done
    return-void
.end method
''')

q=root/'smali/com/mekromn/meboard/BlankKeyIconDrawable.smali'
q.write_text(r'''.class public final Lcom/mekromn/meboard/BlankKeyIconDrawable;
.super Landroid/graphics/drawable/Drawable;
.source "Meboard"
.field private final paint:Landroid/graphics/Paint;
.field private final mode:I
.method public constructor <init>(I)V
    .locals 3
    invoke-direct {p0}, Landroid/graphics/drawable/Drawable;-><init>()V
    iput p1, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->mode:I
    new-instance v0, Landroid/graphics/Paint;
    const/4 v1, 0x1
    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V
    const/4 v1, -0x1
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V
    sget-object v1, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V
    sget-object v1, Landroid/graphics/Paint$StrokeCap;->ROUND:Landroid/graphics/Paint$StrokeCap;
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$StrokeCap;)V
    sget-object v1, Landroid/graphics/Paint$StrokeJoin;->ROUND:Landroid/graphics/Paint$StrokeJoin;
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$StrokeJoin;)V
    iput-object v0, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->paint:Landroid/graphics/Paint;
    return-void
.end method
.method public draw(Landroid/graphics/Canvas;)V
    .locals 15
    invoke-virtual {p0}, Landroid/graphics/drawable/Drawable;->getBounds()Landroid/graphics/Rect;
    move-result-object v0
    invoke-virtual {v0}, Landroid/graphics/Rect;->width()I
    move-result v1
    invoke-virtual {v0}, Landroid/graphics/Rect;->height()I
    move-result v2
    invoke-static {v1, v2}, Ljava/lang/Math;->min(II)I
    move-result v3
    int-to-float v3, v3
    const v4, 0x3dcccccd
    mul-float v4, v4, v3
    iget-object v5, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->paint:Landroid/graphics/Paint;
    invoke-virtual {v5, v4}, Landroid/graphics/Paint;->setStrokeWidth(F)V
    invoke-virtual {v0}, Landroid/graphics/Rect;->centerX()I
    move-result v6
    invoke-virtual {v0}, Landroid/graphics/Rect;->centerY()I
    move-result v7
    int-to-float v6, v6
    int-to-float v7, v7
    iget v8, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->mode:I
    if-nez v8, :emoji

    # Shift: outlined up-arrow/house shape.
    new-instance v8, Landroid/graphics/Path;
    invoke-direct {v8}, Landroid/graphics/Path;-><init>()V
    const v9, 0x3ecccccd
    mul-float v9, v9, v3
    const v10, 0x3e4ccccd
    mul-float v10, v10, v3
    sub-float v11, v6, v9
    invoke-virtual {v8, v11, v7}, Landroid/graphics/Path;->moveTo(FF)V
    sub-float v11, v7, v9
    invoke-virtual {v8, v6, v11}, Landroid/graphics/Path;->lineTo(FF)V
    add-float v11, v6, v9
    invoke-virtual {v8, v11, v7}, Landroid/graphics/Path;->lineTo(FF)V
    add-float v11, v7, v10
    add-float v12, v6, v10
    invoke-virtual {v8, v12, v11}, Landroid/graphics/Path;->lineTo(FF)V
    add-float v11, v7, v9
    invoke-virtual {v8, v12, v11}, Landroid/graphics/Path;->lineTo(FF)V
    sub-float v12, v6, v10
    invoke-virtual {v8, v12, v11}, Landroid/graphics/Path;->lineTo(FF)V
    add-float v11, v7, v10
    invoke-virtual {v8, v12, v11}, Landroid/graphics/Path;->lineTo(FF)V
    invoke-virtual {v8}, Landroid/graphics/Path;->close()V
    invoke-virtual {p1, v8, v5}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V
    return-void

    :emoji
    const v8, 0x3ecccccd
    mul-float v8, v8, v3
    invoke-virtual {p1, v6, v7, v8, v5}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V
    const v9, 0x3e19999a
    mul-float v9, v9, v3
    const v10, 0x3d4ccccd
    mul-float v10, v10, v3
    sub-float v11, v6, v9
    sub-float v12, v7, v9
    invoke-virtual {p1, v11, v12, v10, v5}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V
    add-float v11, v6, v9
    invoke-virtual {p1, v11, v12, v10, v5}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V
    new-instance v11, Landroid/graphics/RectF;
    const v12, 0x3e4ccccd
    mul-float v12, v12, v3
    sub-float v13, v6, v12
    const v14, 0x3dcccccd
    mul-float v14, v14, v3
    sub-float v14, v7, v14
    add-float v6, v6, v12
    add-float v7, v7, v12
    invoke-direct {v11, v13, v14, v6, v7}, Landroid/graphics/RectF;-><init>(FFFF)V
    const/4 v6, 0x0
    const/high16 v7, 0x43340000
    const/4 v8, 0x0
    invoke-virtual {p1, v11, v6, v7, v8, v5}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V
    return-void
.end method
.method public setAlpha(I)V
    .locals 1
    iget-object v0, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->paint:Landroid/graphics/Paint;
    invoke-virtual {v0, p1}, Landroid/graphics/Paint;->setAlpha(I)V
    invoke-virtual {p0}, Landroid/graphics/drawable/Drawable;->invalidateSelf()V
    return-void
.end method
.method public setColorFilter(Landroid/graphics/ColorFilter;)V
    .locals 1
    iget-object v0, p0, Lcom/mekromn/meboard/BlankKeyIconDrawable;->paint:Landroid/graphics/Paint;
    invoke-virtual {v0, p1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;
    invoke-virtual {p0}, Landroid/graphics/drawable/Drawable;->invalidateSelf()V
    return-void
.end method
.method public getOpacity()I
    .locals 1
    const/4 v0, -0x3
    return v0
.end method
.method public getIntrinsicWidth()I
    .locals 1
    const/16 v0, 0x30
    return v0
.end method
.method public getIntrinsicHeight()I
    .locals 1
    const/16 v0, 0x30
    return v0
.end method
''')
print('stage54c source patched')
