package com.swamisamarth.kpmaster.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.print.PageRange;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.util.Base64;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.JsPromptResult;
import android.webkit.JsResult;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    private static final String HOST = "app.kpmaster.local";
    private static final String HOME = "https://" + HOST + "/index.html";
    private static final int OPEN_FILE = 10, SAVE_FILE = 11;
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private byte[] exportBytes;
    private volatile boolean exportBusy;
    private boolean printBusy;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(24,47,61));
        getWindow().setNavigationBarColor(Color.rgb(24,47,61));
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(24,47,61));
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((view, windowInsets) -> {
                Insets bars = windowInsets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                Insets keyboard = windowInsets.getInsets(WindowInsets.Type.ime());
                view.setPadding(bars.left, bars.top, bars.right, Math.max(bars.bottom, keyboard.bottom));
                return windowInsets;
            });
        } else root.setFitsSystemWindows(true);
        if ((getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0) WebView.setWebContentsDebuggingEnabled(true);
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(245,243,238));
        root.addView(web, new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true); // User-selected JSON imports via document picker.
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        if (Build.VERSION.SDK_INT >= 33) settings.setAlgorithmicDarkeningAllowed(false);
        else if (Build.VERSION.SDK_INT >= 29) settings.setForceDark(WebSettings.FORCE_DARK_OFF);
        settings.setSafeBrowsingEnabled(true);
        web.addJavascriptInterface(new MobileBridge(), "KPMobile");
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && "/index.html".equals(uri.getPath())) {
                    try {
                        HashMap<String,String> headers = new HashMap<>();
                        headers.put("Cache-Control", "no-store");
                        headers.put("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'");
                        return new WebResourceResponse("text/html", "UTF-8", 200, "OK", headers, getAssets().open("index.html"));
                    } catch (IOException ignored) { }
                }
                return new WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (HOME.equals(request.getUrl().toString())) return false;
                if ("whatsapp".equals(request.getUrl().getScheme())) openWhatsApp(request.getUrl().toString());
                return true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/json", "text/plain", "application/octet-stream"});
                try { startActivityForResult(intent, OPEN_FILE); }
                catch (ActivityNotFoundException exception) { fileCallback.onReceiveValue(null); fileCallback = null; status("No file picker is installed."); }
                return true;
            }
            @Override public boolean onJsAlert(WebView view, String url, String message, JsResult result) {
                new AlertDialog.Builder(MainActivity.this).setTitle("KP Master").setMessage(message).setPositiveButton("OK", (d,w)->result.confirm()).setOnCancelListener(d->result.cancel()).show(); return true;
            }
            @Override public boolean onJsConfirm(WebView view, String url, String message, JsResult result) {
                new AlertDialog.Builder(MainActivity.this).setTitle("KP Master").setMessage(message).setPositiveButton("Continue", (d,w)->result.confirm()).setNegativeButton("Cancel", (d,w)->result.cancel()).setOnCancelListener(d->result.cancel()).show(); return true;
            }
            @Override public boolean onJsPrompt(WebView view, String url, String message, String value, JsPromptResult result) {
                EditText input = new EditText(MainActivity.this); input.setText(value);
                new AlertDialog.Builder(MainActivity.this).setTitle("KP Master").setMessage(message).setView(input).setPositiveButton("Save", (d,w)->result.confirm(input.getText().toString())).setNegativeButton("Cancel", (d,w)->result.cancel()).setOnCancelListener(d->result.cancel()).show(); return true;
            }
        });
        android.content.pm.PackageInfo engine = WebView.getCurrentWebViewPackage();
        if (engine != null) {
            try {
                if (Integer.parseInt(engine.versionName.split("\\.")[0]) < 80) {
                    new AlertDialog.Builder(this).setTitle("Update Android System WebView").setMessage("Update Android System WebView or Google Chrome on this phone, then reopen KP Master. This is needed for the offline software to work correctly.").setPositiveButton("Close", (d,w)->finish()).setCancelable(false).show();
                    return;
                }
            } catch (NumberFormatException ignored) { }
        }
        web.loadUrl(HOME);
    }

    private void status(String message) {
        runOnUiThread(() -> { if (!isFinishing()) { Toast.makeText(this,message,Toast.LENGTH_LONG).show(); web.evaluateJavascript("window.kpNativeStatus && window.kpNativeStatus("+JSONObject.quote(message)+")", null); } });
    }
    private void openWhatsApp(String value) {
        Uri uri = Uri.parse(value);
        if (!uri.isHierarchical()) return;
        String phone = uri.getQueryParameter("phone"), text = uri.getQueryParameter("text");
        if (!"whatsapp".equals(uri.getScheme()) || !"send".equals(uri.getHost()) || (uri.getPath()!=null && !uri.getPath().isEmpty() && !"/".equals(uri.getPath())) || uri.getUserInfo()!=null || uri.getPort()!=-1 || uri.getFragment()!=null || text==null || text.isEmpty() || text.length()>100000 || (phone!=null && !phone.matches("[1-9][0-9]{6,14}"))) { status("Check the customer mobile number before sharing."); return; }
        for (String key : uri.getQueryParameterNames()) if ((!"text".equals(key) && !"phone".equals(key)) || uri.getQueryParameters(key).size()!=1) return;
        runOnUiThread(() -> {
            for (String pkg : new String[]{"com.whatsapp","com.whatsapp.w4b"}) {
                Intent intent = phone==null ? new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,text) : new Intent(Intent.ACTION_VIEW,uri);
                intent.setPackage(pkg);
                try { startActivity(intent); return; } catch (ActivityNotFoundException ignored) { }
            }
            new AlertDialog.Builder(this).setTitle("WhatsApp required").setMessage("Install WhatsApp or WhatsApp Business on this phone and sign in, then try sharing again.").setPositiveButton("OK",null).show();
        });
    }
    private void startPrint(String name, String paper, boolean landscape) {
        if (printBusy) return;
        printBusy = true;
        PrintDocumentAdapter delegate = web.createPrintDocumentAdapter("KP Master");
        PrintDocumentAdapter adapter = new PrintDocumentAdapter() {
            @Override public void onStart() { delegate.onStart(); }
            @Override public void onLayout(PrintAttributes oldAttrs, PrintAttributes newAttrs, CancellationSignal signal, LayoutResultCallback callback, Bundle extras) { delegate.onLayout(oldAttrs,newAttrs,signal,callback,extras); }
            @Override public void onWrite(PageRange[] pages, ParcelFileDescriptor destination, CancellationSignal signal, WriteResultCallback callback) { delegate.onWrite(pages,destination,signal,callback); }
            @Override public void onFinish() { delegate.onFinish(); printBusy=false; web.evaluateJavascript("dispatchEvent(new Event('afterprint'))",null); }
        };
        PrintAttributes.MediaSize size = "A4".equals(paper) ? PrintAttributes.MediaSize.ISO_A4 : PrintAttributes.MediaSize.ISO_A5;
        PrintAttributes attrs = new PrintAttributes.Builder().setMediaSize(landscape?size.asLandscape():size.asPortrait()).setMinMargins(PrintAttributes.Margins.NO_MARGINS).setColorMode(PrintAttributes.COLOR_MODE_COLOR).build();
        try { ((PrintManager)getSystemService(PRINT_SERVICE)).print("KP Master document",adapter,attrs); }
        catch (RuntimeException exception) { printBusy=false;web.evaluateJavascript("dispatchEvent(new Event('afterprint'))",null);status("Printing is unavailable. Enable Android Print Services in phone settings."); }
    }
    public final class MobileBridge {
        @JavascriptInterface public boolean isSystemDark() { return (getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK) == android.content.res.Configuration.UI_MODE_NIGHT_YES; }
        @JavascriptInterface public void shareWhatsApp(String url) { if(url!=null && url.length()<150000)openWhatsApp(url); }
        @JavascriptInterface public void copyText(String text) { if(text!=null && text.length()<100000)runOnUiThread(()->((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("KP Master",text))); }
        @JavascriptInterface public void printDocument(String name, String paper, boolean landscape) { runOnUiThread(()->startPrint(name,paper,landscape)); }
        @JavascriptInterface public synchronized void saveFile(String name, String mime, String data) {
            if (exportBusy) { status("Finish saving the current file first."); return; }
            if (data==null || data.length()>36*1024*1024) { status("File exceeds the 25 MB export limit."); return; }
            try { exportBytes=Base64.decode(data,Base64.DEFAULT); }
            catch(IllegalArgumentException exception) { status("Could not prepare this file."); return; }
            if(exportBytes.length>25*1024*1024) {exportBytes=null;status("File exceeds the 25 MB export limit.");return;}
            exportBusy=true;
            String sanitizedName=name==null?"KP-Master-backup.json":name.replaceAll("[^\\p{L}\\p{N} ._()-]","_");
            final String safeName=sanitizedName.substring(0,Math.min(sanitizedName.length(),120));
            final String safeMime=(mime!=null&&mime.matches("[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+"))?mime:"application/octet-stream";
            runOnUiThread(()->{try { startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(safeMime).putExtra(Intent.EXTRA_TITLE,safeName),SAVE_FILE); }
            catch(ActivityNotFoundException exception) { exportBytes=null;exportBusy=false;status("No file saver is installed."); }});
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==OPEN_FILE && fileCallback!=null) {fileCallback.onReceiveValue(result==RESULT_OK&&data!=null&&data.getData()!=null?new Uri[]{data.getData()}:null);fileCallback=null;}
        if(request==SAVE_FILE) {
            final byte[] bytes=exportBytes;exportBytes=null;
            if(result!=RESULT_OK||data==null||data.getData()==null||bytes==null){exportBusy=false;status("Save cancelled.");return;}
            final Uri uri=data.getData();
            new Thread(()->{try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new IOException();out.write(bytes);status("File saved. Keep a backup outside the app.");}catch(IOException exception){status("Could not save. Choose another folder or check free space.");}finally{exportBusy=false;}},"KP-file-export").start();
        }
    }
    @Override public void onConfigurationChanged(android.content.res.Configuration configuration) {
        super.onConfigurationChanged(configuration);
        web.evaluateJavascript("window.dispatchEvent(new Event('kp-system-theme'))", null);
    }
    @Override public void onBackPressed() {web.evaluateJavascript("typeof kpRequestBack==='function' ? kpRequestBack() : true",value->{if("true".equals(value))finish();});}
    @Override protected void onDestroy() {if(fileCallback!=null)fileCallback.onReceiveValue(null);web.removeJavascriptInterface("KPMobile");web.destroy();super.onDestroy();}
}
