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
  const [semester, setSemester] = useState("");
  const [year, setYear] = useState<number>(new Date().getFullYear());
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

  // Get the current year for validation
  const currentYear = new Date().getFullYear();
  
  // Valid semester options
  const validSemesters = ["Spring", "Summer", "Fall"];

  // Generate array of years for the dropdown (from 1900 to current year)
  // Generate array of years from 1900 up to 2 years into the future
const yearOptions = Array.from(
  { length: (currentYear + 2) - 1899 },
  (_, i) => currentYear + 2 - i
);

  const existingFile = location.state?.file as FileData || null;
  useEffect(() => {
    if (existingFile) {
      setCourseNumber(existingFile.courseid);
      setFileID(existingFile.id);
      setSubjectName(existingFile.subname);
      setCredits(existingFile.credits.toString());
      setFileURL(existingFile.fileurl);
      // Set semester and year if they exist in the existingFile
      if (existingFile.semester) setSemester(existingFile.semester);
      if (existingFile.year) setYear(existingFile.year);
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

  // Function to sanitize filenames for Supabase storage
  const sanitizeFileName = (fileName: string): string => {
    // Replace square brackets, parentheses, and other special characters
    return fileName
      .replace(/[\[\](){}:;*?/\\<>|#%&]/g, '_')
      .replace(/\s+/g, '_');
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
          semester: semester,
          year: year
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

    // Sanitize the filename before uploading
    const sanitizedFileName = sanitizeFileName(file.name);
    const filePath = `course_syllabuses/${Date.now()}-${sanitizedFileName}`;

    try {
      // Create a new file with the sanitized name
      const fileToUpload = new File([file], sanitizedFileName, {
        type: file.type,
        lastModified: file.lastModified
      });

      const { data, error } = await supabase.storage
        .from("Course Syllabuses")
        .upload(filePath, fileToUpload);

      if (error) throw error;

      const filePublicURL = `https://tsbrojrazwcsjqzvnopi.supabase.co/storage/v1/object/public/Course Syllabuses/${filePath}`;

      const { error: dbError } = await supabase.from("uploads").insert([
        {
          courseid: courseNumber,
          subname: subjectName,
          credits: credits,
          semester: semester,
          year: year,
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
      setSemester("");
      setYear(currentYear);
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
        <Form.Group className="mb-3">
          <Form.Label>Semester</Form.Label>
          <Form.Select
            value={semester}
            onChange={(e) => setSemester(e.target.value)}
            required
          >
            <option value="">Select Semester</option>
            {validSemesters.map((sem) => (
              <option key={sem} value={sem}>
                {sem}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Year</Form.Label>
          <Form.Select
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            required
          >
            <option value="">Select Year</option>
            {yearOptions.map((yr) => (
              <option key={yr} value={yr}>
                {yr}
              </option>
            ))}
          </Form.Select>
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
            <Form.Text className="text-muted">
              Note: Special characters in filenames will be replaced with underscores.
            </Form.Text>
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