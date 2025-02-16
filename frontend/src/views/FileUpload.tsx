import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { app } from "../firebase/firebase"; // Import Firebase

// Initialize Supabase Client
const supabase = createClient(
    "https://tsbrojrazwcsjqzvnopi.supabase.co", // Replace with your Supabase URL
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw" // Replace with your Supabase API Key
  );

function FileUpload() {
  const [courseNumber, setCourseNumber] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [credits, setCredits] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [fileURL, setFileURL] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);

  const auth = getAuth(app);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUserEmail(user.email);
        setUserName(user.displayName || "Unknown User");
      } else {
        setUserEmail(null);
        setUserName(null);
      }
    });
    return () => unsubscribe();
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!file) {
      setMessage("Please select a file to upload.");
      return;
    }

    if (!userEmail) {
      setMessage("You must be logged in to upload files.");
      return;
    }

    setUploading(true);
    setMessage("");

    const filePath = `course_syllabuses/${Date.now()}-${file.name}`;

    try {
      const { data, error } = await supabase.storage
        .from("Course Syllabuses")
        .upload(filePath, file);

      if (error) throw error;

      const filePublicURL = `https://tsbrojrazwcsjqzvnopi.supabase.co/storage/v1/object/public/Course Syllabuses/${filePath}`;

      const { error: dbError } = await supabase.from("uploads").insert([
        {
          courseid: courseNumber,
          subname: subjectName,
          credits: credits,
          fileurl: filePublicURL,
          uploaded_by_name: userName, 
          uploaded_by_email: userEmail, 
        },
      ]);

      if (dbError) throw dbError;

      setMessage("File uploaded successfully!");
      setFileURL(filePublicURL);
      setCourseNumber("");
      setSubjectName("");
      setCredits("");
      setFile(null);
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessage("Error uploading file. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2>Upload a File</h2>
      {userEmail ? <p>Logged in as: {userName} ({userEmail})</p> : <p>Please log in to upload.</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Course Number:</label>
          <input type="text" value={courseNumber} onChange={(e) => setCourseNumber(e.target.value)} required />
        </div>
        <div>
          <label>Subject Name:</label>
          <input type="text" value={subjectName} onChange={(e) => setSubjectName(e.target.value)} required />
        </div>
        <div>
          <label>Number of Credits:</label>
          <input type="number" value={credits} onChange={(e) => setCredits(e.target.value)} required />
        </div>
        <div>
          <label>Upload File (PDF or DOCX):</label>
          <input type="file" accept=".pdf,.docx" onChange={handleFileChange} required />
        </div>
        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading..." : "Submit"}
        </button>
      </form>
      {message && <p>{message}</p>}
      {fileURL && <p>File URL: <a href={fileURL} target="_blank" rel="noopener noreferrer">{fileURL}</a></p>}
    </div>
  );
}

export default FileUpload;
