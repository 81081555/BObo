import unittest

from app import resolve_static_file


class AppRouteTests(unittest.TestCase):
    def test_root_serves_index(self):
        target = resolve_static_file('/')
        self.assertIsNotNone(target)
        self.assertEqual(target.name, 'index.html')

    def test_room_path_falls_back_to_index(self):
        target = resolve_static_file('/room/ABC123')
        self.assertIsNotNone(target)
        self.assertEqual(target.name, 'index.html')

    def test_unknown_asset_still_404(self):
        target = resolve_static_file('/assets/not-found.js')
        self.assertIsNone(target)


if __name__ == '__main__':
    unittest.main()
