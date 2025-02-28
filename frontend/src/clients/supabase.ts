// supabaseClient.ts
import { createClient } from "@supabase/supabase-js";
import { Database } from "../types/db";

const supabaseUrl = "https://tsbrojrazwcsjqzvnopi.supabase.co";
const supabaseAnonKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw";

const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: { persistSession: true }, // ✅ Ensures session persistence
});

export { supabase };
