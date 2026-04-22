from PyQt5.QtCore import QObject
import pymysql
from pymysql.constants import CLIENT
from PyQt5.QtCore import pyqtSignal
import uuid

from datetime import date, datetime
import base64
import time

from Setting_helper import load_his_settings


class His2(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super(His2, self).__init__()
        self.conn = None
        self.his_is_connect = False
        self.config_his = self._load_his_settings()
        print('His Connect', self.config_his)
        self.vendor = self.config_his['his']
        try:
            self.conn = self._create_connection()
            self.his_is_connect = True
            print(f"His {self.vendor} Connect Success")
        except (pymysql.Error, KeyError, ValueError) as e:
            self.signal.emit({'status': 'err'})
            print('His Connect Err', e)

    def his_is_connected(self):
        return self.his_is_connect

    def _load_his_settings(self):
        config = load_his_settings()
        host = str(config["host"] or "")
        user = str(config["user"] or "")
        database = str(config["database"] or "")

        if not all([host, user, database]):
            raise ValueError("ไม่พบค่าเชื่อมต่อ HIS ใน QSettings")

        return config

    def _create_connection(self):
        return pymysql.connect(
            host=self.config_his['host'],
            user=self.config_his['user'],
            password=self.config_his['password'],
            db=self.config_his['database'],
            port=int(self.config_his['port']),
            charset=self.config_his['charset'],
            client_flag=CLIENT.MULTI_STATEMENTS,
            autocommit=False,
        )

    def reconnect(self):
        try:
            self.config_his = self._load_his_settings()
            self.vendor = self.config_his['his']
            self.conn = self._create_connection()
            self.his_is_connect = True
            print(f"His {self.vendor} Reconnect Success")
        except (pymysql.Error, KeyError, ValueError) as e:
            self.his_is_connect = False
            self.conn = None
            print('His Reconnect Err', e)

    def ensure_connection(self):
        if self.conn is None:
            self.reconnect()
            return self.his_is_connect
        try:
            self.conn.ping(reconnect=True)
            self.his_is_connect = True
        except pymysql.Error:
            self.reconnect()
        return self.his_is_connect

    def execute_with_retry(self, sql, dict_cursor=False, commit=False, max_retries=1):
        for attempt in range(max_retries + 1):
            if not self.ensure_connection():
                print("his not connect")
                return None
            try:
                cur = self.conn.cursor(pymysql.cursors.DictCursor) if dict_cursor else self.conn.cursor()
                cur.execute(sql if isinstance(sql, bytes) else sql)
                if commit:
                    self.conn.commit()
                return cur
            except pymysql.OperationalError as e:
                err_code = e.args[0] if e.args else 0
                if err_code in (2006, 2013, 2055) and attempt < max_retries:
                    print(f"His connection lost (err {err_code}), retry {attempt + 1}...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                raise
            except pymysql.Error:
                raise

    def updateStructor(self):
        pass

    def createVisitNumber(self):
        sql_hosxp = """         

                      select concat(
                      CAST((RIGHT(YEAR(CURRENT_DATE)+543,2)) AS CHAR CHARACTER SET utf8)
                      ,CAST((LPAD(MONTH(CURRENT_DATE),2,0)) AS CHAR CHARACTER SET utf8)
                      ,CAST((LPAD(DAY(CURRENT_DATE),2,0)) AS CHAR CHARACTER SET utf8)
                      ,CAST((TIME_FORMAT(TIME(NOW()),'%H%i%s')) AS CHAR CHARACTER SET utf8)
                      ) as vn; 

                      """

        if self.vendor == 'hosxp_pcu':
            sql = sql_hosxp
        else:
            sql = "select 0 as vn"

        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row['vn']

    def getPerson(self, cid: str):
        print('His getPerson',cid,self.vendor)
        sql = f""" SELECT t.hn ,t.cid 
,CONCAT(t.pname,t.fname,' ',t.lname) as 'fullname' 
,t.sex,t.birthday as 'birth' 
,concat('(',t.pttype,') ',p.`name`) as 'inscl'
,concat(t.addrpart,' ม.' ,t.moopart ,' ',a.full_name) as 'addr',
pe.pttype_no,
pe.pttype_hospmain,
pe.pttype_hospsub,
pe.patient_hn
from patient t  LEFT JOIN pttype p on p.pttype = t.pttype
LEFT JOIN thaiaddress a  on  a.addressid = CONCAT(t.chwpart,t.amppart,t.tmbpart)
LEFT JOIN person pe on pe.patient_hn = t.hn
WHERE t.cid = '{cid}'  LIMIT 1 """
        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row

    def resolve_visit_rights(self, cid: str, patient: dict | None = None) -> dict:
        patient = patient or self.getPatient(cid)
        person = self.getPerson(cid)

        patient_pttype = ''
        patient_hospmain = ''
        patient_hospsub = ''
        patient_pttype_no = ''
        if patient:
            patient_pttype = str(patient.get('pttype') or '').strip()
            patient_hospmain = str(patient.get('pttype_hospmain') or '').strip()
            patient_hospsub = str(patient.get('pttype_hospsub') or '').strip()
            patient_pttype_no = str(patient.get('pttype_no') or '').strip()

        person_pttype_no = ''
        person_hospmain = ''
        person_hospsub = ''
        if person:
            person_pttype_no = str(person.get('pttype_no') or '').strip()
            person_hospmain = str(person.get('pttype_hospmain') or '').strip()
            person_hospsub = str(person.get('pttype_hospsub') or '').strip()

        return {
            'pttype': patient_pttype,
            'pttype_no': patient_pttype_no or person_pttype_no or str(cid or '').strip(),
            'pttype_hospmain': patient_hospmain or person_hospmain,
            'pttype_hospsub': patient_hospsub or person_hospsub,
            'person': person,
        }

    def getPatient(self, cid: str):
        sql = f"select * from patient where cid = '{cid}'"
        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row

    def getVisitNumberToday(self, cid: str):
        if self.vendor == 'hosxp_pcu':
            sql = f"select vn from  vn_stat where cid = '{cid}' and vstdate = CURRENT_DATE order by vn DESC"
        else:
            sql = "select 0 as vn"

        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        print("His", "getVisitNumberToday", row)
        if row:
            return row['vn']
        else:
            return None

    def getVisitNumberByDate(self, cid: str, visit_date: str):
        if self.vendor == 'hosxp_pcu':
            sql = f"select * from  vn_stat where cid = '{cid}' and vstdate = '{visit_date}' order by vn DESC"
        else:
            sql = "select 0 as vn"

        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        if row:
            return row['vn']
        else:
            return None

    def getPttypeFromInscl(self, sub_inscl: str):
        sql = f"SELECT pttype from pttype  WHERE hipdata_pttype = '{sub_inscl}'"
        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        if row:
            return row['pttype']
        else:
            return None

    def getPcode(self, pttype: str):
        sql = f"SELECT pcode from pttype WHERE pttype = '{pttype}'"
        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        if row:
            return row['pcode']
        else:
            return None

    def getMobileNumber(self, cid: str):
        if self.vendor == 'hosxp_pcu':
            sql = f"select if(mobile_phone_number is null or trim(mobile_phone_number)='',hometel,mobile_phone_number) as mobile from patient WHERE  cid = '{cid}'"
        else:
            sql = "select '0' as mobile"
        #print('his get_mobile',sql)
        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return '0'
        row = cur.fetchone()
        cur.close()
        if row:
            mobile = str(row['mobile'])
            mobile = mobile.replace('-', '').replace(' ', '')
            return mobile if mobile else '0'
        else:
            return '0'

    #เช็คผู้ป่วยใหม่ up-2025-11-06
    def isNewPatient(self, cid: str):
        if self.vendor == 'hosxp_pcu':
            sql = f"select * from patient where cid = '{cid}'"
        else:
            sql = "select '0' as cc"

        cur = self.execute_with_retry(sql, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        if row:
            return False    
        else:
            return True

    def updatePatientMobile(self, cid: str, mobile: str):
        if self.vendor == 'hosxp_pcu':
            sql = f"UPDATE patient SET mobile_phone_number = '{mobile}'  WHERE  cid = '{cid}'"
        else:
            sql = "select '0' as cc"

        cur = self.execute_with_retry(sql, commit=True)
        if cur is None:
            return None
        cur.close()

    def openVisitHosxp(self, data: dict):
        if not self.ensure_connection():
            print("his not connect")
            return None
        print('openVisitHosxp', data)
        cid = data.get('cid')
        patient = self.getPatient(cid)
        if not patient:
            self.signal.emit({'status': 'ไม่พบข้อมูลผู้ป่วย (No Patient)'})
            print({'status': 'ไม่พบข้อมูลผู้ป่วย (No Patient)'})
            return None

        u1 = str(uuid.uuid4())
        uid1 = "{" + u1.upper() + "}"
        u2 = str(uuid.uuid4())
        uid2 = "{" + u2.upper() + "}"

        sub_inscl = data.get('rightcode') or None

        claim_type = data.get('claim_type')
        claim_code = data.get('claim_code')
        mobile = data.get('mobile')
        hcode = data.get('hcode')
        i_price_code = data.get('i_price_code')
        o_price_code = data.get('o_price_code')
        doctor = data.get('doctor')
        staff = data.get('staff')
        dep = data.get('dep')
        spclty = data.get('spclty')
        visit_date = data.get('visit_date')
        visit_time = data.get('visit_time')

        hn = patient.get('hn')
        sex = patient.get('sex')

        all_d = date.today() - patient.get('birthday')
        age_y = int(all_d.days / 365)
        age_m = int((all_d.days % 365) / 30)
        age_d = ((all_d.days % 365) % 30)

        aid = f"{patient['chwpart']}{patient['amppart']}{patient['tmbpart']}"
        moopart = patient['moopart']

        # สิทธิรักษา
        _pttype = self.getPttypeFromInscl(sub_inscl)
        pttype = _pttype if _pttype else patient['pttype']
        pttype = pttype if pttype else ''

        visit_rights = self.resolve_visit_rights(cid, patient)
        pttype_no = visit_rights['pttype_no']
        pttype_hospmain = visit_rights['pttype_hospmain']
        pttype_hospsub = visit_rights['pttype_hospsub']

        if data.get('hosmain'):
            pttype_hospmain = data.get('hosmain')
        if data.get('hossub'):
            pttype_hospsub = data.get('hossub')

        p = self.getPcode(pttype)
        pcode = p if p else ''

        vn = self.createVisitNumber()

        sql = f"""  

                      set @visit_date = (select if('{visit_date}'='None',CURRENT_DATE,'{visit_date}'));
                      set @visit_time = (select if('{visit_time}'='None',CURRENT_TIME,'{visit_time}'));

                      set @vn = '{vn}';
                      set @cid = '{cid}';
                      set @claim_type = '{claim_type}';
                      set @claim_code = '{claim_code}';
                      set @cc = '{claim_code}';


                      set @hn = '{hn}';
                      set @sex = '{sex}';
                      set @age_y = '{age_y}';
                      set @age_m = '{age_m}';
                      set @age_d = '{age_d}';
                      set @aid = '{aid}'; # รหัสจังหวัด อำเภอ ตำบล
                      set @moopart = '{moopart}'; # หมู่ที่


                      set @pttype = '{pttype}';
                      set @pttypeno = (select (if ('{pttype_no}'= 'None','','{pttype_no}')));
                      set @hospmain = '{pttype_hospmain}';
                      set @hospsub = '{pttype_hospsub}';
                      set @pcode = '{pcode}';
                      set @hcode = '{hcode}'; 



                      set @vstdate = @visit_date;
                      set @vsttime = @visit_time;
                      set @guid1 = '{uid1}';
                      set @guid2 = '{uid2}';



                      set @ovst_seq_id = (select get_serialnumber('ovst_seq_id')); -- ใช้ ovst_seq_id หรือ seq_id
                      set @nhso_seq_id = @ovst_seq_id;
                      set @nhso_seq_id = CAST(@nhso_seq_id AS CHAR CHARACTER SET utf8);
                      set @ovst_q_today = concat('ovst-q-',LEFT(@vn,6));
                      set @ovst_q = (select get_serialnumber(@ovst_q_today));


                      set @doctor = '{doctor}';
                      set @staff = '{staff}';
                      set @dep = '{dep}'; #ห้องตรวจ
                      set @spclty = '{spclty}'; #แผนก
                      set @ovstlist = '01'; #มาเอง
                      set @visit_type = ( SELECT   IF( (@visit_time  >= '16:30:00') OR (@visit_time <= '08:30:00') or (@visit_date in (SELECT holiday_date from holiday)),'O','I') );
                      set @lastvisit = 0;
                      set @pt_subtype = (select pt_subtype from pt_subtype where pcu is not null limit 1);


                      INSERT INTO vn_insert (vn) VALUES (@vn);
                      INSERT INTO vn_stat_signature (vn) VALUES (@vn);


                      INSERT INTO ovst (hos_guid,vn,hn,vstdate,vsttime,doctor,hospmain,hospsub,oqueue,ovstist,pttype,pttypeno,spclty,cur_dep,pt_subtype,visit_type,staff) 
                      VALUES (@guid1,@vn,@hn,@vstdate,@vsttime,@doctor,@hospmain,@hospsub,@ovst_q,@ovstlist,@pttype,@pttypeno,@spclty,@dep,@pt_subtype,@visit_type,@staff);


                      INSERT INTO ovst_seq (vn,seq_id,nhso_seq_id,update_datetime,promote_visit,last_check_datetime)
                      VALUES (@vn,@ovst_seq_id,@nhso_seq_id,NOW(),'N',NOW()); # complete


                      INSERT INTO vn_stat (vn,hn,pdx,lastvisit,dx_doctor,
                      dx0,dx1,dx2,dx3,dx4,dx5,sex,age_y,age_m,age_d,aid,moopart,pttype,spclty,vstdate
                      ,pcode,hcode,hospmain,hospsub,pttypeno,cid) 
                      VALUES (@vn,@hn,'',@lastvisit,@doctor,'','','','','','',@sex,@age_y,@age_m,@age_d,@aid,@moopart,@pttype
                      ,@spclty,@vstdate,@pcode,@hcode,@hospmain,@hospsub,@pttypeno,@cid);


                      set @bw = (select bw from opdscreen where hn = @hn and bw>0 and vn<@vn order by vn desc limit 1);
                      set @height = (select height from opdscreen where hn = @hn and height>0 and vn<@vn order by vn desc limit 1);
                      set @waist = (select waist from opdscreen where hn = @hn and waist>0 and vn<@vn order by vn desc limit 1);
                      set @bps = (select bps from opdscreen where hn = @hn  and vn<@vn order by vn desc limit 1);
                      set @bpd = (select bpd from opdscreen where hn = @hn  and vn<@vn order by vn desc limit 1);
                      set @pulse = (select pulse from opdscreen where hn = @hn and vn<@vn order by vn desc limit 1);
                      set @temperature = '37.0';
                      INSERT INTO opdscreen (hos_guid,vn,hn,vstdate,vsttime,bw,height,waist,bps,bpd,pulse,temperature) 
                      VALUES (@guid2,@vn,@hn,@vstdate,@vsttime,@bw,@height,@waist,@bps,@bpd,@pulse,@temperature);




                      set @icode :=  (SELECT IF(@visit_type = 'O' ,'{o_price_code}','{i_price_code}'));
                      set @price :=  (select price from nondrugitems where icode = @icode);
                      INSERT INTO opitemrece (hos_guid,vn,hn,icode,qty,unitprice,vstdate,vsttime,
                      staff,item_no,last_modified,sum_price) 
                      VALUES (@guid2,@vn,@hn,@icode,1,@price,@vstdate,@vsttime,
                      @staff,1,NOW(),@price);       


                      INSERT INTO dt_list (vn) VALUES (@vn);

                      UPDATE patient SET last_visit= @vstdate,mobile_phone_number = '{mobile}'  WHERE  cid = @cid;


                      INSERT INTO visit_pttype (vn, pttype, staff, hospmain, hospsub, pttypeno, update_datetime,pttype_note,claim_code,auth_code) 
                      VALUES (@vn, @pttype, @staff, @hospmain, @hospsub, @pttypeno , NOW(),@claim_type,@claim_code,@claim_code);



                      """

        result = vn
        for attempt in range(2):
            if not self.ensure_connection():
                print("his not connect")
                return None
            cur = self.conn.cursor()
            try:
                cur.execute(sql.encode(self.config_his['charset']))
                self.conn.commit()
                with open('sql_vst_hos_ok.txt', 'w', encoding='utf-8') as f:
                    f.write(str(sql))
                break
            except pymysql.OperationalError as e:
                cur.close()
                err_code = e.args[0] if e.args else 0
                if err_code in (2006, 2013, 2055) and attempt == 0:
                    print(f"His connection lost (err {err_code}), retry openVisitHosxp...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                self.conn.rollback()
                print('visit err', e)
                self.signal.emit({'status': e})
                with open('visit_err.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(e))
                with open('sql_vst_hos_err.txt', 'a+', encoding='utf-8') as f:
                    n = str("\r\n##############################################################################")
                    f.write(str(sql) + n)
                result = None
                break
            except pymysql.Error as e:
                cur.close()
                self.conn.rollback()
                print('visit err', e)
                self.signal.emit({'status': e})
                with open('visit_err.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(e))
                with open('sql_vst_hos_err.txt', 'a+', encoding='utf-8') as f:
                    n = str("\r\n##############################################################################")
                    f.write(str(sql) + n)
                result = None
                break
            finally:
                cur.close()
        return result

    def updateHosxpOvstKey(self, vn, ovst_key):
        sql = f"update ovst set ovst_key = '{ovst_key}' where vn = '{vn}'"
        cur = self.execute_with_retry(sql, commit=True)
        if cur is None:
            return None
        cur.close()
        return ovst_key

    def updateVisitHosxp(self, data: dict):
        if not self.ensure_connection():
            print("his not connect")
            return None
        patient = self.getPatient(data['cid'])
        if not patient:
            self.signal.emit({'status': 'ไม่พบข้อมูลผู้ป่วย (No Patient)'})
            return None

        cid = data['cid']
        _sub_inscl = data.get('sub_inscl') or None
        sub_inscl = _sub_inscl[1:3] if _sub_inscl else None

        claim_type = data['claim_type']
        claim_code = data['claim_code']
        mobile = data['mobile']
        hcode = data['hcode']
        doctor = data['doctor']
        staff = data['staff']
        dep = data['dep']
        spclty = data['spclty']

        hn = patient['hn']
        sex = patient['sex']

        all_d = date.today() - patient['birthday']
        age_y = int(all_d.days / 365)
        age_m = int((all_d.days % 365) / 30)
        age_d = ((all_d.days % 365) % 30)

        aid = f"{patient['chwpart']}{patient['amppart']}{patient['tmbpart']}"
        moopart = patient['moopart']

        # สิทธิรักษา
        _pttype = self.getPttypeFromInscl(sub_inscl)
        pttype = _pttype if _pttype else patient['pttype']
        pttype = pttype if pttype else ''
        visit_rights = self.resolve_visit_rights(cid, patient)
        pttype_no = visit_rights['pttype_no']
        pttype_hospmain = visit_rights['pttype_hospmain']
        pttype_hospsub = visit_rights['pttype_hospsub']

        if data['hospmain']:
            pttype_hospmain = data['hospmain']
        if data['hospsub']:
            pttype_hospsub = data['hospsub']

        p = self.getPcode(pttype)
        pcode = p if p else ''

        vn = data['vn']

        sql = f"""  

                              set @vn = '{vn}';
                              set @cid = '{cid}';
                              set @claim_type = '{claim_type}';
                              set @claim_code = '{claim_code}';
                              set @cc = '{claim_code}';


                              set @hn = '{hn}';
                              set @sex = '{sex}';
                              set @age_y = '{age_y}';
                              set @age_m = '{age_m}';
                              set @age_d = '{age_d}';
                              set @aid = '{aid}'; # รหัสจังหวัด อำเภอ ตำบล
                              set @moopart = '{moopart}'; # หมู่ที่


                              set @pttype = '{pttype}';
                              set @pttypeno = (select (if ('{pttype_no}'= 'None','','{pttype_no}')));
                              set @hospmain = '{pttype_hospmain}';
                              set @hospsub = '{pttype_hospsub}';
                              set @pcode = '{pcode}';
                              set @hcode = '{hcode}'; 



                              set @doctor = '{doctor}';
                              set @staff = '{staff}';
                              set @dep = '{dep}'; #ห้องตรวจ
                              set @spclty = '{spclty}'; #แผนก
                              set @ovstlist = '01'; #มาเอง
                              set @visit_type = ( SELECT   IF( (@visit_time  >= '16:30:00') OR (@visit_time <= '08:30:00') or (@visit_date in (SELECT holiday_date from holiday)),'O','I') );
                              set @lastvisit = 0;
                              set @pt_subtype = (select pt_subtype from pt_subtype where pcu is not null limit 1);

                              -- update opdscreen SET cc =  concat('{claim_code}','\r\n',cc)  where vn = @vn;

                              update ovst SET pttype=@pttype,pttypeno=@pttypeno,pt_subtype=@pt_subtype where vn = @vn;                          

                              update vn_stat SET pttype = @pttype where vn = @vn;       

                              UPDATE patient SET mobile_phone_number = '{mobile}'  WHERE  cid = @cid;

                              REPLACE INTO visit_pttype (vn, pttype, staff, hospmain, hospsub, pttypeno, update_datetime,pttype_note,claim_code,auth_code) 
                              VALUES (@vn, @pttype, @staff, @hospmain, @hospsub, @pttypeno , NOW(),@claim_type,@claim_code,@claim_code);



                              """

        result = vn
        for attempt in range(2):
            if not self.ensure_connection():
                print("his not connect")
                return None
            cur = self.conn.cursor()
            try:
                cur.execute(sql.encode(self.config_his['charset']))
                self.conn.commit()
                break
            except pymysql.OperationalError as e:
                cur.close()
                err_code = e.args[0] if e.args else 0
                if err_code in (2006, 2013, 2055) and attempt == 0:
                    print(f"His connection lost (err {err_code}), retry updateVisitHosxp...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                self.conn.rollback()
                print('update visit', e)
                self.signal.emit({'status': e})
                with open('visit_err.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(e))
                with open('sql_vst_hos_err.txt', 'a+', encoding='utf-8') as f:
                    n = str("\r\n##############################################################################")
                    f.write(str(sql) + n)
                result = None
                break
            except pymysql.Error as e:
                cur.close()
                self.conn.rollback()
                print('update visit', e)
                self.signal.emit({'status': e})
                with open('visit_err.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(e))
                with open('sql_vst_hos_err.txt', 'a+', encoding='utf-8') as f:
                    n = str("\r\n##############################################################################")
                    f.write(str(sql) + n)
                result = None
                break
            finally:
                cur.close()
        return result

if __name__ == '__main__':
    print('main')
    his = His2()
    rs = his.his_is_connected()
    print(rs)
