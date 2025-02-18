from supabase import create_client, Client
import json

url = "https://tsbrojrazwcsjqzvnopi.supabase.co"
with open("backend/config/SupabaseSA.json") as f:
    key = json.load(f)["service_role"]

supabase: Client = create_client(url, key)