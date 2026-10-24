# iPhone Photo & Video Transfer (Windows)

Moves everything under the iPhone's `DCIM` (photos, videos, `.AAE` edit files) into one folder.
Each file is copied, size-verified, then deleted from the iPhone (cut and paste). Name clashes
keep both files: `IMG_0001.JPG`, `IMG_0001_1.JPG`, `IMG_0001_2.JPG`...

## Use
1. Install Python 3.10+ for Windows, then `pip install -r requirements.txt`.
2. Unlock the iPhone, connect by USB, tap **Trust**. Keep it unlocked during transfer.
3. `python app.py`, choose the destination folder, click **Start**.

Try without a phone: `python app.py --demo C:\some\test\folder` (uses that folder as the "phone").
Run tests: `python -m unittest discover tests`.

## Notes
- If a copy fails or the size doesn't match, that file is **not** deleted.
- Turn off iCloud "Optimize iPhone Storage" or originals may be downloaded slowly or not at all.
- The Windows/iPhone part was written without access to a real iPhone, so test with a few photos first.
