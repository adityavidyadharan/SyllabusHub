import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

// Initialize Supabase Client
const supabase = createClient(
  "https://tsbrojrazwcsjqzvnopi.supabase.co", // Replace with your Supabase URL
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw" // Replace with your Supabase API Key
);
function ViewFiles() {
    const [files, setFiles] = useState<{ courseid: string; subname: string; credits: number; fileurl: string }[]>([]);
  
    useEffect(() => {
      const fetchFiles = async () => {
        const { data, error } = await supabase.from("uploads").select("*");
  
        if (error) {
          console.error("Error fetching files:", error);
        } else {
          console.log("Fetched files:", data); // ✅ Debugging log
          setFiles(data);
        }
      };
  
      fetchFiles();
    }, []);
  
    return (
      <div>
        <h2>Uploaded Files</h2>
        <ul>
          {files.map((file, index) => (
            <li key={index}>
              <strong>{file.courseid} - {file.subname} ({file.credits} credits)</strong><br />
              <a href={file.fileurl} target="_blank" rel="noopener noreferrer">
                View File
              </a>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  
  export default ViewFiles;
  

    