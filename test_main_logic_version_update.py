import unittest
from unittest.mock import Mock, patch

import Main_logic
from version import VERSION


class VersionUpdateTests(unittest.TestCase):
    def test_post_version_update_uses_requests_json_post(self) -> None:
        self.assertTrue(
            hasattr(Main_logic, "requests"),
            "Main_logic should use the requests package for version update POST",
        )

        response = Mock()
        with patch.object(Main_logic.requests, "post", return_value=response) as post:
            Main_logic.post_version_update(" 07475 ", timeout=7)

        post.assert_called_once_with(
            Main_logic.VERSION_UPDATE_API_URL,
            json={"hoscode": "07475", "version": VERSION},
            timeout=7,
        )
        response.raise_for_status.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
