import requests

class ResumeService:
    def __init__(self, base_url, token):
        self.base = base_url.rstrip("/")
        self.h = {"Authorization": f"Bearer {token}", "Accept":"application/json"}

    def add_education(self, data):  return requests.post(f"{self.base}/api/users/resume/education/",  json=data, headers=self.h, timeout=10)
    def add_experience(self, data): return requests.post(f"{self.base}/api/users/resume/experience/", json=data, headers=self.h, timeout=10)
    def add_skill(self, data):      return requests.post(f"{self.base}/api/users/resume/skills/",     json=data, headers=self.h, timeout=10)
    def add_interest(self, data):   return requests.post(f"{self.base}/api/users/resume/interests/",  json=data, headers=self.h, timeout=10)
