# frontend/services/HouseServices.py

import threading
import requests
from PyQt6.QtCore import pyqtSignal, QObject

# Global cache — same as your original
image_cache = {}
image_in_progress = set()


class HouseService(QObject):
    houses_fetched = pyqtSignal(list)

    def fetch_houses(self, token: str = None):
        def worker():
            url = "http://127.0.0.1:8000/api/house/houses/"
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    houses = data.get("results", data) if isinstance(data, dict) else data
                    self.houses_fetched.emit(houses)
                else:
                    self.houses_fetched.emit([])
            except Exception as e:
                print("[HouseService] Error:", e)
                self.houses_fetched.emit([])

        threading.Thread(target=worker, daemon=True).start()

    def load_image_async(self, image_url: str, card):
        """Uses your original working logic — nothing fancy"""
        if not image_url:
            print(f"[HouseService] No image URL provided")
            return

        print(f"[HouseService] Loading image from: {image_url}")

        # FIXED: Correct IP address from 127.0.0.0.1 to 127.0.0.1
        if image_url.startswith("/"):
            image_url = f"http://127.0.0.1:8000{image_url}"
            print(f"[HouseService] Fixed URL: {image_url}")

        # Cache hit — use your working method
        if image_url in image_cache:
            print(f"[HouseService] Cache hit for: {image_url}")
            card.set_image(image_cache[image_url])
            return

        if image_url in image_in_progress:
            print(f"[HouseService] Already downloading: {image_url}")
            return
        
        image_in_progress.add(image_url)
        print(f"[HouseService] Starting download for: {image_url}")

        def download():
            try:
                r = requests.get(image_url, timeout=10)
                print(f"[HouseService] Download status: {r.status_code}")
                if r.status_code == 200:
                    data = r.content
                    print(f"[HouseService] Downloaded {len(data)} bytes")
                    image_cache[image_url] = data
                    # YOUR ORIGINAL METHOD — WORKS PERFECTLY
                    card.set_image(data)
                else:
                    print(f"[HouseService] Failed to download: {r.status_code}")
                    # Try fallback
                    card.set_image(b'')
            except Exception as e:
                print(f"[HouseService] Download failed: {e}")
                # Try fallback
                card.set_image(b'')
            finally:
                image_in_progress.discard(image_url)
                print(f"[HouseService] Finished download for: {image_url}")

        threading.Thread(target=download, daemon=True).start()
