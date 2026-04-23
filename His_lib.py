from PyQt6.QtCore import QObject
import pymysql
from pymysql.constants import CLIENT
from PyQt6.QtCore import pyqtSignal
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

    def createVisitNumber(self, visit_date: str | None = None):
        if self.vendor != 'hosxp_pcu':
            return '0'

        try:
            visit_date_obj = datetime.strptime(str(visit_date), '%Y-%m-%d').date() if visit_date else date.today()
        except ValueError:
            visit_date_obj = date.today()

        prefix = f"{(visit_date_obj.year + 543) % 100:02d}{visit_date_obj.month:02d}{visit_date_obj.day:02d}"

        while True:
            now = datetime.now()
            vn = f"{prefix}{now:%H%M%S}"
            cur = self.execute_with_retry(
                f"select count(*) as c from ovst where vn = '{vn}'",
                dict_cursor=True
            )
            if cur is None:
                return None
            row = cur.fetchone()
            cur.close()
            if int(row['c'] or 0) == 0:
                return vn
            time.sleep(1.1)

    def getPerson(self, cid: str):
        print('His getPerson',cid,self.vendor)
        sql = f""" SELECT t.hn ,t.cid 
,CONCAT(t.pname,t.fname,' ',t.lname) as 'fullname' 
,t.sex,t.birthday as 'birth' 
,concat('(',t.pttype,') ',p.`name`) as 'inscl'
,concat(t.addrpart,' ม.' ,t.moopart ,' ',a.full_name) as 'addr',
pe.person_id,
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

        claim_type = data.get('claim_type') or ''
        claim_code = data.get('claim_code') or ''
        mobile = data.get('mobile') or self.getMobileNumber(cid)
        hcode = data.get('hcode') or ''
        i_price_code = data.get('i_price_code') or '3001647'
        o_price_code = data.get('o_price_code') or '3000002'
        doctor = data.get('doctor') or '0010'
        staff = data.get('staff') or 'sa'
        dep = data.get('dep') or '014'
        spclty = data.get('spclty') or '01'
        ovstist = str(data.get('ovstist') or '05').strip() or '05'
        visit_date = data.get('visit_date') or date.today().isoformat()
        visit_time = data.get('visit_time') or datetime.now().strftime('%H:%M:%S')
        dx_code = str(data.get('dx_code') or 'Z718').strip().upper()
        main_pdx = str(data.get('main_pdx') or (dx_code[:3] if len(dx_code) >= 3 else dx_code)).strip().upper()

        hn = patient.get('hn')
        sex = patient.get('sex')

        try:
            visit_date_obj = datetime.strptime(str(visit_date), '%Y-%m-%d').date()
        except ValueError:
            visit_date_obj = date.today()

        all_d = visit_date_obj - patient.get('birthday')
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
        if not hcode:
            hcode = pttype_hospsub or ''

        person_id = ''
        if visit_rights.get('person'):
            person_id = str(visit_rights['person'].get('person_id') or '').strip()

        vn = self.createVisitNumber(visit_date)

        sql = f"""  

                      set @visit_date = (select if('{visit_date}'='None',CURRENT_DATE,'{visit_date}'));
                      set @visit_time = (select if('{visit_time}'='None',CURRENT_TIME,'{visit_time}'));

                      set @vn = '{vn}';
                      set @cid = '{cid}';
                      set @claim_type = '{claim_type}';
                      set @claim_code = '{claim_code}';
                      set @cc = 'ให้บริการ telemedicine';

                      set @hn = '{hn}';
                      set @sex = '{sex}';
                      set @age_y = '{age_y}';
                      set @age_m = '{age_m}';
                      set @age_d = '{age_d}';
                      set @aid = '{aid}';
                      set @moopart = '{moopart}';

                      set @pttype = '{pttype}';
                      set @pttypeno = (select (if ('{pttype_no}'= 'None','','{pttype_no}')));
                      set @hospmain = '{pttype_hospmain}';
                      set @hospsub = '{pttype_hospsub}';
                      set @pcode = '{pcode}';
                      set @hcode = '{hcode}';
                      set @person_id = '{person_id}';

                      set @vstdate = @visit_date;
                      set @vsttime = @visit_time;
                      set @guid1 = '{uid1}';
                      set @guid2 = '{uid2}';

                      set @ovst_seq_id = (select get_serialnumber('ovst_seq_id'));
                      set @nhso_seq_id = @ovst_seq_id;
                      set @nhso_seq_id = CAST(@nhso_seq_id AS CHAR CHARACTER SET utf8);
                      set @ovst_q_today = concat('ovst-q-',LEFT(@vn,6));
                      set @ovst_q = (select get_serialnumber(@ovst_q_today));

                      set @doctor = '{doctor}';
                      set @staff = '{staff}';
                      set @dep = '{dep}';
                      set @spclty = '{spclty}';
                      set @ovstlist = '{ovstist}';
                      set @ovstost = '99';
                      set @visit_type = ( SELECT IF((@visit_time >= '16:30:00') OR (@visit_time <= '08:30:00') or (@visit_date in (SELECT holiday_date from holiday)),'O','I') );
                      set @lastvisit = 0;
                      set @pt_subtype = (select pt_subtype from pt_subtype where pcu is not null limit 1);

                      INSERT INTO vn_insert (vn) VALUES (@vn);
                      INSERT INTO vn_stat_signature (vn) VALUES (@vn);

                      INSERT INTO ovst (hos_guid,vn,hn,vstdate,vsttime,doctor,hospmain,hospsub,oqueue,ovstist,ovstost,pttype,pttypeno,spclty,cur_dep,pt_subtype,visit_type,staff)
                      VALUES (@guid1,@vn,@hn,@vstdate,@vsttime,@doctor,@hospmain,@hospsub,@ovst_q,@ovstlist,@ovstost,@pttype,@pttypeno,@spclty,@dep,@pt_subtype,@visit_type,@staff);

                      INSERT INTO ovst_seq (vn,seq_id,nhso_seq_id,update_datetime,promote_visit,last_check_datetime)
                      VALUES (@vn,@ovst_seq_id,@nhso_seq_id,NOW(),'N',NOW());

                      UPDATE ovst_seq
                      SET pcu_person_id = @person_id,
                          update_datetime = NOW(),
                          last_check_datetime = NOW()
                      WHERE vn = @vn;

                      INSERT INTO vn_stat (vn,hn,pdx,lastvisit,dx_doctor,
                      dx0,dx1,dx2,dx3,dx4,dx5,sex,age_y,age_m,age_d,aid,moopart,pttype,spclty,vstdate
                      ,pcode,hcode,hospmain,hospsub,pttypeno,cid)
                      VALUES (@vn,@hn,'',@lastvisit,@doctor,'','','','','','',@sex,@age_y,@age_m,@age_d,@aid,@moopart,@pttype
                      ,@spclty,@vstdate,@pcode,@hcode,@hospmain,@hospsub,@pttypeno,@cid);

                      set @bw = (select bw from opdscreen where hn = @hn and bw>0 and vn<@vn order by vn desc limit 1);
                      set @height = (select height from opdscreen where hn = @hn and height>0 and vn<@vn order by vn desc limit 1);
                      set @waist = (select waist from opdscreen where hn = @hn and waist>0 and vn<@vn order by vn desc limit 1);
                      set @bps = (select bps from opdscreen where hn = @hn and vn<@vn order by vn desc limit 1);
                      set @bpd = (select bpd from opdscreen where hn = @hn and vn<@vn order by vn desc limit 1);
                      set @pulse = (select pulse from opdscreen where hn = @hn and vn<@vn order by vn desc limit 1);
                      set @temperature = '37.0';

                      INSERT INTO opdscreen (hos_guid,vn,hn,vstdate,vsttime,bw,height,waist,bps,bpd,pulse,temperature,cc)
                      VALUES (@guid2,@vn,@hn,@vstdate,@vsttime,@bw,@height,@waist,@bps,@bpd,@pulse,@temperature,@cc);

                      UPDATE opdscreen
                      SET bmi = ROUND((bw / POWER((height / 100),2)), 3),
                          cc = @cc
                      WHERE hos_guid = @guid2;

                      set @icode := (SELECT IF(@visit_type = 'O' ,'{o_price_code}','{i_price_code}'));
                      set @price := (select price from nondrugitems where icode = @icode);

                      INSERT INTO opitemrece (hos_guid,vn,hn,icode,qty,unitprice,vstdate,vsttime,
                      staff,item_no,last_modified,sum_price,pttype,income,paidst)
                      VALUES (@guid2,@vn,@hn,@icode,1,@price,@vstdate,@vsttime,
                      @staff,1,NOW(),@price,@pttype,'12','02');

                      UPDATE opitemrece
                      SET rxdate = @vstdate,
                          sub_type = '3',
                          cost = 0,
                          node_id = '',
                          last_modified = NOW()
                      WHERE hos_guid = @guid2;

                      INSERT INTO opitemrece_summary
                        (vn,rxdate,icode,income,qty,sum_price,department,hos_guid,opitemrece_id,opitemrece_did,hos_guid_ext)
                      VALUES
                        (@vn,@vstdate,@icode,'12',1,@price,'OPD',@guid2,NULL,'',NULL);

                      DELETE FROM incoth WHERE vn = @vn;

                      INSERT INTO incoth
                        (vn,billdate,billtime,hn,incdate,inctime,income,paidst,rcpno,rcptamt,`user`,computer,finance_number,porder,discount,verify,pttype,hos_guid,hos_guid_ext)
                      VALUES
                        (@vn,@vstdate,@vsttime,@hn,@vstdate,@vsttime,'12','02',NULL,@price,NULL,NULL,NULL,NULL,NULL,'N',@pttype,NULL,NULL);

                      INSERT INTO inc_opd_stat
                        (vn,hn,vstdate,pttype,pcode,inc01,inc02,inc03,inc04,inc05,inc06,inc07,inc08,inc09,inc10,inc11,inc12,inc13,inc14,inc15,inc16,inc17,income,inc_drug,inc_nondrug,uinc01,uinc02,uinc03,uinc04,uinc05,uinc06,uinc07,uinc08,uinc09,uinc10,uinc11,uinc12,uinc13,uinc14,uinc15,uinc16,uinc17,uincome,uinc_drug,uinc_nondrug,hos_guid)
                      VALUES
                        (@vn,@hn,@vstdate,@pttype,NULL,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,@price,0,0,0,0,0,@price,0,0,NULL);

                      INSERT INTO fbshistory
                        (vn,hn,fbslevel,fbs1mo,fbs2mo,fbs3mo,fbs4mo,fbs5mo,fbs6mo,hos_guid)
                      VALUES
                        (@vn,@hn,NULL,0,0,0,0,0,0,NULL);

                      UPDATE vn_stat
                      SET income = @price,
                          paid_money = 0,
                          remain_money = 0,
                          uc_money = @price,
                          item_money = @price,
                          inc12 = @price,
                          inc_drug = 0,
                          inc_nondrug = 0,
                          pt_subtype = @pt_subtype,
                          ym = DATE_FORMAT(@vstdate,'%Y-%m'),
                          ill_visit = 'Y',
                          old_diagnosis = 'N',
                          debt_id_list = ''
                      WHERE vn = @vn;

                      INSERT INTO dt_list (vn) VALUES (@vn);

                      UPDATE patient SET last_visit= @vstdate,mobile_phone_number = '{mobile}' WHERE cid = @cid;

                      INSERT INTO visit_pttype (vn, pttype, staff, hospmain, hospsub, pttypeno, update_datetime,pttype_note,claim_code,auth_code)
                      VALUES (@vn, @pttype, @staff, @hospmain, @hospsub, @pttypeno, NOW(),@claim_type,@claim_code,@claim_code);

                      set @dx = '{dx_code}';
                      set @main_pdx = '{main_pdx}';
                      set @ovst_diag_id = (select get_serialnumber('ovst_diag_id'));
                      set @opi_dispense_id = (select get_serialnumber('opi_dispense_id'));

                      INSERT INTO ovstdiag
                        (ovst_diag_id,vn,icd10,hn,vstdate,vsttime,diagtype,icd103,hcode,doctor,episode,ext_code,hos_guid,dep_flag,ovst_oper_type,staff,dx_guid,lock_dx,dx_code_note,ovstdiag_severe_type_id,diag_no,update_datetime,confirm,confirm_staff,opi_guid,sct_id)
                      VALUES
                        (@ovst_diag_id,@vn,@dx,@hn,@vstdate,@vsttime,'1',NULL,NULL,@doctor,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NOW(),NULL,NULL,NULL,NULL);

                      UPDATE ovst_seq
                      SET update_datetime = NOW(),
                          last_check_datetime = NOW()
                      WHERE vn = @vn;

                      UPDATE vn_stat
                      SET pdx = @dx,
                          main_pdx = @main_pdx
                      WHERE vn = @vn;

                      DELETE FROM opi_dispense WHERE hos_guid = @guid2;

                      INSERT INTO opi_dispense
                        (opi_dispense_id,hos_guid,icode,qty,usage_code,dose,unit_name,frequency_code,time_code,drug_hint_text,modify_datetime,modify_staff,modify_computer,print_sticker,price,sp_use,usage_unit_code,doctor,usage_line1,usage_line2,usage_line3,usage_line4,usage_shortlist,usage_lock,med_plan_number,orderstatus,use_rx_pattern,opi_dispense_type_id,opi_dispense_item_type_id,opi_dispense_qty_type_id,opi_dispense_usage_type_id,opi_dispense_his_name,pttype_items_price_id,depcode,shortlist,discount,usage_eng_line1,usage_eng_line2,usage_eng_line3,usage_eng_line4,lang,qty_per_day,finish_date,usage_note,presc_duration_days)
                      VALUES
                        (@opi_dispense_id,@guid2,@icode,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);

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
        time.sleep(0.1)
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
                              set @ovstlist = '05'; #Telehealth
                              set @ovstost = '99';
                              set @visit_type = ( SELECT   IF( (@visit_time  >= '16:30:00') OR (@visit_time <= '08:30:00') or (@visit_date in (SELECT holiday_date from holiday)),'O','I') );
                              set @lastvisit = 0;
                              set @pt_subtype = (select pt_subtype from pt_subtype where pcu is not null limit 1);

                              -- update opdscreen SET cc =  concat('{claim_code}','\r\n',cc)  where vn = @vn;

                              update ovst SET pttype=@pttype,pttypeno=@pttypeno,pt_subtype=@pt_subtype,ovstost=@ovstost where vn = @vn;                          

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
