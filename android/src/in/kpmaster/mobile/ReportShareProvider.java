package in.kpmaster.mobile;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.ParcelFileDescriptor;import android.provider.OpenableColumns;import java.io.*;import java.util.*;
/** Read-only, temporary URI grants for a generated report; no external-storage permission. */
public final class ReportShareProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 private File report(Uri uri)throws FileNotFoundException{try{List<String> parts=uri.getPathSegments();if(parts.size()!=2||!parts.get(0).matches("[0-9a-f-]{36}")||!parts.get(1).matches("[\\p{L}\\p{N}._ -]{1,100}\\.pdf"))throw new IOException();File base=new File(getContext().getCacheDir(),"shared-reports").getCanonicalFile(),file=new File(new File(base,parts.get(0)),parts.get(1)).getCanonicalFile();if(!file.getPath().startsWith(base.getPath()+File.separator)||!file.isFile())throw new IOException();return file;}catch(Exception e){throw new FileNotFoundException("Report is unavailable.");}}
 public String getType(Uri uri){return "application/pdf";}
 public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{if(!"r".equals(mode))throw new FileNotFoundException("Read-only report.");return ParcelFileDescriptor.open(report(uri),ParcelFileDescriptor.MODE_READ_ONLY);}
 public Cursor query(Uri uri,String[] projection,String selection,String[] args,String sort){try{File file=report(uri);String[] columns=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;MatrixCursor result=new MatrixCursor(columns);Object[] values=new Object[columns.length];for(int i=0;i<columns.length;i++)values[i]=OpenableColumns.DISPLAY_NAME.equals(columns[i])?file.getName():OpenableColumns.SIZE.equals(columns[i])?file.length():null;result.addRow(values);return result;}catch(FileNotFoundException e){return null;}}
 public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}public int update(Uri uri,ContentValues values,String where,String[] args){throw new UnsupportedOperationException();}public int delete(Uri uri,String where,String[] args){throw new UnsupportedOperationException();}
}
