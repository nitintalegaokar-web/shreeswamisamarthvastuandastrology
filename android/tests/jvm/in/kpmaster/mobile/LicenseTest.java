package in.kpmaster.mobile;import org.json.*;import java.nio.file.*;import android.content.Context;
public class LicenseTest{
 static int assertions=0;static String read(Path d,String f)throws Exception{return new String(Files.readAllBytes(d.resolve(f)),java.nio.charset.StandardCharsets.UTF_8);}
 static void rejects(RunnableChecked action)throws Exception{try{action.run();throw new AssertionError("Accepted invalid licence/status");}catch(AssertionError e){throw e;}catch(Exception expected){assertions++;}}
 interface RunnableChecked{void run()throws Exception;}
 public static void main(String[] a)throws Exception{
  Path d=Paths.get(a[0]);String id=read(d,"id.txt").trim();LicenseManager m=new LicenseManager(new Context(d.toString()),id);
  rejects(()->m.active());m.importLicence(read(d,"valid.json"));if(!m.active().getString("systemId").equals(id))throw new AssertionError();assertions++;
  rejects(()->m.importLicence(read(d,"tampered.json")));rejects(()->m.importLicence(read(d,"wrong-device.json")));rejects(()->m.importLicence(read(d,"expired.json")));rejects(()->m.importLicence(read(d,"foreign-key.json")));m.active();assertions++;
  m.importControl(read(d,"deactivate.json"));rejects(()->m.active());m.importControl(read(d,"activate.json"));m.active();assertions++;
  rejects(()->m.importControl(read(d,"deactivate.json")));rejects(()->m.importControl(read(d,"wrong-control.json")));rejects(()->m.importControl(read(d,"altered-control.json")));m.active();assertions++;
  JSONObject valid=new JSONObject(read(d,"valid.json"));String code="KP-A1."+valid.getString("payload")+"."+valid.getString("signature");m.importLicence(LicenseManager.codeEnvelope(code,false));m.active();assertions++;
  rejects(()->LicenseManager.codeEnvelope(code,true));rejects(()->LicenseManager.codeEnvelope("bad",false));
  JSONObject off=new JSONObject(read(d,"deactivate.json"));String offCode="KP-S1."+off.getString("payload")+"."+off.getString("signature");LicenseManager fresh=new LicenseManager(new Context(d.toString()),id);fresh.importLicence(LicenseManager.codeEnvelope(code,false));fresh.importControl(LicenseManager.codeEnvelope(offCode,true));rejects(()->fresh.active());
  JSONObject request=new JSONObject(read(d,"owner-request.json"));if(!m.request().contains(request.getString("systemId")))throw new AssertionError();assertions++;
  m.importLicence(read(d,"feature-plan.json"));if(!m.active().getJSONArray("features").getString(0).equals("vedic"))throw new AssertionError();assertions++;rejects(()->m.importLicence(read(d,"invalid-feature.json")));
  m.importLicence(read(d,"limited.json"));if(!m.active().getString("expiresAt").endsWith("T23:59:59.999Z"))throw new AssertionError("Dated licence lost its expiry");assertions++;
  rejects(()->m.importLicence(read(d,"future-issued.json")));rejects(()->m.importLicence(read(d,"invalid-expiry.json")));m.active();assertions++;
  Context stored=new Context(d.toString());stored.getSharedPreferences("activation",0).edit().putString("license",read(d,"expired.json")).commit();LicenseManager expiredSaved=new LicenseManager(stored,id);rejects(()->expiredSaved.active());
  stored.getSharedPreferences("activation",0).edit().putString("license",read(d,"valid.json")).putLong("lastSeen",System.currentTimeMillis()+86400000).commit();rejects(()->expiredSaved.active());
  System.out.println("Android signed-licence/control compatibility: PASS ("+assertions+" assertions)");
 }
}
