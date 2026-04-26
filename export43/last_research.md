# สรุปผลวิจัย Logic Mapping: Vendor DB ไป Standard Files

วันที่วิจัย: 2026-04-26

## ขอบเขตการตรวจ

ตรวจ logic การ mapping ข้อมูลจาก vendor HOSxP PCU ไปยังแฟ้มส่งออกมาตรฐานใน `export43/` โดยอ้างอิงจาก:

- ฐานข้อมูล vendor: `hos_07547`
- ฐานข้อมูลผลส่งออกชั่วคราว: `temp`
- ตารางผลส่งออกตัวอย่าง: `tmp_exp_<run_id>_*`
- run id ที่ใช้เป็น snapshot รอบนี้: `3093`
- source query จาก vendor: `docs/vendor_hos_07547_source_selects.sql`
- credential/context: `.claude/worktrees/exciting-hypatia-bcce5e/docs/hosxp_pcu.md`
- ข้อมูลโครงสร้าง 43 แฟ้มและ HOSxP PCU จาก NotebookLM (`nlm`)

หมายเหตุ: เลข `3093` ใน `tmp_exp_3093_*` เป็น run/export id ที่เปลี่ยนได้เมื่อ vendor export ใหม่ จึงไม่ควร hard-code เป็น baseline ถาวร ให้ใช้ pattern `tmp_exp_<run_id>_*`.

## ผลสรุป

ด้านจำนวนและลำดับ column: ผ่าน เมื่อใช้ `temp.tmp_exp_3093_*` เป็น base

ด้าน logic mapping จาก vendor DB ไป standard files: ผ่านบางส่วน ยังไม่ครบทุกแฟ้ม

กล่าวคือ `export43/*.py` มีโครงสร้างคอลัมน์ตรงกับผล export ใน `temp` แต่ยังมีหลายแฟ้มที่ยังไม่ได้ map logic จริงจากตาราง vendor หรือยังใช้ placeholder query ที่ไม่คืนข้อมูล

## สิ่งที่ตรวจแล้วผ่าน

- พบแฟ้มใน `export43/` ครบ 52 แฟ้ม
- พบตารางผลส่งออกใน `temp.tmp_exp_3093_*` ครบ 52 ตาราง
- จำนวน column ใน `export43/*.py` ตรงกับ `temp.tmp_exp_3093_*` ทุกแฟ้ม
- ลำดับ column ตรงกับ `temp.tmp_exp_3093_*` ทุกแฟ้ม
- query ทุกแฟ้ม execute ตรวจ syntax แบบ `LIMIT 0` กับฐาน `hos_07547` ได้
- เอกสารโครงสร้าง column ถูกสร้างไว้ที่ `export43/files_structure.md`

## กลุ่มที่ Mapping ค่อนข้างถูกทิศทาง

แฟ้ม OPD หลักมี logic ใกล้เคียง vendor source และใช้ตารางต้นทางถูกกลุ่ม:

- `SERVICE`
- `DIAGNOSIS_OPD`
- `DRUG_OPD`
- `CHARGE_OPD`
- `PROCEDURE_OPD`
- `APPOINTMENT`
- `DENTAL`
- `LABFU`
- `CHRONIC`
- `CHRONICFU`

ตาราง vendor ที่ใช้ในกลุ่มนี้สอดคล้องกับ HOSxP PCU:

- `ovst`
- `ovst_seq`
- `patient`
- `person`
- `vn_stat`
- `opdscreen`
- `ovstdiag`
- `opitemrece`
- `drugitems`
- `spclty`
- `clinicmember`
- `clinic`

## ปัญหาหลักที่พบ

### 1. หลายแฟ้มยังเป็น Stub

มีหลายแฟ้มที่ query เป็น `FROM dual WHERE 1=0` ทำให้ไม่ส่งออกข้อมูลเสมอ แม้ vendor source มี query จริง หรือ `temp` มีผลลัพธ์ตัวอย่างแล้ว

ตัวอย่างแฟ้มที่ยังเป็น stub:

- `VILLAGE`
- `SURVEILLANCE`
- `SPECIALPP`
- `WOMEN`
- `FUNCTIONAL`
- `ICF`
- `REHABILITATION`
- `NEWBORNCARE`
- `POSTNATAL`
- `DISABILITY`
- `COMMUNITY_ACTIVITY`
- `COMMUNITY_SERVICE`
- `CARE_REFER`
- `CLINICAL_REFER`
- `DRUG_REFER`
- `INVESTIGATION_REFER`
- `PROCEDURE_REFER`
- `REFER_RESULT`
- `POLICY`
- `DATA_CORRECT`

ผลกระทบ: แฟ้มเหล่านี้ยังไม่ถือว่ามี logic mapping จริง

### 2. บางแฟ้ม Temp มีข้อมูล แต่ Code จะส่งออกว่าง

ตัวอย่างจาก `temp.tmp_exp_3093_*`:

- `VILLAGE` มี 6 แถว แต่ `export43/VILLAGE.py` เป็น stub
- `SURVEILLANCE` มี 1 แถว แต่ `export43/SURVEILLANCE.py` เป็น stub
- `SPECIALPP` มี 64 แถว แต่ `export43/SPECIALPP.py` เป็น stub

นี่เป็นหลักฐานชัดว่า logic mapping ของ code ยังไม่ครบเมื่อเทียบกับผล export vendor

### 3. กลุ่ม PP/MCH ยังใช้ Source ไม่ครบ

vendor source มี query จากตารางเฉพาะของ HOSxP PCU แต่ code ยังไม่ได้ map ครบในหลายแฟ้ม

ตารางที่ควรใช้เติม logic:

- `person_women`
- `person_women_service`
- `person_wbc`
- `person_wbc_service`
- `person_wbc_nutrition`
- `person_wbc_vaccine_detail`
- `person_wbc_post_care`
- `person_anc`
- `person_anc_service`
- `person_anc_preg_care`
- `person_labour`

แฟ้มที่เกี่ยวข้อง:

- `WOMEN`
- `FP`
- `ANC`
- `PRENATAL`
- `POSTNATAL`
- `LABOR`
- `NEWBORN`
- `NEWBORNCARE`
- `EPI`
- `NUTRITION`

### 4. NCDSCREEN ยัง Mapping ไม่ครบ

`NCDSCREEN` มี query แล้ว แต่บาง field ยังปล่อยว่างหรือใช้แหล่งข้อมูลไม่ครบ เช่น:

- `DMFAMILY`
- `HTFAMILY`
- `SBP_2`
- `DBP_2`
- `BSTEST`

vendor source มีข้อมูลจากกลุ่ม:

- `person_dmht_screen_summary`
- `person_dmht_risk_screen_head`
- `person_dmht_nhso_screen`
- `person_ht_risk_bp_screen`

จึงควรใช้กลุ่มนี้เติม mapping ให้ครบกว่าเดิม

### 5. กลุ่ม Refer/Rehab/Functional/ICF ยังไม่ครบ

vendor source มี query จากตาราง:

- `referout`
- `referin`
- `ovst_rehab`
- `ovst_rehab_detail`
- `ovst_functional`
- `ovst_icf`

แต่หลายแฟ้มใน `export43/` ยังเป็น stub จึงควร implement mapping ต่อ

## ข้อสรุปเชิงสถานะ

| ด้านที่ตรวจ | สถานะ | หมายเหตุ |
|---|---|---|
| จำนวน column ตาม `temp` | ผ่าน | ใช้ `tmp_exp_<run_id>_*` เป็น base |
| ลำดับ column ตาม `temp` | ผ่าน | ตรงทุกแฟ้มใน snapshot `3093` |
| Syntax SQL | ผ่าน | ตรวจแบบ `LIMIT 0` ผ่านทุกแฟ้ม |
| Mapping OPD หลัก | ผ่านบางส่วน | ทิศทางถูก แต่ควรตรวจค่า field รายละเอียด |
| Mapping PP/MCH | ยังไม่ครบ | ต้องเติมจาก `person_women`, `person_wbc`, `person_anc` |
| Mapping NCDSCREEN | ยังไม่ครบ | ต้องเติมจาก `person_dmht_*` |
| Mapping Refer/Rehab/ICF/Functional | ยังไม่ครบ | หลายแฟ้มเป็น stub |
| แฟ้ม stub | ไม่ผ่าน logic | ต้อง implement query จริง |

## Priority แนะนำสำหรับการทำต่อ

1. Implement แฟ้มที่ `temp` มีข้อมูลแต่ code เป็น stub ก่อน:
   - `SPECIALPP`
   - `VILLAGE`
   - `SURVEILLANCE`

2. เติมกลุ่ม PP/MCH ที่ vendor source มีข้อมูลชัด:
   - `WOMEN`
   - `POSTNATAL`
   - `NEWBORNCARE`
   - `EPI`
   - `NUTRITION`

3. ปรับ `NCDSCREEN` ให้ใช้ source กลุ่ม `person_dmht_*` เพื่อเติม family history, BP ครั้งที่ 2 และชนิดการตรวจน้ำตาล

4. เติมกลุ่ม rehab/refer:
   - `FUNCTIONAL`
   - `ICF`
   - `REHABILITATION`
   - `REFER_HISTORY`
   - `REFER_RESULT`

## สรุปสุดท้าย

โครงสร้างแฟ้มใน code ตรงกับผล export vendor ใน `temp` แล้ว แต่ logic mapping ยังไม่สมบูรณ์ครบทุกแฟ้ม

สถานะปัจจุบันเหมาะเรียกว่า:

`column-compatible แต่ mapping-incomplete`

