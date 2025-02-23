import { useEffect, useState } from "react";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import {
  Table,
  Form,
  Button,
  Container,
  Spinner,
} from "react-bootstrap";
import { useNavigate } from "react-router";
import { FileData } from "../types/FileTypes";
import firebase from "firebase/compat/app";
import { supabase } from "../clients/supabase";

function ViewFiles() {
  const [files, setFiles] = useState<FileData[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<FileData[]>([]);
  const [courseFilter, setCourseFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [creditsFilter, setCreditsFilter] = useState("");
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    const auth = firebase.auth();
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setCurrentUser(user.email || null);
      } else {
        setCurrentUser(null);
      }
    });
    
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (currentUser) {
      fetchFiles();
    }
  }
  , [currentUser]);

  const handleEdit = (file: FileData) => {
    navigate("/upload", { state: { file } });
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

  const fetchFiles = async () => {
    try {
      setLoading(true);
      console.log(currentUser);
      const { data, error } = await supabase
        .from("uploads")
        .select("id, courseid, subname, credits, fileurl, uploaded_by_name, uploaded_by_email")
        // filter by user email
        .eq("uploaded_by_email", currentUser);
      console.log(data);

      if (error) throw error;

      setFiles(data || []);
      setFilteredFiles(data || []);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      alert("Failed to fetch files. Please try again.");
    }
  };

  useEffect(() => {
    const filtered = files.filter((file) => {
      return (
        (courseFilter
          ? file.courseid.toLowerCase().includes(courseFilter.toLowerCase())
          : true) &&
        (subjectFilter
          ? file.subname.toLowerCase().includes(subjectFilter.toLowerCase())
          : true) &&
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
        {loading ? (
          <tbody>
            <tr>
              <td colSpan={6} className="text-center">
                <Spinner animation="border" />
              </td>
            </tr>
          </tbody>
        ) : (
          <tbody>
            {filteredFiles.length > 0 ? (
              filteredFiles.map((file) => (
                <tr key={file.id}>
                  <td>{file.courseid}</td>
                  <td>{file.subname}</td>
                  <td>{file.credits}</td>
                  <td>{file.uploaded_by_name || "Unknown"}</td>
                  <td>
                    <a
                      href={file.fileurl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View File
                    </a>
                  </td>
                  <td>
                    {currentUser === file.uploaded_by_email ? (
                      <>
                        <Button
                          variant="warning"
                          size="sm"
                          onClick={() => handleEdit(file)}
                        >
                          Edit
                        </Button>{" "}
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDelete(file)}
                        >
                          Delete
                        </Button>
                      </>
                    ) : (
                      <span>N/A</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="text-center">
                  No matching files found.
                </td>
              </tr>
            )}
          </tbody>
        )}
      </Table>
    </Container>
  );
}

export default ViewFiles;
