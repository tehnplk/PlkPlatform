import unittest
from urllib.parse import parse_qs, urlparse

from Chat_logic import build_chat_url
from version import VERSION


class ChatLogicTests(unittest.TestCase):
    def test_build_chat_url_includes_hoscode_and_version_query_strings(self) -> None:
        url = build_chat_url(" 10653 ")

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "platform.plkhealth.go.th")
        self.assertEqual(parsed.path, "/chat/user")
        self.assertEqual(query["hoscode"], ["10653"])
        self.assertEqual(query["version"], [VERSION])


if __name__ == "__main__":
    unittest.main()
