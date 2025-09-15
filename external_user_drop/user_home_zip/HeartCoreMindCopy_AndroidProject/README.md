# HeartCore MindCopy — Android Project

Build steps:
1) Open in Android Studio (Giraffe+).
2) Let it sync Gradle (AGP 8.5+, Kotlin 1.9+).
3) Build → Build APK(s) → install on your device.
APK path: `app/build/outputs/apk/debug/app-debug.apk`.

Notes:
- Loads offline app from `file:///android_asset/www/index.html`.
- JS & DOM storage enabled; local assets bundled.
