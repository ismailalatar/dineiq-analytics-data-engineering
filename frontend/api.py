"""API client."""
import requests
import streamlit as st
import pandas as pd


class DineIQAPI:
    def __init__(self, base="http://localhost:5000/api/v1"):
        self.base = base

    def _h(self):
        t = st.session_state.get("token")
        return {"Authorization": f"Bearer {t}"} if t else {}

    def login(self, email, password):
        return requests.post(f"{self.base}/auth/login",
                             json={"email": email, "password": password}, timeout=15)

    def get(self, path, **params):
        return requests.get(f"{self.base}{path}", headers=self._h(),
                            params=params, timeout=30)

    def post(self, path, json=None):
        return requests.post(f"{self.base}{path}", headers=self._h(),
                             json=json, timeout=30)

    def df(self, path, **params):
        r = self.get(path, **params)
        if r.status_code != 200:
            return None
        data = r.json()
        return pd.DataFrame(data) if data else pd.DataFrame()

    def summary(self):
        r = self.get("/analytics/summary")
        return r.json() if r.status_code == 200 else {}
