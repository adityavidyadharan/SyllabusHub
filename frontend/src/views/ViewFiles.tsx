import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { app } from "../firebase/firebase";

interface FileData {
  id: string;
  courseid: string;
  subname: string;
  credits: number;
  fileurl: string;
  uploaded_by_name: string;
}

const supabase = createClient(
  "https://tsbrojrazwcsjqzvnopi.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw"
);

function ViewFiles() {
  const [files, setFiles] = useState<FileData[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<FileData[]>([]);
  const [courseFilter, setCourseFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [creditsFilter, setCreditsFilter] = useState("");
  const [editingFile, setEditingFile] = useState<FileData | null>(null);
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchFiles();

    const auth = getAuth(app);
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        console.log("Current user:", user.displayName); // Debug log
        setCurrentUser(user.displayName || null);
      } else {
        console.log("No user logged in"); // Debug log
        setCurrentUser(null);
      }
    });

    // Cleanup subscription
    return () => unsubscribe();
  }, []);

  const fetchFiles = async () => {
    try {
      const { data, error } = await supabase
        .from("uploads")
        .select("id, courseid, subname, credits, fileurl, uploaded_by_name");

      if (error) throw error;

      console.log("Fetched files:", data); // Debug log
      setFiles(data || []);
      setFilteredFiles(data || []);
    } catch (error) {
      console.error("Error fetching files:", error);
      alert("Failed to fetch files. Please try again.");
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

  // ... previous imports and interface remain the same ...

  const handleUpdate = async () => {
    if (!editingFile) {
      alert("No file selected for editing.");
      return;
    }
  
    if (isUpdating) return;
  
    try {
      setIsUpdating(true);
  
      const auth = getAuth(app);
      const user = auth.currentUser;
  
      if (!user || !user.displayName) {
        alert("You must be logged in to update files.");
        return;
      }
  
      console.log("Attempting update with user:", user.displayName);
      console.log("File uploaded by:", editingFile.uploaded_by_name);
  
      if (user.displayName !== editingFile.uploaded_by_name) {
        alert("You can only edit files that you uploaded.");
        return;
      }
  
      const updateData = {
        courseid: editingFile.courseid.trim(),
        subname: editingFile.subname.trim(),
        credits: editingFile.credits,
      };
  
      console.log("Updating file with data:", updateData);
      console.log("File ID:", editingFile.id);
  
      // First, perform the update
      const { error: updateError } = await supabase
        .from("uploads")
        .update(updateData)
        .match({ id: editingFile.id });
  
      if (updateError) throw updateError;
  
      // If update successful, fetch the updated record
      const { data: updatedData, error: fetchError } = await supabase
        .from("uploads")
        .select("*")
        .match({ id: editingFile.id })
        .single();
  
      if (fetchError) throw fetchError;
  
      console.log("Update successful:", updatedData);
  
      // Update local state
      setFiles(prevFiles =>
        prevFiles.map(file =>
          file.id === editingFile.id 
            ? { ...file, ...updateData } 
            : file
        )
      );
  
      // Refresh the file list to ensure we have the latest data
      fetchFiles();
  
      setEditingFile(null);
      alert("File updated successfully!");
    } catch (error) {
      console.error("Error updating file:", error);
      if (error instanceof Error) {
        alert(`Failed to update file: ${error.message}`);
      } else {
        alert("Failed to update file. Please try again.");
      }
    } finally {
      setIsUpdating(false);
    }
  };
  
  const handleDelete = async (file: FileData) => {
    if (!window.confirm("Are you sure you want to delete this file?")) return;

    try {
      // Check Firebase authentication
      const auth = getAuth(app);
      const user = auth.currentUser;

      if (!user || !user.displayName) {
        alert("You must be logged in to delete files.");
        return;
      }

      if (user.displayName !== file.uploaded_by_name) {
        alert("You can only delete files that you uploaded.");
        return;
      }

      const filePath = file.fileurl.split("/storage/v1/object/public/")[1];

      const { error: storageError } = await supabase.storage
        .from("Course Syllabuses")
        .remove([filePath]);

      if (storageError) throw storageError;

      const { error: dbError } = await supabase
        .from("uploads")
        .delete()
        .eq("id", file.id);

      if (dbError) throw dbError;

      await fetchFiles();
      alert("File deleted successfully!");
    } catch (error) {
      console.error("Error deleting file:", error);
      alert("Failed to delete file. Please try again.");
    }
  };

  // Rest of the component remains the same...
  return (
    <div style={{ padding: "20px", maxWidth: "900px", margin: "auto" }}>
      <h2>Uploaded Files</h2>

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

      <table style={{ width: "100%", borderCollapse: "collapse", border: "1px solid #ddd" }}>
        <thead>
          <tr style={{ backgroundColor: "#f4f4f4", textAlign: "left" }}>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Course Number</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Subject Name</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Credits</th>
            <th style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>Uploaded By</th>
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
                <td style={{ padding: "10px" }}>{file.uploaded_by_name || "Unknown"}</td>
                <td style={{ padding: "10px" }}>
                  <a href={file.fileurl} target="_blank" rel="noopener noreferrer">
                    View File
                  </a>
                </td>
                <td style={{ padding: "10px" }}>
                  {currentUser === file.uploaded_by_name ? (
                    <>
                      <button 
                        onClick={() => setEditingFile(file)} 
                        style={{ marginRight: "5px" }}
                        disabled={isUpdating}
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDelete(file)} 
                        style={{ backgroundColor: "red", color: "white" }}
                        disabled={isUpdating}
                      >
                        Delete
                      </button>
                    </>
                  ) : (
                    <>
                      <button disabled style={{ backgroundColor: "#ccc", color: "#666", cursor: "not-allowed", marginRight: "5px" }}>Edit</button>
                      <button disabled style={{ backgroundColor: "#ccc", color: "#666", cursor: "not-allowed" }}>Delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6} style={{ textAlign: "center", padding: "10px" }}>No matching files found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {editingFile && (
        <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ddd" }}>
          <h3>Edit File</h3>
          <input
            type="text"
            value={editingFile.courseid}
            onChange={(e) => setEditingFile({ ...editingFile, courseid: e.target.value })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
            disabled={isUpdating}
          />
          <input
            type="text"
            value={editingFile.subname}
            onChange={(e) => setEditingFile({ ...editingFile, subname: e.target.value })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
            disabled={isUpdating}
          />
          <input
            type="number"
            value={editingFile.credits}
            onChange={(e) => setEditingFile({ ...editingFile, credits: parseInt(e.target.value) || 0 })}
            style={{ padding: "8px", width: "100%", marginBottom: "10px" }}
            disabled={isUpdating}
          />
          <button 
            onClick={handleUpdate} 
            style={{ marginRight: "5px" }}
            disabled={isUpdating}
          >
            {isUpdating ? "Updating..." : "Update"}
          </button>
          <button 
            onClick={() => setEditingFile(null)} 
            style={{ backgroundColor: "gray", color: "white" }}
            disabled={isUpdating}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export default ViewFiles;