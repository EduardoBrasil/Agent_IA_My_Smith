import unittest
import discord_bot
import release_handler

class TestImports(unittest.TestCase):
    def test_import_discord_bot(self):
        self.assertIsNotNone(discord_bot)

    def test_import_release_handler(self):
        self.assertIsNotNone(release_handler)

if __name__ == '__main__':
    unittest.main()
