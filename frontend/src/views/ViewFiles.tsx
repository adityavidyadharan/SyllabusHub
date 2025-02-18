import { useEffect, useState } from "react";
import { onAuthStateChanged } from "firebase/auth";
import {
  Table,
  Form,
  Button,
  Container,
  Spinner,
  Row,
  Col,
  Accordion,
  Alert,
  Modal
} from "react-bootstrap";
import { useNavigate, useLocation } from "react-router";
import firebase from "firebase/compat/app";
import { supabase } from "../clients/supabase";
import { UserUploadedFile } from "../types/relations";

function ViewFiles() {
  const [files, setFiles] = useState<UserUploadedFile[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<UserUploadedFile[]>([]);
  const [courseNumberFilter, setCourseNumberFilter] = useState("");
  const [courseSubjectFilter, setCourseSubjectFilter] = useState("");
  const [courseNameFilter, setCourseNameFilter] = useState("");
  const [semesterFilter, setSemesterFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Add state for alerts
  const [alert, setAlert] = useState<{show: boolean; message: string; variant: string}>({
    show: false,
    message: "",
    variant: "success",
  });
  // Add state for delete modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<UserUploadedFile | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  
  const validSemesters = ["Spring", "Summer", "Fall"];

  useEffect(() => {
    const auth = firebase.auth();
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setCurrentUser(user.uid);
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
  }, [currentUser]);

  // Check for success/error messages from location state
  useEffect(() => {
    // Check if we have a state with success or error message
    if (location.state?.message) {
      showAlert(
        location.state.message,
        location.state.success ? "success" : "danger"
      );
      
      // Clear the location state after showing the alert
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location, navigate]); 

  // Helper function to show alert
  const showAlert = (message: string, variant: string) => {
    setAlert({
      show: true,
      message,
      variant,
    });
    
    // Auto-dismiss alert after 5 seconds
    setTimeout(() => {
      setAlert(prev => ({...prev, show: false}));
    }, 5000);
  };

  const resetFilters = () => {
    setCourseNumberFilter("");
    setCourseSubjectFilter("");
    setCourseNameFilter("");
    setSemesterFilter("");
    setYearFilter("");
  };

  const fetchFiles = async () => {
    if (!currentUser) return; // Ensure user is logged in
  
    try {
      if (!currentUser) return;
      setLoading(true);
      const { data, error } = await supabase
        .from("uploads")
        .select("id, semester, year, fileurl, courses(course_number, course_subject, name), professors(name, firebase_id)")
        .eq("professors.firebase_id", currentUser);
      if (error) throw error;
      if (!data) return;

      setFiles(data);
      setFilteredFiles(data || []);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      showAlert("Failed to fetch files. Please try again.", "danger");
    }
  };
  

  const handleEdit = (file: UserUploadedFile) => {
    // Navigate to the upload page with the file data for editing
    navigate("/upload", { 
      state: { 
        file,
        returnUrl: "/view-files", 
        isEditing: true 
      } 
    });
  };

  // Open delete confirmation modal
  const confirmDelete = (file: UserUploadedFile) => {
    setFileToDelete(file);
    setShowDeleteModal(true);
  };

  // Handle actual delete after confirmation
  const handleDelete = async () => {
    if (!fileToDelete) return;
    
    try {
      const { error: storageError } = await supabase.storage
        .from("Course Syllabuses")
        .remove([fileToDelete.fileurl.split("/storage/v1/object/public/")[1]]);

      if (storageError) throw storageError;

      const { error: dbError } = await supabase
        .from("uploads")
        .delete()
        .eq("id", fileToDelete.id);

      if (dbError) throw dbError;

      // Close the modal
      setShowDeleteModal(false);
      // Clear the file to delete
      setFileToDelete(null);
      // Refresh the files list
      fetchFiles();
      // Show success message
      showAlert("File deleted successfully!", "success");
    } catch (error) {
      console.error("Error deleting file:", error);
      setShowDeleteModal(false);
      showAlert("Failed to delete file. Please try again.", "danger");
    }
  };

  // Apply filters whenever filter values change
  useEffect(() => {
    let filtered = [...files];
    
    if (courseNumberFilter) {
      filtered = filtered.filter(file => 
        file.courses.course_number.toString().includes(courseNumberFilter)
      );
    }
    
    if (courseSubjectFilter) {
      filtered = filtered.filter(file => 
        file.courses.course_subject.toLowerCase().includes(courseSubjectFilter.toLowerCase())
      );
    }

    if (courseNameFilter) {
      filtered = filtered.filter(file => 
        file.courses.name.toLowerCase().includes(courseNameFilter.toLowerCase())
      );
    }
    
    if (semesterFilter) {
      filtered = filtered.filter(file => 
        file.semester === semesterFilter
      );
    }
    
    if (yearFilter) {
      filtered = filtered.filter(file => 
        file.year === parseInt(yearFilter)
      );
    }
    
    setFilteredFiles(filtered);
  }, [files, courseNumberFilter, courseSubjectFilter, courseNameFilter, semesterFilter, yearFilter]);

  return (
    <Container className="mt-4">
      <h2>Uploaded Files</h2>
      
      {/* Alert component */}
      {alert.show && (
        <Alert 
          variant={alert.variant} 
          onClose={() => setAlert(prev => ({...prev, show: false}))} 
          dismissible
        >
          {alert.message}
        </Alert>
      )}
      
      <Accordion defaultActiveKey="0" className="mb-3">
        <Accordion.Item eventKey="0">
          <Accordion.Header>Advanced Filters</Accordion.Header>
          <Accordion.Body>
            <Row>
              <Col md={4} className="mb-2">
                <Form.Control
                  type="number"
                  placeholder="Filter by Course Number"
                  value={courseNumberFilter}
                  onChange={(e) => setCourseNumberFilter(e.target.value)}
                />
              </Col>
              <Col md={4} className="mb-2">
                <Form.Control
                  type="text"
                  placeholder="Filter by Course Subject"
                  value={courseSubjectFilter}
                  onChange={(e) => setCourseSubjectFilter(e.target.value)}
                />
              </Col>
              <Col md={4} className="mb-2">
                <Form.Control
                  type="text"
                  placeholder="Filter by Course name"
                  value={courseNameFilter}
                  onChange={(e) => setCourseNameFilter(e.target.value)}
                />
              </Col>
              <Col md={6} className="mb-2">
                <Form.Select
                  value={semesterFilter}
                  onChange={(e) => setSemesterFilter(e.target.value)}
                >
                  <option value="">Filter by Semester</option>
                  {validSemesters.map((sem) => (
                    <option key={sem} value={sem}>{sem}</option>
                  ))}
                </Form.Select>
              </Col>
              <Col md={6} className="mb-2">
                <Form.Select
                  value={yearFilter}
                  onChange={(e) => setYearFilter(e.target.value)}
                >
                  <option value="">Filter by Year</option>
                  {[...Array(new Date().getFullYear() - 1999 + 3)].map((_, i) => (
    <option key={i} value={(new Date().getFullYear() - i + 2).toString()}>
      {new Date().getFullYear() - i + 2}
    </option>
  ))}
                </Form.Select>
              </Col>
              <Col md={12} className="mt-2">
                <Button variant="secondary" onClick={resetFilters}>Reset Filters</Button>
              </Col>
            </Row>
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
      
      {loading ? (
        <div className="text-center my-4">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      ) : (
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Course Name</th>
              <th>Course Number</th>
              <th>Course Subject</th>
              <th>Semester</th>
              <th>Year</th>
              <th>Actions</th>
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {filteredFiles.length > 0 ? (
              filteredFiles.map((file) => (
                <tr key={file.id}>
                  <td>{file.courses.name}</td>
                  <td>{file.courses.course_number}</td>
                  <td>{file.courses.course_subject}</td>
                  <td>{file.semester || "N/A"}</td>
                  <td>{file.year || "N/A"}</td>
                  <td>
                    <Button variant="success" size="sm" onClick={() => handleEdit(file)}>
                      Edit
                    </Button>{" "}
                    <Button variant="danger" size="sm" onClick={() => confirmDelete(file)}>
                      Delete
                    </Button>
                  </td>
                  <td>
                    <a href={file.fileurl} target="_blank" rel="noopener noreferrer">View File</a>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} className="text-center">No files found</td>
              </tr>
            )}
          </tbody>
        </Table>
      )}
      
      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this file?
          {fileToDelete && (
            <div className="mt-2">
              <strong>Course:</strong> {fileToDelete.courseid} - {fileToDelete.subname}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}
export default ViewFiles;