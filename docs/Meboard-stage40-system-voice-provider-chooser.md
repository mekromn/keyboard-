# Meboard Stage 40 — Android system voice-provider chooser

Stage 40 keeps the proven Stage-39/Stage-35 distinct microphone long-press path and changes only provider selection/result handling.

## Why Stage 39 showed the wrong chooser
The old custom popup enumerated `android.speech.RecognitionService`. FUTO Voice Input does not implement the standard SpeechRecognizer service API. It does expose an exported activity for `android.speech.action.RECOGNIZE_SPEECH` and returns recognized text in `RecognizerIntent.EXTRA_RESULTS`.

## Stage 40 design
- Short microphone tap remains stock Meboard/Gboard voice typing.
- Long press keeps the Stage-39 custom LONG_PRESS ActionDef.
- The active chooser path starts a small non-exported translucent `VoiceProviderRelayActivity`.
- The relay calls `Intent.createChooser()` around implicit `android.speech.action.RECOGNIZE_SPEECH`, forcing Android's system app/provider chooser on every long press.
- The selected provider's activity result is returned to the relay.
- The relay commits the first `android.speech.extra.RESULTS` string to the input connection captured at long-press time, then closes.
- Canceling the chooser/provider commits nothing.

## Package delta versus Stage 39
Only `classes.dex` and `AndroidManifest.xml` change. `resources.arsc`, DEX 2–4, assets, and native libraries remain byte-identical.

Output APK SHA-256: `1ce6bd3e5a0f136830c052ae257b3e80cf505642f0d8f68a08da3707de2cca16`
Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

The private signing key is not stored in this repository.
