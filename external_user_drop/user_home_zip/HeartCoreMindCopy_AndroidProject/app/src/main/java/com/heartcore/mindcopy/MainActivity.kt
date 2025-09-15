package com.heartcore.mindcopy

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity

class MainActivity : ComponentActivity() {
  private lateinit var webView: WebView
  @SuppressLint("SetJavaScriptEnabled")
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)
    webView = findViewById(R.id.webview)
    val ws: WebSettings = webView.settings
    ws.javaScriptEnabled = true
    ws.domStorageEnabled = true
    ws.allowFileAccessFromFileURLs = true
    ws.allowUniversalAccessFromFileURLs = true
    webView.webViewClient = object: WebViewClient(){}
    webView.loadUrl("file:///android_asset/www/index.html")
  }
  override fun onBackPressed() {
    if (this::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
  }
}
