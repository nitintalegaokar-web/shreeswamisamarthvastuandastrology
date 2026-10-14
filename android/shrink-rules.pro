-keep class in.kpmaster.mobile.** { *; }
-keepattributes *Annotation*
-keepclassmembers class * {
 @android.webkit.JavascriptInterface <methods>;
}
