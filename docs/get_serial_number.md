# ฟังก์ชัน get_serialnumber

## คำอธิบาย
ฟังก์ชัน `get_serialnumber` เป็นฟังก์ชันในฐานข้อมูล MySQL ที่ใช้สร้างลำดับตัวเลขที่ไม่ซ้ำกัน (sequence number) โดยอิงจากตาราง `serial` ซึ่งเก็บค่าตัวนับสำหรับชื่อต่างๆ

## การทำงาน
1. รับพารามิเตอร์ `param1` ซึ่งเป็นชื่อตัวนับ (เช่น `'ovst_seq_id'` หรือ `'seq_id'`)
2. หาก `param1` เป็น string ว่าง จะถูกแทนที่ด้วย `'test'` (เพื่อป้องกันข้อผิดพลาด)
3. ตรวจสอบว่ามีบันทึกในตาราง `serial` ที่มี `name = param1` และ `serial_no` ไม่เป็น NULL หรือไม่
4. หากไม่มีบันทึกดังกล่าว:
   - ลบบันทึกที่มี `name = param1` และ `serial_no` เป็น NULL ออก (ถ้ามี)
   - เพิ่มบันทึกใหม่ในตาราง `serial` ด้วย `name = param1` และ `serial_no = 0`
5. อัปเดตค่า `serial_no` ในตาราง `serial` โดยเพิ่มขึ้น 1 และคืนค่าใหม่ที่ได้โดยใช้ฟังก์ชัน `LAST_INSERT_ID()`

## ตัวอย่างการใช้งาน
```sql
SELECT hos_07547.get_serialnumber('ovst_seq_id');
```
ผลลัพธ์: คืนค่าตัวเลขถัดไปในลำดับ (เช่น 369484 หากค่าปัจจุบันคือ 369483)

## โครงสร้างตาราง serial
| Field      | Type         | Null | Key | Default | Extra |
|------------|--------------|------|-----|---------|-------|
| name       | varchar(50)  | NO   | PRI |         |       |
| serial_no  | int(11)      | YES  |     | NULL    |       |
| node_id    | char(1)      | YES  |     | NULL    |       |
| hos_guid   | varchar(38)  | YES  | MUL | NULL    |       |
| hos_guid_ext| varchar(64) | YES  | MUL | NULL    |       |

## ความสัมพันธ์กับตารางอื่นๆ
- `ovst_seq.seq_id` อ้างอิงถึงค่าที่ได้จาก `get_serialnumber(...)`
- `ovst.seq_id` (ถ้ามี) จะอ้างอิงกลับไปยัง `ovst_seq.seq_id`
- บางฐานใช้ `serial.name = 'ovst_seq_id'` และบางฐานใช้ `serial.name = 'seq_id'`
- Logic ในโปรแกรมจะเทียบ `serial.serial_no` ของทั้งสอง key กับ `MAX(ovst_seq.seq_id)` แล้วเลือก key ที่ sync กับตาราง `ovst_seq` อยู่จริง
- ถ้า insert ชน unique index `ovst_seq.ix_seq_id` โปรแกรมจะ refresh key แล้วขอ serial ใหม่อีกครั้ง

## หมายเหตุ
- ฟังก์ชันนี้ออกแบบมาให้ปลอดภัยต่อการเรียกพร้อมกันหลายครั้ง (thread-safe) โดยการใช้ `LAST_INSERT_ID()` ในการอัปเดตและคืนค่า
- หากต้องการใช้ตัวนับชื่ออื่น ให้เปลี่ยนพารามิเตอร์เป็นชื่อที่ต้องการ (เช่น `'ovst-dep-q-001-470906'`)
