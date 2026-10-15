package in.kpmaster.mobile;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import org.bouncycastle.math.ec.rfc8032.Ed25519;

/** Existing Windows signed licence/control protocol, with a native mobile identity. */
final class LicenseManager {
 private final Context context; private final String systemId; private final SharedPreferences prefs; private final JSONArray keys;
 LicenseManager(Context c,String id)throws Exception{context=c;systemId=id;prefs=c.getSharedPreferences("activation",0);keys=new JSONArray(readKeys(c));}
 private static String readKeys(Context c)throws Exception{try(java.io.InputStream in=c.getAssets().open("owner-public-keys.json");java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){byte[] bytes=new byte[1024];int n;while((n=in.read(bytes))!=-1)out.write(bytes,0,n);return out.toString("UTF-8");}}
 static String codeEnvelope(String text,boolean status)throws Exception{
  if(text==null||text.length()>16384)throw new Exception("Paste the complete owner key.");
  String[] parts=text.replaceAll("\\s", "").split("\\.",-1);
  if(parts.length!=3||!(status?"KP-S1":"KP-A1").equals(parts[0])||!parts[1].matches("[A-Za-z0-9_-]{1,12000}")||!parts[2].matches("[A-Za-z0-9_-]{86}"))throw new Exception("Paste a complete "+(status?"status key (KP-S1…)":"activation key (KP-A1…)"));
  return new JSONObject().put("payload",parts[1]).put("signature",parts[2]).toString();
 }
 static final class Signed {JSONObject claims;String key;Signed(JSONObject c,String k){claims=c;key=k;}}
 private Signed signed(String text)throws Exception{
  if(text==null||text.length()>16384)throw new Exception("Choose a valid KP licence/status file.");
  JSONObject outer=new JSONObject(text);String p=outer.getString("payload"),s=outer.getString("signature");
  if(p.length()>12000||!p.matches("[A-Za-z0-9_-]+")||!s.matches("[A-Za-z0-9_-]+"))throw new Exception("Invalid signed file.");
  byte[] payload=Base64.decode(p,Base64.URL_SAFE|Base64.NO_WRAP),sig=Base64.decode(s,Base64.URL_SAFE|Base64.NO_WRAP);
  if(sig.length!=64)throw new Exception("Invalid owner signature.");
  for(int i=0;i<keys.length();i++){
   JSONObject key=keys.getJSONObject(i);byte[] der=Base64.decode(key.getString("der"),Base64.DEFAULT);
   if(der.length!=44)continue;byte[] raw=java.util.Arrays.copyOfRange(der,12,44);
   if(Ed25519.verify(sig,0,raw,0,payload,0,payload.length))return new Signed(new JSONObject(new String(payload,StandardCharsets.UTF_8)),key.getString("id"));
  }
  throw new Exception("This file was not issued by your software owner, or has been changed.");
 }
 private long time(String iso)throws Exception{try{return Instant.parse(iso).toEpochMilli();}catch(Exception e){throw new Exception("Invalid licence date/time.");}}
 private void common(JSONObject c)throws Exception{
  if(!"kp-master-offline".equals(c.optString("product"))||c.optInt("version")!=1)throw new Exception("This licence belongs to another product.");
  if(!systemId.equals(c.optString("systemId")))throw new Exception("This licence belongs to another device. Send this mobile System ID to the owner.");
  long issued=time(c.getString("issuedAt"));if(issued>System.currentTimeMillis()+300000)throw new Exception("Check your phone date and time.");
 }
 Signed licence(String text)throws Exception{
  Signed s=signed(text);JSONObject c=s.claims;common(c);
  if(c.optString("licenseId").isEmpty()||c.optString("clientName").isEmpty()||!c.has("expiresAt"))throw new Exception("Invalid licence claims.");
  if(!c.isNull("expiresAt")){long expiry=time(c.getString("expiresAt"));if(expiry<time(c.getString("issuedAt")))throw new Exception("Invalid licence expiry.");if(System.currentTimeMillis()>expiry)throw new Exception("Licence expired. Contact the owner.");}
  return s;
 }
 JSONObject active()throws Exception{
  long now=System.currentTimeMillis(),seen=prefs.getLong("lastSeen",0);if(now+300000<seen)throw new Exception("Check the phone date and time before using the app.");
  Signed license=licence(prefs.getString("license",""));JSONObject controls=new JSONObject(prefs.getString("controls","{}"));String id=license.claims.getString("licenseId");
  if(controls.has(id)){
   Signed status=signed(controls.getString(id));common(status.claims);if(!license.key.equals(status.key)||!"license-status".equals(status.claims.optString("kind"))||!id.equals(status.claims.optString("licenseId")))throw new Exception("Invalid licence status.");
   if(!"activate".equals(status.claims.optString("action")))throw new Exception("This licence has been deactivated by the owner.");
  }
  prefs.edit().putLong("lastSeen",Math.max(now,seen)).apply();return license.claims;
 }
 void importLicence(String text)throws Exception{
  Signed checked=licence(text); // Never replace a valid saved licence with an invalid import.
  prefs.edit().putString("license",text).commit();
 }
 void importControl(String text)throws Exception{
  Signed s=signed(text);JSONObject c=s.claims;common(c);
  if(!"license-status".equals(c.optString("kind"))||!c.optString("licenseId").matches("[a-fA-F0-9-]{36}")||!c.optString("commandId").matches("[a-fA-F0-9-]{36}")||c.optLong("revision")<1||(!"activate".equals(c.optString("action"))&&!"deactivate".equals(c.optString("action"))))throw new Exception("Invalid owner status file.");
  Signed license=licence(prefs.getString("license",""));if(!s.key.equals(license.key)||!c.getString("licenseId").equals(license.claims.getString("licenseId")))throw new Exception("This status file does not match the installed licence.");
  JSONObject controls=new JSONObject(prefs.getString("controls","{}"));String id=c.getString("licenseId");
  if(controls.has(id)){JSONObject old=signed(controls.getString(id)).claims;long revision=c.getLong("revision"),previous=old.getLong("revision");if(revision<previous||(revision==previous&&!c.getString("commandId").equals(old.getString("commandId"))))throw new Exception("This status file is older than the last imported status.");}
  controls.put(id,text);prefs.edit().putString("controls",controls.toString()).commit();
 }
 String request()throws Exception{StringBuilder ids=new StringBuilder();for(int i=0;i<keys.length();i++){if(i>0)ids.append(", ");ids.append(keys.getJSONObject(i).getString("id"));}return "KP MASTER Android customer\nSystem ID: "+systemId+"\nAccepted owner Key IDs: "+ids+"\nVersion: "+BuildConfig.VERSION+"\n";}
}
