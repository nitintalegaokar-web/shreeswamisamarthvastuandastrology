// Real OOXML workbook; all report data comes from saved bookings on this device.
async function bkExportExcel(){
 const button=bkEl('bkExcelExport');
 try{
  const rows=bkLoad();
  if(!rows.length){bkToast('No saved bookings to export. Save a booking first.');return}
  button.disabled=true;button.textContent='Preparing Excel…';
  const book=new ExcelJS.Workbook();
  book.creator='KP Master';book.created=new Date();book.modified=new Date();book.calcProperties.fullCalcOnLoad=true;
  const sheet=book.addWorksheet('Booking Report',{views:[{state:'frozen',ySplit:5}],pageSetup:{paperSize:11,orientation:'landscape',fitToPage:true,fitToWidth:1,fitToHeight:0,horizontalCentered:true,margins:{left:0.25,right:0.25,top:0.32,bottom:0.32,header:0.12,footer:0.12}},headerFooter:{oddFooter:'&L&8KP Master&C&8Page &P of &N'}});
  sheet.columns=[{width:26},{width:22},{width:17},{width:14},{width:7},{width:13},{width:13},{width:13}];
  sheet.mergeCells('A1:H1');sheet.getCell('A1').value=profile.printConsultancy?profile.consultancy:'Matrugaya Booking Report';sheet.getCell('A1').font={name:'Calibri',size:15,bold:true,color:{argb:'FF182937'}};sheet.getCell('A1').alignment={horizontal:'center',vertical:'middle',wrapText:true};sheet.getRow(1).height=30;
  const details=[profile.printAstrologer?profile.astrologer:'',profile.printAddress?profile.address:'',profile.printMobile?'Mobile: '+profile.mobile:''].filter(Boolean).join(' · ');
  sheet.mergeCells('A2:H2');sheet.getCell('A2').value=details;sheet.getCell('A2').alignment={horizontal:'center',vertical:'middle',wrapText:true};sheet.getCell('A2').font={name:'Calibri',size:10,color:{argb:'FF667780'}};sheet.getRow(2).height=details?Math.max(18,details.split(/\r?\n/).reduce((count,line)=>count+Math.max(1,Math.ceil(line.length/110)),0)*15):5;
  sheet.mergeCells('A3:H3');sheet.getCell('A3').value='Matrugaya Bookings / मातृगया बुकिंग · '+rows.length+' bookings · '+new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',dateStyle:'medium'}).format(new Date());sheet.getCell('A3').font={name:'Calibri',size:11,bold:true,color:{argb:'FF967033'}};sheet.getCell('A3').alignment={horizontal:'center',vertical:'middle'};sheet.getRow(3).height=23;sheet.getRow(4).height=6;
  const headings=['Booking ID','Customer / नाव','Mobile / मोबाईल','Departure / तारीख','Persons / व्यक्ती','Total / एकूण (₹)','Advance / जमा (₹)','Balance / शिल्लक (₹)'];
  const header=sheet.getRow(5);header.values=headings;header.height=30;
  header.eachCell(c=>{c.font={name:'Calibri',size:11,bold:true,color:{argb:'FFFFFFFF'}};c.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FF182937'}};c.alignment={vertical:'middle',wrapText:true};c.border={bottom:{style:'thin',color:{argb:'FFB38B48'}}}});
  const moneyFormat='"₹"#,##0.00;[Red]-"₹"#,##0.00';
  const numeric=v=>{const n=Number(v);if(!Number.isFinite(n))throw Error('A saved booking contains an invalid number.');return n};
  let persons=0,total=0,advance=0;
  rows.forEach((r,i)=>{
   const n=i+6,t=numeric(r.totalPackage),a=numeric(r.advance),count=numeric(r.persons);persons+=count;total+=t;advance+=a;
   let date=String(r.leavingDate||'');if(/^\d{4}-\d{2}-\d{2}$/.test(date)){const [y,m,d]=date.split('-').map(Number);date=new Date(Date.UTC(y,m-1,d))}
   // Strings remain strings, including IDs, phone numbers and names beginning '='.
   const row=sheet.getRow(n);row.values=[String(r.bookingId||''),String(r.fullName||''),String(r.contact||''),date,count,t,a,{formula:`F${n}-G${n}`,result:Math.round((t-a)*100)/100}];row.height=Math.max(32,Math.ceil(String(r.fullName||'').length/18)*14,Math.ceil(String(r.bookingId||'').length/24)*14);
   row.eachCell({includeEmpty:true},(cell,col)=>{cell.font={name:'Calibri',size:11,color:{argb:'FF253B49'}};cell.alignment={vertical:'middle',wrapText:true,horizontal:col>=5?'right':'left'};cell.border={bottom:{style:'hair',color:{argb:'FFDDE3E1'}}};if(i%2===1)cell.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FFF5F3EE'}};if(col>=6)cell.numFmt=moneyFormat});
   row.getCell(1).numFmt='@';row.getCell(3).numFmt='@';row.getCell(4).numFmt='dd mmm yyyy';
  });
  const last=rows.length+5,end=last+1,summary=sheet.getRow(end);summary.values=['TOTALS','','','', {formula:`SUM(E6:E${last})`,result:persons},{formula:`SUM(F6:F${last})`,result:Math.round(total*100)/100},{formula:`SUM(G6:G${last})`,result:Math.round(advance*100)/100},{formula:`SUM(H6:H${last})`,result:Math.round((total-advance)*100)/100}];sheet.mergeCells(`A${end}:D${end}`);summary.height=28;
  summary.eachCell({includeEmpty:true},(c,col)=>{c.font={name:'Calibri',size:11,bold:true,color:{argb:'FF182937'}};c.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FFF1E5CF'}};c.alignment={horizontal:col>=5?'right':'left',vertical:'middle'};c.border={top:{style:'thin',color:{argb:'FFB38B48'}}};if(col>=6)c.numFmt=moneyFormat});
  sheet.autoFilter={from:'A5',to:`H${last}`};sheet.pageSetup.printTitlesRow='1:5';sheet.pageSetup.printArea=`A1:H${end}`;
  const bytes=await book.xlsx.writeBuffer();const blob=new Blob([bytes],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Matrugaya-Bookings-'+new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata'}).format(new Date())+'.xlsx';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);bkToast('Excel report downloaded. Open it in Excel and choose Print; A5 landscape is already set.');
 }catch(error){bkToast('Could not export Excel. Check the saved booking data and try again.');console.error('Excel report failed:',error)}
 finally{button.textContent='Export Excel / एक्सेल';button.disabled=bkLoad().length===0}
}
