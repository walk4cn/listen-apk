package com.kidlisten.app;

import android.app.Activity;
import android.content.res.AssetFileDescriptor;
import android.content.res.Configuration;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

import androidx.webkit.WebViewAssetLoader;

/**
 * 英语课文点读台：本地 WebView 壳。
 * 页面与音频全部打包在 assets 下，通过 WebViewAssetLoader 以 https 域提供，
 * 这样 localStorage（已听记录 / 连播设置）可正常工作，且不依赖任何网络。
 * 方向：平板（sw>=600dp）横屏，手机竖屏，运行时按屏幕判断。
 */
public class MainActivity extends Activity {

    private static final String DOMAIN = "appassets.androidplatform.net";
    private static final String HOME = "https://" + DOMAIN + "/assets/index.html";

    private WebView web;
    private long lastBackAt = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 手机竖屏、平板横屏
        boolean tablet = getResources().getConfiguration().smallestScreenWidthDp >= 600;
        setRequestedOrientation(tablet
                ? android.content.pm.ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
                : android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);

        WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .setDomain(DOMAIN)
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(false);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setAllowFileAccess(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);

        // 不做沉浸式：内容排在状态栏/导航栏之间，避免状态栏遮挡页面顶栏
        // （状态栏与导航栏颜色由主题设为页面同款粉色，视觉连续）

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                android.net.Uri url = request.getUrl();
                String path = url.getPath();
                // mp3 走自带 Range 支持的分发器：WebViewAssetLoader 不支持 Range 请求，
                // 会导致 Chromium 把音频标记为"不可定位"，拖进度条松手直接回到开头
                if (DOMAIN.equals(url.getHost()) && path != null && path.endsWith(".mp3")) {
                    WebResourceResponse r = serveAudio(path.substring("/assets/".length()),
                            request.getRequestHeaders() == null ? null : request.getRequestHeaders().get("Range"));
                    if (r != null) return r;
                }
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // 只允许在本应用内加载，外链一律忽略
                return !DOMAIN.equals(request.getUrl().getHost());
            }
        });

        web.loadUrl(HOME);
        setContentView(web);
    }

    /**
     * 支持 HTTP Range 的 assets 音频分发：
     * 有 Range 头时返回 206 + Content-Range + 跳过起始字节的流，Chromium 才会认为媒体可 seek。
     */
    private WebResourceResponse serveAudio(String assetName, String rangeHeader) {
        InputStream in = null;
        try {
            AssetFileDescriptor afd = getAssets().openFd(assetName);
            long total = afd.getLength();
            afd.close();
            if (total <= 0) return null;

            long start = 0;
            if (rangeHeader != null && rangeHeader.startsWith("bytes=")) {
                String p = rangeHeader.substring(6);
                int dash = p.indexOf('-');
                try { start = Long.parseLong(p.substring(0, dash)); } catch (Exception e) { start = 0; }
                if (start < 0 || start >= total) start = 0;
            }

            in = getAssets().open(assetName);
            long skip = start;
            while (skip > 0) {
                long n = in.skip(skip);
                if (n <= 0) break;
                skip -= n;
            }

            Map<String, String> h = new HashMap<String, String>();
            h.put("Accept-Ranges", "bytes");
            h.put("Content-Type", "audio/mpeg");
            if (start > 0) {
                h.put("Content-Range", "bytes " + start + "-" + (total - 1) + "/" + total);
                h.put("Content-Length", String.valueOf(total - start));
                return new WebResourceResponse("audio/mpeg", null, 206, "Partial Content", h, in);
            }
            h.put("Content-Length", String.valueOf(total));
            return new WebResourceResponse("audio/mpeg", null, 200, "OK", h, in);
        } catch (IOException e) {
            if (in != null) { try { in.close(); } catch (IOException ignore) {} }
            return null;
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
            return;
        }
        long now = System.currentTimeMillis();
        if (now - lastBackAt > 2000) {
            lastBackAt = now;
            Toast.makeText(this, "再按一次退出", Toast.LENGTH_SHORT).show();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onPause() {
        if (web != null) {
            web.onPause();
        }
        super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) {
            web.onResume();
        }
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
