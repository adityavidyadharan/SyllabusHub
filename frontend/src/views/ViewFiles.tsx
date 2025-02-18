import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { app } from "../firebase/firebase";
import { Table, Form, Button, Container, Alert, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router";
import { FileData } from "../types/FileTypes";



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

  const navigate = useNavigate();

  useEffect(() => {
    fetchFiles();

    const auth = getAuth(app);
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setCurrentUser(user.displayName || null);
      } else {
        setCurrentUser(null);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleEdit = (file: FileData) => {
    navigate("/upload", { state: { file } });
  }

  const fetchFiles = async () => {
    try {
      const { data, error } = await supabase
        .from("uploads")
        .select("id, courseid, subname, credits, fileurl, uploaded_by_name");

      if (error) throw error;

      setFiles(data || []);
      setFilteredFiles(data || []);
    } catch (error) {
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

  return (
    <Container className="mt-4">
      <h2>Uploaded Files</h2>
      <Form className="mb-3">
        <Form.Control
          type="text"
          placeholder="Filter by Course Number"
          value={courseFilter}
          onChange={(e) => setCourseFilter(e.target.value)}
          className="mb-2"
        />
        <Form.Control
          type="text"
          placeholder="Filter by Subject Name"
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          className="mb-2"
        />
        <Form.Control
          type="number"
          placeholder="Filter by Credits"
          value={creditsFilter}
          onChange={(e) => setCreditsFilter(e.target.value)}
        />
      </Form>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Course Number</th>
            <th>Subject Name</th>
            <th>Credits</th>
            <th>Uploaded By</th>
            <th>File</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredFiles.length > 0 ? (
            filteredFiles.map((file) => (
              <tr key={file.id}>
                <td>{file.courseid}</td>
                <td>{file.subname}</td>
                <td>{file.credits}</td>
                <td>{file.uploaded_by_name || "Unknown"}</td>
                <td>
                  <a href={file.fileurl} target="_blank" rel="noopener noreferrer">
                    View File
                  </a>
                </td>
                <td>
                  {currentUser === file.uploaded_by_name ? (
                    <>
                      <Button variant="warning" size="sm" onClick={() => handleEdit(file)}>Edit</Button>{' '}
                      <Button variant="danger" size="sm" onClick={() => handleDelete(file)}>Delete</Button>
                    </>
                  ) : (
                    <span>N/A</span>
                  )}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6} className="text-center">No matching files found.</td>
            </tr>
          )}
        </tbody>
      </Table>
    </Container>
  );
}

export default ViewFiles;
