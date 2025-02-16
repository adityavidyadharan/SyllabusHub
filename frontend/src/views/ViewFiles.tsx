import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

interface FileData {
  id: string; // UUID from Supabase
  courseid: string;
  subname: string;
  credits: number;
  fileurl: string;
}

// Initialize Supabase Client
const supabase = createClient(
    "https://tsbrojrazwcsjqzvnopi.supabase.co", // Replace with your Supabase URL
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw" // Replace with your Supabase API Key
  );

function ViewFiles() {
  const [files, setFiles] = useState<FileData[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<FileData[]>([]);
  const [courseFilter, setCourseFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [creditsFilter, setCreditsFilter] = useState("");
  const [editingFile, setEditingFile] = useState<FileData | null>(null);

  useEffect(() => {
    fetchFiles();
  }, []);


  const fetchFiles = async () => {
    const { data, error } = await supabase.from("uploads").select("*");
    if (error) {
      console.error("Error fetching files:", error);
    } else {
      setFiles(data as FileData[]);
      setFilteredFiles(data as FileData[]);
    }
  };


  useEffect(() => {
    const filtered = files.filter((file) => {
      return (
        (courseFilter ? file.courseid.toLowerCase().includes(courseFilter.toLowerCase()) : true) &&
        (subjectFilter ? file.subname.toLowerCase().includes(subjectFilter.toLowerCase()) : true) &&
        (creditsFilter ? file.credits.toString() === creditsFilter : true)
      );
    });
    setFilteredFiles(filtered);
  }, [courseFilter, subjectFilter, creditsFilter, files]);


  const handleEdit = (file: FileData) => {
    setEditingFile({ ...file });
  };


  const handleUpdate = async () => {
    if (!editingFile) return;

    const { error } = await supabase
      .from("uploads")
      .update({
        courseid: editingFile.courseid,
        subname: editingFile.subname,
        credits: Number(editingFile.credits), 
      })
      .eq("id", editingFile.id);

    if (error) {
      console.error("Error updating file:", error);
    } else {
      setEditingFile(null);
      fetchFiles();
    }
  };


  const handleDelete = async (file: FileData) => {
    if (!window.confirm("Are you sure you want to delete this file?")) return;

    const filePath = file.fileurl.split("/storage/v1/object/public/")[1];
    const { error: storageError } = await supabase.storage.from("Course Syllabuses").remove([filePath]);

    if (storageError) {
      console.error("Error deleting file from storage:", storageError);
      return;
    }

    const { error: dbError } = await supabase.from("uploads").delete().eq("id", file.id);

    if (dbError) {
      console.error("Error deleting file from database:", dbError);
    } else {
      fetchFiles();
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "900px", margin: "auto" }}>
      <h2>Uploaded Files</h2>

      {/* ✅ Filters */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
        <input
          type="text"
          placeholder="Filter by Course Number"
          value={courseFilter}
          onChange={(e) => setCourseFilter(e.target.value)}
          style={{ padding: "8px", width: "30%" }}
        />
        <input
          type="text"
          placeholder="Filter by Subject Name"
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          style={{ padding: "8px", width: "30%" }}
        />
        <input
          type="number"
          placeholder="Filter by Credits"
          value={creditsFilter}
          onChange={(e) => setCreditsFilter(e.target.value)}
          style={{ padding: "8px", width: "20%" }}
        />
      </div>

      {/* ✅ Table */}
      <table style={{ width: "100%", borderCollapse: "collapse", border: "1px solid #ddd" }}>
        <thead>
          <tr style={{ backgroundColor: "#f4f4f4", textAlign: "left" }}>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Course Number</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Subject Name</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Credits</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>File</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredFiles.length > 0 ? (
            filteredFiles.map((file) => (
              <tr key={file.id} style={{ borderBottom: "1px solid #ddd" }}>
                <td style={{ padding: "10px" }}>{file.courseid}</td>
                <td style={{ padding: "10px" }}>{file.subname}</td>
                <td style={{ padding: "10px" }}>{file.credits}</td>
                <td style={{ padding: "10px" }}>
                  <a href={file.fileurl} target="_blank" rel="noopener noreferrer">
                    View File
                  </a>
                </td>
                <td style={{ padding: "10px" }}>
                  <button onClick={() => handleEdit(file)} style={{ marginRight: "5px" }}>Edit</button>
                  <button onClick={() => handleDelete(file)} style={{ backgroundColor: "red", color: "white" }}>Delete</button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} style={{ textAlign: "center", padding: "10px" }}>No matching files found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {/* ✅ Edit Form */}
      {editingFile && (
        <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ddd" }}>
          <h3>Edit File</h3>
          <input
            type="text"
            value={editingFile?.courseid ?? ""}
            onChange={(e) => setEditingFile({ ...editingFile, courseid: e.target.value })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
          />
          <input
            type="text"
            value={editingFile?.subname ?? ""}
            onChange={(e) => setEditingFile({ ...editingFile, subname: e.target.value })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
          />
          <input
            type="number"
            value={editingFile?.credits.toString() ?? ""}
            onChange={(e) => setEditingFile({ ...editingFile, credits: Number(e.target.value) || 0 })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
          />
          <button onClick={handleUpdate} style={{ marginRight: "5px" }}>Update</button>
          <button onClick={() => setEditingFile(null)} style={{ backgroundColor: "gray", color: "white" }}>Cancel</button>
        </div>
      )}
    </div>
  );
}

export default ViewFiles;
