from __future__ import annotations

import time
import uuid
from datetime import date, datetime

import psycopg2
import psycopg2.extras
from PyQt6.QtCore import QObject, pyqtSignal

from Setting_helper import load_his_settings


class His2Pg(QObject):
    """HOSxP PostgreSQL edition connection + visit operations.

    Mirrors His_lib.His2 but targets HOSxP ports that run on PostgreSQL.
    Multi-statement MySQL session-variable SQL is replaced by Python-side
    parameter computation and individual parameterised statements in one
    transaction.
    """

    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.conn = None
        self.his_is_connect = False
        self.config_his = self._load_his_settings()
        print('His-PG Connect', self.config_his)
        self.vendor = self.config_his['his']
        try:
            self.conn = self._create_connection()
            self.his_is_connect = True
            print(f"His-PG {self.vendor} Connect Success")
        except (psycopg2.Error, KeyError, ValueError) as e:
            self.signal.emit({'status': 'err'})
            print('His-PG Connect Err', e)

    def his_is_connected(self) -> bool:
        return self.his_is_connect

    def _load_his_settings(self) -> dict:
        config = load_his_settings()
        host = str(config["host"] or "")
        user = str(config["user"] or "")
        database = str(config["database"] or "")

        if not all([host, user, database]):
            raise ValueError("ไม่พบค่าเชื่อมต่อ HIS ใน QSettings")

        return config

    def _create_connection(self):
        conn = psycopg2.connect(
            host=self.config_his['host'],
            user=self.config_his['user'],
            password=self.config_his['password'],
            dbname=self.config_his['database'],
            port=int(self.config_his['port']),
        )
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute("SET client_encoding = 'UTF8'")
            conn.commit()
        except psycopg2.Error:
            conn.rollback()
        return conn

    def reconnect(self):
        try:
            if self.conn is not None:
                try:
                    self.conn.close()
                except psycopg2.Error:
                    pass
            self.config_his = self._load_his_settings()
            self.vendor = self.config_his['his']
            self.conn = self._create_connection()
            self.his_is_connect = True
            print(f"His-PG {self.vendor} Reconnect Success")
        except (psycopg2.Error, KeyError, ValueError) as e:
            self.his_is_connect = False
            self.conn = None
            print('His-PG Reconnect Err', e)

    def ensure_connection(self) -> bool:
        if self.conn is None or self.conn.closed:
            self.reconnect()
            return self.his_is_connect
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
            self.his_is_connect = True
        except psycopg2.Error:
            self.reconnect()
        return self.his_is_connect

    def execute_with_retry(
        self,
        sql: str,
        params: tuple | dict | None = None,
        dict_cursor: bool = False,
        commit: bool = False,
        max_retries: int = 1,
    ):
        for attempt in range(max_retries + 1):
            if not self.ensure_connection():
                print("his-pg not connect")
                return None
            try:
                cur = (
                    self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    if dict_cursor
                    else self.conn.cursor()
                )
                cur.execute(sql, params)
                if commit:
                    self.conn.commit()
                return cur
            except psycopg2.OperationalError as e:
                try:
                    self.conn.rollback()
                except psycopg2.Error:
                    pass
                if attempt < max_retries:
                    print(f"His-PG connection lost ({e}), retry {attempt + 1}...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                raise
            except psycopg2.Error:
                try:
                    self.conn.rollback()
                except psycopg2.Error:
                    pass
                raise

    def createVisitNumber(self, visit_date: str | None = None) -> str | None:
        if self.vendor != 'hosxp_pcu':
            return '0'

        try:
            visit_date_obj = (
                datetime.strptime(str(visit_date), '%Y-%m-%d').date()
                if visit_date
                else date.today()
            )
        except ValueError:
            visit_date_obj = date.today()

        prefix = f"{(visit_date_obj.year + 543) % 100:02d}{visit_date_obj.month:02d}{visit_date_obj.day:02d}"

        while True:
            now = datetime.now()
            vn = f"{prefix}{now:%H%M%S}"
            cur = self.execute_with_retry(
                "SELECT COUNT(*) AS c FROM ovst WHERE vn = %s",
                (vn,),
                dict_cursor=True,
            )
            if cur is None:
                return None
            row = cur.fetchone()
            cur.close()
            if int(row['c'] or 0) == 0:
                return vn
            time.sleep(1.1)

    def getPerson(self, cid: str):
        print('His-PG getPerson', cid, self.vendor)
        sql = """
            SELECT t.hn, t.cid,
                   CONCAT(t.pname, t.fname, ' ', t.lname) AS fullname,
                   t.sex, t.birthday AS birth,
                   CONCAT('(', t.pttype, ') ', p.name) AS inscl,
                   CONCAT(t.addrpart, ' ม.', t.moopart, ' ', a.full_name) AS addr,
                   pe.person_id,
                   pe.pttype_no,
                   pe.pttype_hospmain,
                   pe.pttype_hospsub,
                   pe.patient_hn
            FROM patient t
            LEFT JOIN pttype p ON p.pttype = t.pttype
            LEFT JOIN thaiaddress a
                   ON a.addressid = CONCAT(t.chwpart, t.amppart, t.tmbpart)
            LEFT JOIN person pe ON pe.patient_hn = t.hn
            WHERE t.cid = %s
            LIMIT 1
        """
        cur = self.execute_with_retry(sql, (cid,), dict_cursor=True)
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
        cur = self.execute_with_retry(
            "SELECT * FROM patient WHERE cid = %s", (cid,), dict_cursor=True
        )
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row

    def getVisitNumberToday(self, cid: str):
        if self.vendor == 'hosxp_pcu':
            sql = (
                "SELECT vn FROM vn_stat "
                "WHERE cid = %s AND vstdate = CURRENT_DATE "
                "ORDER BY vn DESC"
            )
            params = (cid,)
        else:
            sql = "SELECT 0 AS vn"
            params = None

        cur = self.execute_with_retry(sql, params, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        print("His-PG", "getVisitNumberToday", row)
        return row['vn'] if row else None

    def getVisitNumberByDate(self, cid: str, visit_date: str):
        if self.vendor == 'hosxp_pcu':
            sql = (
                "SELECT * FROM vn_stat "
                "WHERE cid = %s AND vstdate = %s "
                "ORDER BY vn DESC"
            )
            params = (cid, visit_date)
        else:
            sql = "SELECT 0 AS vn"
            params = None

        cur = self.execute_with_retry(sql, params, dict_cursor=True)
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row['vn'] if row else None

    def getPttypeFromInscl(self, sub_inscl: str):
        cur = self.execute_with_retry(
            "SELECT pttype FROM pttype WHERE hipdata_pttype = %s",
            (sub_inscl,),
            dict_cursor=True,
        )
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row['pttype'] if row else None

    def getPcode(self, pttype: str):
        cur = self.execute_with_retry(
            "SELECT pcode FROM pttype WHERE pttype = %s",
            (pttype,),
            dict_cursor=True,
        )
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return row['pcode'] if row else None

    def getMobileNumber(self, cid: str) -> str:
        if self.vendor == 'hosxp_pcu':
            sql = (
                "SELECT CASE "
                "  WHEN mobile_phone_number IS NULL OR TRIM(mobile_phone_number) = '' "
                "  THEN hometel ELSE mobile_phone_number "
                "END AS mobile FROM patient WHERE cid = %s"
            )
            params = (cid,)
        else:
            sql = "SELECT '0' AS mobile"
            params = None

        cur = self.execute_with_retry(sql, params, dict_cursor=True)
        if cur is None:
            return '0'
        row = cur.fetchone()
        cur.close()
        if row:
            mobile = str(row['mobile'] or '').replace('-', '').replace(' ', '')
            return mobile or '0'
        return '0'

    def isNewPatient(self, cid: str) -> bool | None:
        if self.vendor != 'hosxp_pcu':
            return None
        cur = self.execute_with_retry(
            "SELECT 1 FROM patient WHERE cid = %s", (cid,), dict_cursor=True
        )
        if cur is None:
            return None
        row = cur.fetchone()
        cur.close()
        return not bool(row)

    def updatePatientMobile(self, cid: str, mobile: str):
        if self.vendor != 'hosxp_pcu':
            return None
        cur = self.execute_with_retry(
            "UPDATE patient SET mobile_phone_number = %s WHERE cid = %s",
            (mobile, cid),
            commit=True,
        )
        if cur is None:
            return None
        cur.close()

    def _get_serialnumber(self, cur, key: str) -> str:
        """Call HOSxP's get_serialnumber() stored function.

        Assumes the HOSxP-PG port exposes this function with the same name.
        If your deployment uses a different name (e.g. get_serial_no), change here.
        """
        cur.execute("SELECT get_serialnumber(%s) AS sn", (key,))
        row = cur.fetchone()
        return str(row[0] if row else '')

    def openVisitHosxp(self, data: dict):
        if not self.ensure_connection():
            print("his-pg not connect")
            return None
        print('openVisitHosxpPg', data)

        cid = data.get('cid')
        patient = self.getPatient(cid)
        if not patient:
            self.signal.emit({'status': 'ไม่พบข้อมูลผู้ป่วย (No Patient)'})
            print({'status': 'ไม่พบข้อมูลผู้ป่วย (No Patient)'})
            return None

        uid1 = '{' + str(uuid.uuid4()).upper() + '}'
        uid2 = '{' + str(uuid.uuid4()).upper() + '}'

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
        ovstost = '99'
        visit_date = data.get('visit_date') or date.today().isoformat()
        visit_time = data.get('visit_time') or datetime.now().strftime('%H:%M:%S')
        dx_code = str(data.get('dx_code') or 'Z718').strip().upper()
        main_pdx = str(
            data.get('main_pdx') or (dx_code[:3] if len(dx_code) >= 3 else dx_code)
        ).strip().upper()
        cc = 'ให้บริการ telemedicine'

        hn = patient.get('hn')
        sex = patient.get('sex')

        try:
            visit_date_obj = datetime.strptime(str(visit_date), '%Y-%m-%d').date()
        except ValueError:
            visit_date_obj = date.today()
        vstdate = visit_date_obj.isoformat()
        vsttime = visit_time

        birthday = patient.get('birthday')
        if isinstance(birthday, date):
            all_d = visit_date_obj - birthday
            age_y = int(all_d.days / 365)
            age_m = int((all_d.days % 365) / 30)
            age_d = (all_d.days % 365) % 30
        else:
            age_y = age_m = age_d = 0

        aid = f"{patient['chwpart']}{patient['amppart']}{patient['tmbpart']}"
        moopart = patient['moopart']

        _pttype = self.getPttypeFromInscl(sub_inscl) if sub_inscl else None
        pttype = _pttype or patient.get('pttype') or ''

        visit_rights = self.resolve_visit_rights(cid, patient)
        pttype_no = visit_rights['pttype_no']
        pttype_hospmain = data.get('hosmain') or visit_rights['pttype_hospmain']
        pttype_hospsub = data.get('hossub') or visit_rights['pttype_hospsub']

        pcode = self.getPcode(pttype) or ''
        if not hcode:
            hcode = pttype_hospsub or ''

        person_id = ''
        if visit_rights.get('person'):
            person_id = str(visit_rights['person'].get('person_id') or '').strip()

        if str(pttype_no) == 'None':
            pttype_no = ''

        vn = self.createVisitNumber(visit_date)
        if vn is None:
            return None

        result = vn
        for attempt in range(2):
            if not self.ensure_connection():
                print("his-pg not connect")
                return None
            cur = self.conn.cursor()
            try:
                # HOSxP serial numbers
                ovst_seq_id = self._get_serialnumber(cur, 'ovst_seq_id')
                ovst_q_key = f"ovst-q-{vn[:6]}"
                ovst_q = self._get_serialnumber(cur, ovst_q_key)
                ovst_diag_id = self._get_serialnumber(cur, 'ovst_diag_id')
                opi_dispense_id = self._get_serialnumber(cur, 'opi_dispense_id')

                # visit_type: 'O' if outside office hours or holiday, else 'I'
                cur.execute(
                    "SELECT CASE "
                    "  WHEN (%s >= '16:30:00' OR %s <= '08:30:00') "
                    "    OR %s IN (SELECT holiday_date FROM holiday) "
                    "  THEN 'O' ELSE 'I' "
                    "END AS vt",
                    (vsttime, vsttime, vstdate),
                )
                vt_row = cur.fetchone()
                visit_type = (vt_row[0] if vt_row else 'I') or 'I'

                # pt_subtype (first row where pcu is set)
                cur.execute(
                    "SELECT pt_subtype FROM pt_subtype WHERE pcu IS NOT NULL LIMIT 1"
                )
                pt_row = cur.fetchone()
                pt_subtype = pt_row[0] if pt_row else None

                # icode based on visit_type
                icode = o_price_code if visit_type == 'O' else i_price_code
                cur.execute(
                    "SELECT price FROM nondrugitems WHERE icode = %s", (icode,)
                )
                pr_row = cur.fetchone()
                price = pr_row[0] if pr_row else 0

                # previous vitals (latest non-zero before current vn)
                def _latest(col: str):
                    cur.execute(
                        f"SELECT {col} FROM opdscreen "
                        f"WHERE hn = %s AND {col} > 0 AND vn < %s "
                        f"ORDER BY vn DESC LIMIT 1",
                        (hn, vn),
                    )
                    r = cur.fetchone()
                    return r[0] if r else None

                def _latest_any(col: str):
                    cur.execute(
                        f"SELECT {col} FROM opdscreen "
                        f"WHERE hn = %s AND vn < %s "
                        f"ORDER BY vn DESC LIMIT 1",
                        (hn, vn),
                    )
                    r = cur.fetchone()
                    return r[0] if r else None

                bw = _latest('bw')
                height = _latest('height')
                waist = _latest('waist')
                bps = _latest_any('bps')
                bpd = _latest_any('bpd')
                pulse = _latest_any('pulse')
                temperature = 37.0

                # INSERTS / UPDATES
                cur.execute("INSERT INTO vn_insert (vn) VALUES (%s)", (vn,))
                cur.execute("INSERT INTO vn_stat_signature (vn) VALUES (%s)", (vn,))

                cur.execute(
                    """
                    INSERT INTO ovst
                        (hos_guid, vn, hn, vstdate, vsttime, doctor, hospmain, hospsub,
                         oqueue, ovstist, ovstost, pttype, pttypeno, spclty, cur_dep,
                         pt_subtype, visit_type, staff)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        uid1, vn, hn, vstdate, vsttime, doctor, pttype_hospmain,
                        pttype_hospsub, ovst_q, ovstist, ovstost, pttype, pttype_no,
                        spclty, dep, pt_subtype, visit_type, staff,
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO ovst_seq
                        (vn, seq_id, nhso_seq_id, update_datetime, promote_visit, last_check_datetime)
                    VALUES (%s, %s, %s, NOW(), 'N', NOW())
                    """,
                    (vn, ovst_seq_id, ovst_seq_id),
                )

                cur.execute(
                    """
                    UPDATE ovst_seq
                       SET pcu_person_id = %s,
                           update_datetime = NOW(),
                           last_check_datetime = NOW()
                     WHERE vn = %s
                    """,
                    (person_id, vn),
                )

                cur.execute(
                    """
                    INSERT INTO vn_stat
                        (vn, hn, pdx, lastvisit, dx_doctor,
                         dx0, dx1, dx2, dx3, dx4, dx5,
                         sex, age_y, age_m, age_d, aid, moopart, pttype, spclty, vstdate,
                         pcode, hcode, hospmain, hospsub, pttypeno, cid)
                    VALUES (%s,%s,'',%s,%s,
                            '','','','','','',
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s)
                    """,
                    (
                        vn, hn, 0, doctor,
                        sex, age_y, age_m, age_d, aid, moopart, pttype, spclty, vstdate,
                        pcode, hcode, pttype_hospmain, pttype_hospsub, pttype_no, cid,
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO opdscreen
                        (hos_guid, vn, hn, vstdate, vsttime, bw, height, waist,
                         bps, bpd, pulse, temperature, cc)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (uid2, vn, hn, vstdate, vsttime, bw, height, waist,
                     bps, bpd, pulse, temperature, cc),
                )

                cur.execute(
                    """
                    UPDATE opdscreen
                       SET bmi = CASE
                                   WHEN height IS NULL OR height = 0 THEN NULL
                                   ELSE ROUND((bw / POWER((height / 100.0), 2))::numeric, 3)
                                 END,
                           cc = %s
                     WHERE hos_guid = %s
                    """,
                    (cc, uid2),
                )

                cur.execute(
                    """
                    INSERT INTO opitemrece
                        (hos_guid, vn, hn, icode, qty, unitprice, vstdate, vsttime,
                         staff, item_no, last_modified, sum_price, pttype, income, paidst)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s)
                    """,
                    (uid2, vn, hn, icode, 1, price, vstdate, vsttime,
                     staff, 1, price, pttype, '12', '02'),
                )

                cur.execute(
                    """
                    UPDATE opitemrece
                       SET rxdate = %s,
                           sub_type = '3',
                           cost = 0,
                           node_id = '',
                           last_modified = NOW()
                     WHERE hos_guid = %s
                    """,
                    (vstdate, uid2),
                )

                cur.execute(
                    """
                    INSERT INTO opitemrece_summary
                        (vn, rxdate, icode, income, qty, sum_price, department,
                         hos_guid, opitemrece_id, opitemrece_did, hos_guid_ext)
                    VALUES (%s,%s,%s,'12',1,%s,'OPD',%s,NULL,'',NULL)
                    """,
                    (vn, vstdate, icode, price, uid2),
                )

                cur.execute("DELETE FROM incoth WHERE vn = %s", (vn,))

                cur.execute(
                    """
                    INSERT INTO incoth
                        (vn, billdate, billtime, hn, incdate, inctime, income, paidst,
                         rcpno, rcptamt, "user", computer, finance_number, porder,
                         discount, verify, pttype, hos_guid, hos_guid_ext)
                    VALUES (%s,%s,%s,%s,%s,%s,'12','02',
                            NULL,%s,NULL,NULL,NULL,NULL,
                            NULL,'N',%s,NULL,NULL)
                    """,
                    (vn, vstdate, vsttime, hn, vstdate, vsttime, price, pttype),
                )

                cur.execute(
                    """
                    INSERT INTO inc_opd_stat
                        (vn, hn, vstdate, pttype, pcode,
                         inc01, inc02, inc03, inc04, inc05, inc06, inc07, inc08, inc09,
                         inc10, inc11, inc12, inc13, inc14, inc15, inc16, inc17,
                         income, inc_drug, inc_nondrug,
                         uinc01, uinc02, uinc03, uinc04, uinc05, uinc06, uinc07, uinc08, uinc09,
                         uinc10, uinc11, uinc12, uinc13, uinc14, uinc15, uinc16, uinc17,
                         uincome, uinc_drug, uinc_nondrug, hos_guid)
                    VALUES (%s,%s,%s,%s,NULL,
                            0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,
                            0,0,0,
                            0,0,0,0,0,0,0,0,0,
                            0,0,%s,0,0,0,0,0,
                            %s,0,0,NULL)
                    """,
                    (vn, hn, vstdate, pttype, price, price),
                )

                cur.execute(
                    """
                    INSERT INTO fbshistory
                        (vn, hn, fbslevel, fbs1mo, fbs2mo, fbs3mo, fbs4mo, fbs5mo, fbs6mo, hos_guid)
                    VALUES (%s, %s, NULL, 0, 0, 0, 0, 0, 0, NULL)
                    """,
                    (vn, hn),
                )

                cur.execute(
                    """
                    UPDATE vn_stat
                       SET income = %s,
                           paid_money = 0,
                           remain_money = 0,
                           uc_money = %s,
                           item_money = %s,
                           inc12 = %s,
                           inc_drug = 0,
                           inc_nondrug = 0,
                           pt_subtype = %s,
                           ym = to_char(%s::date, 'YYYY-MM'),
                           ill_visit = 'Y',
                           old_diagnosis = 'N',
                           debt_id_list = ''
                     WHERE vn = %s
                    """,
                    (price, price, price, price, pt_subtype, vstdate, vn),
                )

                cur.execute("INSERT INTO dt_list (vn) VALUES (%s)", (vn,))

                cur.execute(
                    "UPDATE patient SET last_visit = %s, mobile_phone_number = %s WHERE cid = %s",
                    (vstdate, mobile, cid),
                )

                cur.execute(
                    """
                    INSERT INTO visit_pttype
                        (vn, pttype, staff, hospmain, hospsub, pttypeno,
                         update_datetime, pttype_note, claim_code, auth_code)
                    VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s)
                    """,
                    (
                        vn, pttype, staff, pttype_hospmain, pttype_hospsub,
                        pttype_no, claim_type, claim_code, claim_code,
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO ovstdiag
                        (ovst_diag_id, vn, icd10, hn, vstdate, vsttime, diagtype,
                         icd103, hcode, doctor, episode, ext_code, hos_guid, dep_flag,
                         ovst_oper_type, staff, dx_guid, lock_dx, dx_code_note,
                         ovstdiag_severe_type_id, diag_no, update_datetime,
                         confirm, confirm_staff, opi_guid, sct_id)
                    VALUES (%s,%s,%s,%s,%s,%s,'1',
                            NULL,NULL,%s,NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,NULL,NULL,
                            NULL,NULL,NOW(),
                            NULL,NULL,NULL,NULL)
                    """,
                    (ovst_diag_id, vn, dx_code, hn, vstdate, vsttime, doctor),
                )

                cur.execute(
                    """
                    UPDATE ovst_seq
                       SET update_datetime = NOW(),
                           last_check_datetime = NOW()
                     WHERE vn = %s
                    """,
                    (vn,),
                )

                cur.execute(
                    "UPDATE vn_stat SET pdx = %s, main_pdx = %s WHERE vn = %s",
                    (dx_code, main_pdx, vn),
                )

                cur.execute("DELETE FROM opi_dispense WHERE hos_guid = %s", (uid2,))

                cur.execute(
                    """
                    INSERT INTO opi_dispense
                        (opi_dispense_id, hos_guid, icode, qty, usage_code, dose,
                         unit_name, frequency_code, time_code, drug_hint_text,
                         modify_datetime, modify_staff, modify_computer, print_sticker,
                         price, sp_use, usage_unit_code, doctor,
                         usage_line1, usage_line2, usage_line3, usage_line4,
                         usage_shortlist, usage_lock, med_plan_number, orderstatus,
                         use_rx_pattern, opi_dispense_type_id, opi_dispense_item_type_id,
                         opi_dispense_qty_type_id, opi_dispense_usage_type_id,
                         opi_dispense_his_name, pttype_items_price_id, depcode, shortlist,
                         discount, usage_eng_line1, usage_eng_line2, usage_eng_line3,
                         usage_eng_line4, lang, qty_per_day, finish_date, usage_note,
                         presc_duration_days)
                    VALUES (%s,%s,%s,%s,NULL,NULL,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,%s,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,
                            NULL,NULL,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,NULL,
                            NULL,NULL,NULL,NULL,NULL,
                            NULL)
                    """,
                    (opi_dispense_id, uid2, icode, 1, ''),
                )

                self.conn.commit()
                with open('sql_vst_hos_ok.txt', 'w', encoding='utf-8') as f:
                    f.write(f'openVisitHosxpPg OK vn={vn}')
                cur.close()
                break

            except psycopg2.OperationalError as e:
                try:
                    cur.close()
                except psycopg2.Error:
                    pass
                if attempt == 0:
                    print(f"His-PG connection lost ({e}), retry openVisitHosxp...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                self._rollback_quiet()
                print('visit err', e)
                self.signal.emit({'status': str(e)})
                self._log_err(e, 'openVisitHosxpPg failed')
                result = None
                break
            except psycopg2.Error as e:
                try:
                    cur.close()
                except psycopg2.Error:
                    pass
                self._rollback_quiet()
                print('visit err', e)
                self.signal.emit({'status': str(e)})
                self._log_err(e, 'openVisitHosxpPg failed')
                result = None
                break

        time.sleep(0.1)
        return result

    def updateHosxpOvstKey(self, vn, ovst_key):
        cur = self.execute_with_retry(
            "UPDATE ovst SET ovst_key = %s WHERE vn = %s",
            (ovst_key, vn),
            commit=True,
        )
        if cur is None:
            return None
        cur.close()
        return ovst_key

    def updateVisitHosxp(self, data: dict):
        if not self.ensure_connection():
            print("his-pg not connect")
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
        staff = data['staff']

        _pttype = self.getPttypeFromInscl(sub_inscl) if sub_inscl else None
        pttype = _pttype or patient.get('pttype') or ''

        visit_rights = self.resolve_visit_rights(cid, patient)
        pttype_no = visit_rights['pttype_no']
        pttype_hospmain = data.get('hospmain') or visit_rights['pttype_hospmain']
        pttype_hospsub = data.get('hospsub') or visit_rights['pttype_hospsub']

        if str(pttype_no) == 'None':
            pttype_no = ''

        vn = data['vn']
        ovstost = '99'

        for attempt in range(2):
            if not self.ensure_connection():
                print("his-pg not connect")
                return None
            cur = self.conn.cursor()
            try:
                cur.execute(
                    "SELECT pt_subtype FROM pt_subtype WHERE pcu IS NOT NULL LIMIT 1"
                )
                pt_row = cur.fetchone()
                pt_subtype = pt_row[0] if pt_row else None

                cur.execute(
                    """
                    UPDATE ovst
                       SET pttype = %s, pttypeno = %s, pt_subtype = %s, ovstost = %s
                     WHERE vn = %s
                    """,
                    (pttype, pttype_no, pt_subtype, ovstost, vn),
                )

                cur.execute(
                    "UPDATE vn_stat SET pttype = %s WHERE vn = %s", (pttype, vn)
                )

                cur.execute(
                    "UPDATE patient SET mobile_phone_number = %s WHERE cid = %s",
                    (mobile, cid),
                )

                # REPLACE INTO → INSERT ON CONFLICT (requires unique constraint on vn)
                cur.execute(
                    """
                    INSERT INTO visit_pttype
                        (vn, pttype, staff, hospmain, hospsub, pttypeno,
                         update_datetime, pttype_note, claim_code, auth_code)
                    VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s)
                    ON CONFLICT (vn) DO UPDATE SET
                        pttype = EXCLUDED.pttype,
                        staff = EXCLUDED.staff,
                        hospmain = EXCLUDED.hospmain,
                        hospsub = EXCLUDED.hospsub,
                        pttypeno = EXCLUDED.pttypeno,
                        update_datetime = NOW(),
                        pttype_note = EXCLUDED.pttype_note,
                        claim_code = EXCLUDED.claim_code,
                        auth_code = EXCLUDED.auth_code
                    """,
                    (
                        vn, pttype, staff, pttype_hospmain, pttype_hospsub,
                        pttype_no, claim_type, claim_code, claim_code,
                    ),
                )

                self.conn.commit()
                cur.close()
                return vn

            except psycopg2.OperationalError as e:
                try:
                    cur.close()
                except psycopg2.Error:
                    pass
                if attempt == 0:
                    print(f"His-PG connection lost ({e}), retry updateVisitHosxp...")
                    self.reconnect()
                    time.sleep(0.5)
                    continue
                self._rollback_quiet()
                print('update visit', e)
                self.signal.emit({'status': str(e)})
                self._log_err(e, 'updateVisitHosxpPg failed')
                return None
            except psycopg2.Error as e:
                try:
                    cur.close()
                except psycopg2.Error:
                    pass
                self._rollback_quiet()
                print('update visit', e)
                self.signal.emit({'status': str(e)})
                self._log_err(e, 'updateVisitHosxpPg failed')
                return None

        return None

    def _rollback_quiet(self):
        try:
            if self.conn is not None and not self.conn.closed:
                self.conn.rollback()
        except psycopg2.Error:
            pass

    def _log_err(self, err, note: str):
        try:
            with open('visit_err.txt', 'a+', encoding='utf-8') as f:
                f.write(f"{note}: {err}\n")
        except OSError:
            pass


if __name__ == '__main__':
    print('main')
    his = His2Pg()
    print(his.his_is_connected())
