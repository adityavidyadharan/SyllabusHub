import { useState, useEffect } from "react";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { Form, Button, Container, Alert, Spinner } from "react-bootstrap";
import { useLocation, useNavigate } from "react-router";
import { FileData } from "../types/FileTypes";
import firebase from "firebase/compat/app";
import { supabase } from "../clients/supabase";

function FileUpload() {
  const [courseNumber, setCourseNumber] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [credits, setCredits] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [fileURL, setFileURL] = useState("");
  const [fileID, setFileID] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [isEdit, setIsEdit] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const existingFile = location.state?.file as FileData || null;
  useEffect(() => {
    if (existingFile) {
      setCourseNumber(existingFile.courseid);
      setFileID(existingFile.id);
      setSubjectName(existingFile.subname);
      setCredits(existingFile.credits.toString());
      setFileURL(existingFile.fileurl);
      setIsEdit(true);
    }
  }, [existingFile]);

  const auth = firebase.auth();

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

    if (!userEmail) {
      setMessage("You must be logged in to upload files.");
      return;
    }

    try {
      if (isEdit) {
        setUploading(true);
        const updateData = {
          courseid: courseNumber,
          subname: subjectName,
          credits: credits,
        };

        const { error: updateError } = await supabase
        .from("uploads")
        .update(updateData)
        .match({ id: fileID });

        if (updateError) throw updateError;

        navigate("/files");
        return;
      }
    } catch (error) {
      console.error("Error updating file:", error);
      setMessage("Error updating file. Please try again.");
    } finally {
      setUploading(false);
    }
    
    if (!file) {
      setMessage("Please select a file to upload.");
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
    <Container className="mt-4">
      <h2>Upload a File</h2>
      {userEmail ? (
        <Alert variant="info">
          Logged in as: {userName} ({userEmail})
        </Alert>
      ) : (
        <Alert variant="warning">Please log in to upload.</Alert>
      )}
      {message && <Alert variant="info">{message}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Course Number</Form.Label>
          <Form.Control
            type="text"
            value={courseNumber}
            onChange={(e) => setCourseNumber(e.target.value)}
            required
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Subject Name</Form.Label>
          <Form.Control
            type="text"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
            required
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Number of Credits</Form.Label>
          <Form.Control
            type="number"
            value={credits}
            onChange={(e) => setCredits(e.target.value)}
            required
          />
        </Form.Group>
        {!isEdit && (
          <Form.Group className="mb-3">
            <Form.Label>Upload File (PDF or DOCX)</Form.Label>
            <Form.Control
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              required
            />
          </Form.Group>
        )}
        <Button variant="primary" type="submit" disabled={uploading}>
          {uploading ? (
            <Spinner as="span" animation="border" size="sm" />
          ) : (
            "Submit"
          )}
        </Button>
      </Form>
      {fileURL && (
        <Alert variant="success" className="mt-3">
          File URL:{" "}
          <a href={fileURL} target="_blank" rel="noopener noreferrer">
            {fileURL}
          </a>
        </Alert>
      )}
    </Container>
  );
}

export default FileUpload;
