from __future__ import annotations

import argparse
import re
import time
import uuid
from datetime import date, datetime
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor

from Setting_helper import load_his_settings


BASE_DIR = Path(__file__).resolve().parent
DOCS_CONFIG = BASE_DIR / "docs" / "hosxp_pcu.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open HOSxP PCU visit by CID and visit date."
    )
    parser.add_argument("cid", help="13-digit citizen ID")
    parser.add_argument("vst_date", help="Visit date in YYYY-MM-DD")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate SQL file only, do not execute.",
    )
    return parser.parse_args()


def parse_docs_config(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    if not path.exists():
        return config

    pattern = re.compile(r"^\s*-\s*(host|port|user|password|db)\s*=\s*(.+?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.groups()
        mapped_key = "database" if key == "db" else key
        config[mapped_key] = value.strip()
    return config


def load_config() -> dict[str, str | int]:
    try:
        config = load_his_settings(BASE_DIR)
    except Exception:
        config = {}

    docs_config = parse_docs_config(DOCS_CONFIG)
    merged = {
        "host": str(config.get("host") or docs_config.get("host") or ""),
        "port": int(config.get("port") or docs_config.get("port") or 3306),
        "user": str(config.get("user") or docs_config.get("user") or ""),
        "password": str(config.get("password") or docs_config.get("password") or ""),
        "database": str(config.get("database") or docs_config.get("database") or ""),
        "charset": str(config.get("charset") or "utf8mb4"),
    }
    missing = [key for key in ("host", "user", "database") if not merged[key]]
    if missing:
        raise RuntimeError(f"Missing DB config: {', '.join(missing)}")
    return merged


def sql_quote(value: object) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def connect_db(config: dict[str, str | int]) -> pymysql.Connection:
    return pymysql.connect(
        host=str(config["host"]),
        port=int(config["port"]),
        user=str(config["user"]),
        password=str(config["password"]),
        database=str(config["database"]),
        charset=str(config["charset"]),
        cursorclass=DictCursor,
        autocommit=False,
    )


def fetch_one(cur: pymysql.cursors.Cursor, sql: str, args: tuple = ()) -> dict | None:
    cur.execute(sql, args)
    return cur.fetchone()


def fetch_scalar(cur: pymysql.cursors.Cursor, sql: str, args: tuple = ()) -> object:
    cur.execute(sql, args)
    row = cur.fetchone()
    if not row:
        return None
    return next(iter(row.values()))


def compute_age(birthday: date | None, visit_date: date) -> tuple[int, int, int]:
    if not birthday:
        return 0, 0, 0
    all_days = visit_date - birthday
    age_y = int(all_days.days / 365)
    age_m = int((all_days.days % 365) / 30)
    age_d = (all_days.days % 365) % 30
    return age_y, age_m, age_d


def create_visit_number(cur: pymysql.cursors.Cursor, visit_date: date) -> tuple[str, str]:
    prefix = f"{(visit_date.year + 543) % 100:02d}{visit_date.month:02d}{visit_date.day:02d}"
    while True:
        now = datetime.now()
        vn = f"{prefix}{now:%H%M%S}"
        exists = fetch_scalar(cur, "select count(*) as c from ovst where vn = %s", (vn,))
        if int(exists or 0) == 0:
            return vn, now.strftime("%H:%M:%S")
        time.sleep(1.1)


def load_patient_context(cur: pymysql.cursors.Cursor, cid: str, visit_date: date) -> dict[str, str]:
    patient = fetch_one(
        cur,
        """
        select *
        from patient
        where cid = %s
        limit 1
        """,
        (cid,),
    )
    if not patient:
        raise RuntimeError(f"Patient not found for CID {cid}")

    person = fetch_one(
        cur,
        """
        select person_id, pttype, pttype_no, pttype_hospmain, pttype_hospsub, age_y, age_m, age_d
        from person
        where patient_hn = %s or cid = %s
        order by patient_hn = %s desc, person_id desc
        limit 1
        """,
        (patient["hn"], cid, patient["hn"]),
    ) or {}

    latest_visit = fetch_one(
        cur,
        """
        select
            o.vn,
            o.pttype,
            o.pttypeno,
            o.hospmain,
            o.hospsub,
            o.doctor,
            o.staff,
            o.cur_dep,
            o.spclty,
            vs.pcode,
            vs.hcode
        from ovst o
        left join vn_stat vs on vs.vn = o.vn
        where o.hn = %s
        order by o.vstdate desc, o.vn desc
        limit 1
        """,
        (patient["hn"],),
    ) or {}

    pttype = str(
        latest_visit.get("pttype")
        or patient.get("pttype")
        or person.get("pttype")
        or ""
    ).strip()

    pttype_no = str(
        latest_visit.get("pttypeno")
        or person.get("pttype_no")
        or ""
    ).strip()
    hospmain = str(
        latest_visit.get("hospmain")
        or person.get("pttype_hospmain")
        or ""
    ).strip()
    hospsub = str(
        latest_visit.get("hospsub")
        or person.get("pttype_hospsub")
        or ""
    ).strip()

    pcode_row = fetch_one(
        cur,
        "select pcode from pttype where pttype = %s limit 1",
        (pttype,),
    ) or {}
    pcode = str(pcode_row.get("pcode") or latest_visit.get("pcode") or "").strip()
    hcode = str(latest_visit.get("hcode") or hospsub or "").strip()

    doctor = str(latest_visit.get("doctor") or "0010").strip()
    staff = str(latest_visit.get("staff") or "sa").strip()
    dep = str(latest_visit.get("cur_dep") or "014").strip()
    spclty = str(latest_visit.get("spclty") or "01").strip()

    age_y, age_m, age_d = compute_age(patient.get("birthday"), visit_date)
    if not any((age_y, age_m, age_d)):
        age_y = int(person.get("age_y") or 0)
        age_m = int(person.get("age_m") or 0)
        age_d = int(person.get("age_d") or 0)

    chwpart = str(patient.get("chwpart") or "")
    amppart = str(patient.get("amppart") or "")
    tmbpart = str(patient.get("tmbpart") or "")
    aid = f"{chwpart}{amppart}{tmbpart}"

    return {
        "cid": cid,
        "hn": str(patient.get("hn") or ""),
        "fullname": " ".join(
            filter(
                None,
                [
                    str(patient.get("pname") or "").strip(),
                    str(patient.get("fname") or "").strip(),
                    str(patient.get("lname") or "").strip(),
                ],
            )
        ).strip(),
        "sex": str(patient.get("sex") or ""),
        "age_y": str(age_y),
        "age_m": str(age_m),
        "age_d": str(age_d),
        "aid": aid,
        "moopart": str(patient.get("moopart") or ""),
        "pttype": pttype,
        "pttype_no": pttype_no,
        "hospmain": hospmain,
        "hospsub": hospsub,
        "pcode": pcode,
        "hcode": hcode,
        "person_id": str(person.get("person_id") or ""),
        "doctor": doctor,
        "staff": staff,
        "dep": dep,
        "spclty": spclty,
        "mobile": str(patient.get("mobile_phone_number") or patient.get("hometel") or ""),
    }


def build_sql(ctx: dict[str, str], visit_date: str, visit_time: str, vn: str) -> list[str]:
    guid1 = "{" + str(uuid.uuid4()).upper() + "}"
    guid2 = "{" + str(uuid.uuid4()).upper() + "}"
    cc = "ให้บริการ telemedicine"
    claim_type = ""
    claim_code = ""
    dx = "Z718"
    main_pdx = "Z71"
    i_price_code = "3001647"
    o_price_code = "3000002"

    return [
        f"set @visit_date = {sql_quote(visit_date)}",
        f"set @visit_time = {sql_quote(visit_time)}",
        f"set @vn = {sql_quote(vn)}",
        f"set @cid = {sql_quote(ctx['cid'])}",
        f"set @claim_type = {sql_quote(claim_type)}",
        f"set @claim_code = {sql_quote(claim_code)}",
        f"set @cc = {sql_quote(cc)}",
        f"set @hn = {sql_quote(ctx['hn'])}",
        f"set @sex = {sql_quote(ctx['sex'])}",
        f"set @age_y = {sql_quote(ctx['age_y'])}",
        f"set @age_m = {sql_quote(ctx['age_m'])}",
        f"set @age_d = {sql_quote(ctx['age_d'])}",
        f"set @aid = {sql_quote(ctx['aid'])}",
        f"set @moopart = {sql_quote(ctx['moopart'])}",
        f"set @pttype = {sql_quote(ctx['pttype'])}",
        f"set @pttypeno = {sql_quote(ctx['pttype_no'])}",
        f"set @hospmain = {sql_quote(ctx['hospmain'])}",
        f"set @hospsub = {sql_quote(ctx['hospsub'])}",
        f"set @pcode = {sql_quote(ctx['pcode'])}",
        f"set @hcode = {sql_quote(ctx['hcode'])}",
        f"set @person_id = {sql_quote(ctx['person_id'])}",
        "set @vstdate = @visit_date",
        "set @vsttime = @visit_time",
        f"set @guid1 = {sql_quote(guid1)}",
        f"set @guid2 = {sql_quote(guid2)}",
        "set @ovst_seq_id = (select get_serialnumber('ovst_seq_id'))",
        "set @nhso_seq_id = cast(@ovst_seq_id as char character set utf8)",
        "set @ovst_q_today = concat('ovst-q-',left(@vn,6))",
        "set @ovst_q = (select get_serialnumber(@ovst_q_today))",
        f"set @doctor = {sql_quote(ctx['doctor'])}",
        f"set @staff = {sql_quote(ctx['staff'])}",
        f"set @dep = {sql_quote(ctx['dep'])}",
        f"set @spclty = {sql_quote(ctx['spclty'])}",
        "set @ovstlist = '05'",
        "set @ovstost = '99'",
        "set @visit_type = (select if((@visit_time >= '16:30:00') or (@visit_time <= '08:30:00') or (@visit_date in (select holiday_date from holiday)),'O','I'))",
        "set @lastvisit = 0",
        "set @pt_subtype = (select pt_subtype from pt_subtype where pcu is not null limit 1)",
        "insert into vn_insert (vn) values (@vn)",
        "insert into vn_stat_signature (vn) values (@vn)",
        """
        insert into ovst
          (hos_guid,vn,hn,vstdate,vsttime,doctor,hospmain,hospsub,oqueue,ovstist,ovstost,pttype,pttypeno,spclty,cur_dep,pt_subtype,visit_type,staff)
        values
          (@guid1,@vn,@hn,@vstdate,@vsttime,@doctor,@hospmain,@hospsub,@ovst_q,@ovstlist,@ovstost,@pttype,@pttypeno,@spclty,@dep,@pt_subtype,@visit_type,@staff)
        """.strip(),
        """
        insert into ovst_seq
          (vn,seq_id,nhso_seq_id,update_datetime,promote_visit,last_check_datetime)
        values
          (@vn,@ovst_seq_id,@nhso_seq_id,now(),'N',now())
        """.strip(),
        """
        update ovst_seq
        set pcu_person_id = @person_id,
            update_datetime = now(),
            last_check_datetime = now()
        where vn = @vn
        """.strip(),
        """
        insert into vn_stat
          (vn,hn,pdx,lastvisit,dx_doctor,dx0,dx1,dx2,dx3,dx4,dx5,sex,age_y,age_m,age_d,aid,moopart,pttype,spclty,vstdate,pcode,hcode,hospmain,hospsub,pttypeno,cid)
        values
          (@vn,@hn,'',@lastvisit,@doctor,'','','','','','',@sex,@age_y,@age_m,@age_d,@aid,@moopart,@pttype,@spclty,@vstdate,@pcode,@hcode,@hospmain,@hospsub,@pttypeno,@cid)
        """.strip(),
        "set @bw = (select bw from opdscreen where hn = @hn and bw > 0 and vn < @vn order by vn desc limit 1)",
        "set @height = (select height from opdscreen where hn = @hn and height > 0 and vn < @vn order by vn desc limit 1)",
        "set @waist = (select waist from opdscreen where hn = @hn and waist > 0 and vn < @vn order by vn desc limit 1)",
        "set @bps = (select bps from opdscreen where hn = @hn and vn < @vn order by vn desc limit 1)",
        "set @bpd = (select bpd from opdscreen where hn = @hn and vn < @vn order by vn desc limit 1)",
        "set @pulse = (select pulse from opdscreen where hn = @hn and vn < @vn order by vn desc limit 1)",
        "set @temperature = '37.0'",
        """
        insert into opdscreen
          (hos_guid,vn,hn,vstdate,vsttime,bw,height,waist,bps,bpd,pulse,temperature,cc)
        values
          (@guid2,@vn,@hn,@vstdate,@vsttime,@bw,@height,@waist,@bps,@bpd,@pulse,@temperature,@cc)
        """.strip(),
        """
        update opdscreen
        set bmi = round((bw / power((height / 100), 2)), 3),
            cc = @cc
        where hos_guid = @guid2
        """.strip(),
        f"set @icode = (select if(@visit_type = 'O', {sql_quote(o_price_code)}, {sql_quote(i_price_code)}))",
        "set @price = (select price from nondrugitems where icode = @icode)",
        """
        insert into opitemrece
          (hos_guid,vn,hn,icode,qty,unitprice,vstdate,vsttime,staff,item_no,last_modified,sum_price,pttype,income,paidst)
        values
          (@guid2,@vn,@hn,@icode,1,@price,@vstdate,@vsttime,@staff,1,now(),@price,@pttype,'12','02')
        """.strip(),
        """
        update opitemrece
        set rxdate = @vstdate,
            sub_type = '3',
            cost = 0,
            node_id = '',
            last_modified = now()
        where hos_guid = @guid2
        """.strip(),
        """
        insert into opitemrece_summary
          (vn,rxdate,icode,income,qty,sum_price,department,hos_guid,opitemrece_id,opitemrece_did,hos_guid_ext)
        values
          (@vn,@vstdate,@icode,'12',1,@price,'OPD',@guid2,null,'',null)
        """.strip(),
        "delete from incoth where vn = @vn",
        """
        insert into incoth
          (vn,billdate,billtime,hn,incdate,inctime,income,paidst,rcpno,rcptamt,`user`,computer,finance_number,porder,discount,verify,pttype,hos_guid,hos_guid_ext)
        values
          (@vn,@vstdate,@vsttime,@hn,@vstdate,@vsttime,'12','02',null,@price,null,null,null,null,null,'N',@pttype,null,null)
        """.strip(),
        """
        insert into inc_opd_stat
          (vn,hn,vstdate,pttype,pcode,inc01,inc02,inc03,inc04,inc05,inc06,inc07,inc08,inc09,inc10,inc11,inc12,inc13,inc14,inc15,inc16,inc17,income,inc_drug,inc_nondrug,uinc01,uinc02,uinc03,uinc04,uinc05,uinc06,uinc07,uinc08,uinc09,uinc10,uinc11,uinc12,uinc13,uinc14,uinc15,uinc16,uinc17,uincome,uinc_drug,uinc_nondrug,hos_guid)
        values
          (@vn,@hn,@vstdate,@pttype,null,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,@price,0,0,0,0,0,@price,0,0,null)
        """.strip(),
        """
        insert into fbshistory
          (vn,hn,fbslevel,fbs1mo,fbs2mo,fbs3mo,fbs4mo,fbs5mo,fbs6mo,hos_guid)
        values
          (@vn,@hn,null,0,0,0,0,0,0,null)
        """.strip(),
        """
        update vn_stat
        set income = @price,
            paid_money = 0,
            remain_money = 0,
            uc_money = @price,
            item_money = @price,
            inc12 = @price,
            inc_drug = 0,
            inc_nondrug = 0,
            pt_subtype = @pt_subtype,
            ym = date_format(@vstdate,'%Y-%m'),
            ill_visit = 'Y',
            old_diagnosis = 'N',
            debt_id_list = ''
        where vn = @vn
        """.strip(),
        "insert into dt_list (vn) values (@vn)",
        f"update patient set last_visit = @vstdate, mobile_phone_number = {sql_quote(ctx['mobile'])} where cid = @cid",
        """
        insert into visit_pttype
          (vn,pttype,staff,hospmain,hospsub,pttypeno,update_datetime,pttype_note,claim_code,auth_code)
        values
          (@vn,@pttype,@staff,@hospmain,@hospsub,@pttypeno,now(),@claim_type,@claim_code,@claim_code)
        """.strip(),
        f"set @dx = {sql_quote(dx)}",
        f"set @main_pdx = {sql_quote(main_pdx)}",
        "set @ovst_diag_id = (select get_serialnumber('ovst_diag_id'))",
        "set @opi_dispense_id = (select get_serialnumber('opi_dispense_id'))",
        """
        insert into ovstdiag
          (ovst_diag_id,vn,icd10,hn,vstdate,vsttime,diagtype,icd103,hcode,doctor,episode,ext_code,hos_guid,dep_flag,ovst_oper_type,staff,dx_guid,lock_dx,dx_code_note,ovstdiag_severe_type_id,diag_no,update_datetime,confirm,confirm_staff,opi_guid,sct_id)
        values
          (@ovst_diag_id,@vn,@dx,@hn,@vstdate,@vsttime,'1',null,null,@doctor,null,null,null,null,null,null,null,null,null,null,null,now(),null,null,null,null)
        """.strip(),
        """
        update ovst_seq
        set update_datetime = now(),
            last_check_datetime = now()
        where vn = @vn
        """.strip(),
        """
        update vn_stat
        set pdx = @dx,
            main_pdx = @main_pdx
        where vn = @vn
        """.strip(),
        "delete from opi_dispense where hos_guid = @guid2",
        """
        insert into opi_dispense
          (opi_dispense_id,hos_guid,icode,qty,usage_code,dose,unit_name,frequency_code,time_code,drug_hint_text,modify_datetime,modify_staff,modify_computer,print_sticker,price,sp_use,usage_unit_code,doctor,usage_line1,usage_line2,usage_line3,usage_line4,usage_shortlist,usage_lock,med_plan_number,orderstatus,use_rx_pattern,opi_dispense_type_id,opi_dispense_item_type_id,opi_dispense_qty_type_id,opi_dispense_usage_type_id,opi_dispense_his_name,pttype_items_price_id,depcode,shortlist,discount,usage_eng_line1,usage_eng_line2,usage_eng_line3,usage_eng_line4,lang,qty_per_day,finish_date,usage_note,presc_duration_days)
        values
          (@opi_dispense_id,@guid2,@icode,1,null,null,null,null,null,null,null,null,null,null,null,null,null,'',null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
        """.strip(),
    ]


def write_sql_file(vn: str, cid: str, full_name: str, statements: list[str]) -> Path:
    path = BASE_DIR / f"sql_test_open_visit_{vn}.txt"
    header = [
        f"-- Auto generated by test_open_visit.py",
        f"-- CID: {cid}",
        f"-- VN: {vn}",
        f"-- Patient: {full_name}",
        "",
    ]
    content = "\n".join(header + [stmt.rstrip() + ";" for stmt in statements]) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def execute_statements(conn: pymysql.Connection, statements: list[str]) -> None:
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)


def verify_visit(cur: pymysql.cursors.Cursor, vn: str) -> dict[str, object]:
    ovst = fetch_one(
        cur,
        """
        select vn, hn, ovstist, ovstost, doctor, staff
        from ovst
        where vn = %s
        """,
        (vn,),
    ) or {}
    vn_stat = fetch_one(
        cur,
        """
        select pdx, main_pdx, income, uc_money, item_money, inc12, cid, pcode
        from vn_stat
        where vn = %s
        """,
        (vn,),
    ) or {}
    screen = fetch_one(
        cur,
        """
        select cc, temperature
        from opdscreen
        where vn = %s
        """,
        (vn,),
    ) or {}
    return {
        "vn": vn,
        "hn": ovst.get("hn"),
        "cid": vn_stat.get("cid"),
        "ovstist": ovst.get("ovstist"),
        "ovstost": ovst.get("ovstost"),
        "doctor": ovst.get("doctor"),
        "staff": ovst.get("staff"),
        "pdx": vn_stat.get("pdx"),
        "main_pdx": vn_stat.get("main_pdx"),
        "income": vn_stat.get("income"),
        "uc_money": vn_stat.get("uc_money"),
        "item_money": vn_stat.get("item_money"),
        "inc12": vn_stat.get("inc12"),
        "pcode": vn_stat.get("pcode"),
        "cc": screen.get("cc"),
        "temperature": screen.get("temperature"),
    }


def main() -> None:
    args = parse_args()
    visit_date = datetime.strptime(args.vst_date, "%Y-%m-%d").date()
    config = load_config()

    conn = connect_db(config)
    try:
        with conn.cursor() as cur:
            context = load_patient_context(cur, args.cid, visit_date)
            vn, visit_time = create_visit_number(cur, visit_date)
            statements = build_sql(context, args.vst_date, visit_time, vn)
            sql_path = write_sql_file(vn, args.cid, context["fullname"], statements)

        if args.dry_run:
            print(f"dry_run=1 sql_file={sql_path}")
            print(f"cid={args.cid} hn={context['hn']} vn={vn} visit_date={args.vst_date} visit_time={visit_time}")
            return

        execute_statements(conn, statements)
        conn.commit()

        with conn.cursor() as cur:
            summary = verify_visit(cur, vn)

        print(f"sql_file={sql_path}")
        for key, value in summary.items():
            print(f"{key}={value}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
