# Android prototype

This is an offline, dependency-light Android implementation of the n-gram memory baseline. It has **no neural inference** and is not a validated assistant. There is no `INTERNET` permission. The user can enter text, generate a deterministic continuation, import a selected text document (up to 1 MiB), inspect memory size, and delete all learned memory.

## Reference target

- Functional reference: Pixel 8 Android Virtual Device, Android 15 / API 35.
- Physical performance target: Pixel 8 running Android 15 / API 35. The physical-device measurements are pending.
- Minimum supported Android version: API 28.

An emulator checks behavior and build compatibility; its latency and energy figures must not be presented as physical-device measurements.

## Build and run

Install JDK 17, Android SDK Platform 35, Build Tools 35.0.0, and Gradle 8.13, or import this directory into Android Studio. Then run from this directory:

```bash
gradle --no-daemon assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

The app stores its database in private app storage. Android backup is disabled. Clearing memory deletes its n-gram and import records; uninstalling the app also removes its app-private data. A file is read only after a user selects it through Android's document picker. The app does not retain access to the selected URI after import.

## Measurement protocol

On the named device, record OS build, app commit, battery level, power mode, thermal state, and whether the device is charging. Use a fixed corpus and the same tokenizer/settings across runs. After five warmups, time at least 30 continuations for each prompt length and report median, p95, and peak RAM. Measure training/import separately. For energy, use a physical device and a documented measurement tool; the emulator cannot establish energy cost. Do not call this benchmark complete until the measurements and raw logs are published.

The Java tokenizer and Python tokenizer are close but not byte-for-byte identical for every Unicode combining-mark sequence. Cross-runtime parity tests and database migration are future work.
