import os
import tempfile
import unittest

from iphone_transfer.backend_local import LocalBackend
from iphone_transfer.core import transfer


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class TransferTest(unittest.TestCase):
    def test_duplicates_kept_and_source_deleted(self):
        with tempfile.TemporaryDirectory() as phone, tempfile.TemporaryDirectory() as dest:
            write(f"{phone}/100APPLE/IMG_1.JPG", b"a")
            write(f"{phone}/101APPLE/IMG_1.JPG", b"bb")
            write(f"{phone}/101APPLE/IMG_2.MOV", b"ccc")
            write(f"{dest}/IMG_2.MOV", b"existing")
            s = transfer(LocalBackend(phone), dest, True, log=lambda m: None)
            self.assertEqual((s.copied, s.deleted, s.failed, s.renamed), (3, 3, 0, 2))
            self.assertEqual(sorted(os.listdir(dest)),
                             ["IMG_1.JPG", "IMG_1_1.JPG", "IMG_2.MOV", "IMG_2_1.MOV"])
            self.assertEqual([x for _, _, n in os.walk(phone) for x in n], [])

    def test_no_delete_when_disabled(self):
        with tempfile.TemporaryDirectory() as phone, tempfile.TemporaryDirectory() as dest:
            write(f"{phone}/a/X.JPG", b"x")
            transfer(LocalBackend(phone), dest, False, log=lambda m: None)
            self.assertTrue(os.path.exists(f"{phone}/a/X.JPG"))

    def test_failed_copy_is_not_deleted(self):
        class Bad(LocalBackend):
            def fetch(self, f, dest_path):
                write(dest_path, b"")  # truncated copy
        with tempfile.TemporaryDirectory() as phone, tempfile.TemporaryDirectory() as dest:
            write(f"{phone}/a/X.JPG", b"xyz")
            s = transfer(Bad(phone), dest, True, log=lambda m: None)
            self.assertEqual((s.failed, s.deleted), (1, 0))
            self.assertTrue(os.path.exists(f"{phone}/a/X.JPG"))
            self.assertEqual(os.listdir(dest), [])


if __name__ == "__main__":
    unittest.main()
