# Setting Collection

เอกสารรายการตัวแปรที่เก็บใน QSettings และ `.env` ของแอปพลิเคชัน PlkPlatform

---

## Database Connection Settings

ตัวแปรเหล่านี้เก็บค่าการเชื่อมต่อฐานข้อมูล HIS และถูกกรอกผ่านหน้าจอ **File → Setting**

| Key | ค่าเริ่มต้น | แหล่งที่มา | คำอธิบาย |
|-----|-----------|-----------|---------|
| `DB_TYPE` | `mysql` | `.env` / ผู้ใช้กรอก | ประเภทฐานข้อมูล (`mysql` หรือ `postgres`) |
| `DB_HOST` | *(ว่าง)* | `.env` / ผู้ใช้กรอก | ที่อยู่เซิร์ฟเวอร์ฐานข้อมูล |
| `DB_PORT` | `3306` (MySQL) / `5432` (PG) | `.env` / ผู้ใช้กรอก | พอร์ตเชื่อมต่อ |
| `DB_USER` | *(ว่าง)* | `.env` / ผู้ใช้กรอก | ชื่อผู้ใช้ฐานข้อมูล |
| `DB_PASSWORD` | *(ว่าง)* | `.env` / ผู้ใช้กรอก | รหัสผ่านฐานข้อมูล |
| `DB_NAME` | *(ว่าง)* | `.env` / ผู้ใช้กรอก | ชื่อ database/schema |
| `DB_CHARSET` | `utf8mb4` | `.env` / ผู้ใช้กรอก | charset สำหรับ MySQL |
| `HIS_VENDOR` | `hosxp_pcu` | `.env` | ระบบ HIS (`hosxp`, `hosxp_pcu`, `jhcis`) |

---

## Auto-Generated Settings

ตัวแปรเหล่านี้ถูกสร้างโดยอัตโนมัติจากระบบ

| Key | แหล่งที่มา | คำอธิบาย |
|-----|-----------|---------|
| `hoscode` | ดึงจากฐานข้อมูล HIS เมื่อ **Test Connection** สำเร็จ | รหัสหน่วยบริการ 5 หลัก (ดึงจากตาราง `opdconfig` หรือ `hospital`) |

### วิธีดึง hoscode

เมื่อผู้ใช้กด **ทดสอบการเชื่อมต่อ** ใน HisSetting_dlg และเชื่อมต่อสำเร็จ:

1. ระบบจะ query ฐานข้อมูลตามลำดับ:
   - `SELECT hospitalcode AS hoscode FROM opdconfig LIMIT 1`
   - `SELECT hospcode FROM hospital LIMIT 1`
2. หากพบค่า จะบันทึกลง QSettings ด้วย key `hoscode`
3. แสดงผลรหัสหน่วยบริการในข้อความแจ้งเตือนความสำเร็จ

---

## Priority Order

การอ่านค่า settings มีลำดับความสำคัญดังนี้:

```
QSettings (Windows Registry) → .env file → hardcoded defaults
```

- **QSettings** มีลำดับสูงสุด — ค่าที่บันทึกผ่าน `save_settings()` หรือ `settings.setValue()`
- **.env file** ใช้เป็น fallback หากไม่มีใน QSettings
- **hardcoded defaults** ใช้เมื่อไม่มีค่าในทั้งสองแหล่งข้างต้น

---

## Example Usage

```python
from Setting_helper import read_setting, get_settings

# อ่านค่า hoscode
settings = get_settings()
hoscode = settings.value("hoscode", "")

# หรือใช้ helper
host = read_setting("DB_HOST", "localhost")
```

---

## Storage Location

- **QSettings**: Windows Registry (`HKEY_CURRENT_USER\Software\PlkPlatformSetting\PlkPlatformSetting`)
- **.env**: ไฟล์ `.env` ใน root directory ของโปรเจกต์
