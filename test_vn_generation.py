from __future__ import annotations

import unittest
from datetime import datetime as real_datetime
from unittest.mock import patch

from His_lib import His2
from His_lib_pg import His2Pg


class FixedDateTime(real_datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 5, 8, 19, 50, 59, tzinfo=tz)


class FakeCursor:
    def __init__(self, row: dict[str, str | None]):
        self.row = row
        self.closed = False

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class FakeHisMixin:
    vendor = 'hosxp_pcu'

    def __init__(self, latest_vn: str | None = None):
        self.latest_vn = latest_vn
        self.executed_sql: list[str] = []

    def execute_with_retry(self, sql, *args, **kwargs):
        self.executed_sql.append(sql)
        return FakeCursor({'latest_vn': self.latest_vn})

    def reserve_generated_vn(self, vn: str) -> None:
        self.latest_vn = vn


class FakeHis(FakeHisMixin, His2):
    pass


class FakeHisPg(FakeHisMixin, His2Pg):
    pass


class VisitNumberGenerationTests(unittest.TestCase):
    MODULE_BY_CLASS = {
        FakeHis: "His_lib",
        FakeHisPg: "His_lib_pg",
    }

    def test_single_visit_uses_save_datetime_when_no_vn_exists_today(self) -> None:
        for cls in (FakeHis, FakeHisPg):
            with self.subTest(cls=cls.__name__):
                his = cls()
                with patch(f"{self.MODULE_BY_CLASS[cls]}.datetime", FixedDateTime):
                    vn = his.createVisitNumber()

                self.assertEqual(vn, "690508195059")

    def test_single_visit_adds_one_second_from_latest_vn_when_latest_is_ahead(self) -> None:
        for cls in (FakeHis, FakeHisPg):
            with self.subTest(cls=cls.__name__):
                his = cls("690508195959")
                with patch(f"{self.MODULE_BY_CLASS[cls]}.datetime", FixedDateTime):
                    vn = his.createVisitNumber()

                self.assertEqual(vn, "690508200000")

    def test_group_visit_numbers_increment_without_second_or_minute_loop(self) -> None:
        expected = [
            "690508195059",
            "690508195100",
            "690508195101",
            "690508195102",
            "690508195103",
        ]

        for cls in (FakeHis, FakeHisPg):
            with self.subTest(cls=cls.__name__):
                his = cls()
                generated: list[str] = []
                with patch(f"{self.MODULE_BY_CLASS[cls]}.datetime", FixedDateTime):
                    for _ in expected:
                        vn = his.createVisitNumber()
                        generated.append(vn)
                        his.reserve_generated_vn(vn)

                self.assertEqual(generated, expected)
                self.assertEqual(len(his.executed_sql), len(expected))


if __name__ == "__main__":
    unittest.main()
