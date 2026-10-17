package in.kpmaster.mobile;
import android.content.Context;
import android.content.SharedPreferences;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.*;
/** Native, persistent per-operation counters. Chart backups never contain these counters. */
final class DemoManager {
 private final SharedPreferences prefs; private final String systemId;
 DemoManager(Context context,String id){prefs=context.getSharedPreferences("demo-usage",0);systemId=id;}
 private JSONObject read()throws Exception{String text=prefs.getString("demo-state","");JSONObject d=text.isEmpty()?new JSONObject().put("systemId",systemId).put("kundali",new JSONArray()).put("matchmaking",new JSONArray()):new JSONObject(text);if(!systemId.equals(d.getString("systemId")))throw new Exception("Demo usage identity mismatch.");for(String k:new String[]{"kundali","matchmaking"}){JSONArray a=d.getJSONArray(k);if(a.length()>limit(k))throw new Exception("Invalid demo usage data.");java.util.HashSet<String> seen=new java.util.HashSet<>();for(int i=0;i<a.length();i++){String v=a.getString(i);if(!v.matches("[a-f0-9]{64}")||!seen.add(v))throw new Exception("Invalid demo usage data.");}}return d;}
 private int limit(String kind)throws Exception{if("kundali".equals(kind))return 15;if("matchmaking".equals(kind))return 10;throw new Exception("Invalid demo calculation type.");}
 synchronized JSONObject status()throws Exception{JSONObject d=read(),used=new JSONObject(),left=new JSONObject(),limits=new JSONObject();for(String k:new String[]{"kundali","matchmaking"}){int n=d.getJSONArray(k).length();used.put(k,n);left.put(k,limit(k)-n);limits.put(k,limit(k));}return new JSONObject().put("demo",true).put("limits",limits).put("used",used).put("remaining",left);}
 synchronized JSONObject use(String kind,String signature,boolean consume)throws Exception{int max=limit(kind);if(signature==null||signature.length()<3||signature.length()>16384)throw new Exception("Invalid demo request.");JSONObject d=read();JSONArray a=d.getJSONArray(kind);byte[] bytes=MessageDigest.getInstance("SHA-256").digest(signature.getBytes(StandardCharsets.UTF_8));StringBuilder h=new StringBuilder();for(byte b:bytes)h.append(String.format(java.util.Locale.ROOT,"%02x",b&255));String id=h.toString();for(int i=0;i<a.length();i++)if(id.equals(a.getString(i)))return status().put("allowed",true).put("known",true);if(!consume||a.length()>=max)return status().put("allowed",false);a.put(id);if(!prefs.edit().putString("demo-state",d.toString()).commit())throw new Exception("Could not save demo usage. Calculation cancelled.");return status().put("allowed",true).put("known",false);}
}
