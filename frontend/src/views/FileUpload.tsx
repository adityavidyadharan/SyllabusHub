import { useState, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import {
  Form,
  Button,
  Container,
  Alert,
  Spinner,
  Col,
  Row,
} from "react-bootstrap";
import { useLocation, useNavigate } from "react-router";
import firebase from "firebase/compat/app";
import { supabase } from "../clients/supabase";
import { Database } from "../types/db";
import { Tags, UserUploadedFile } from "../types/relations";

function FileUpload() {
  const [courseId, setCourseId] = useState("");
  const [courseNumber, setCourseNumber] = useState("");
  const [courseSubject, setCourseSubject] = useState("");
  const [courseName, setCourseName] = useState("");
  const [semesterYear, setSemesterYear] = useState("");
  const [semesterSeason, setSemesterSeason] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [fileURL, setFileURL] = useState("");
  const [fileID, setFileID] = useState<number | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [isEdit, setIsEdit] = useState(false);

  const [courseSubjects, setCourseSubjects] = useState<string[]>([]);
  const [courseNumbers, setCourseNumbers] = useState<Record<number, number>>(
    {}
  );

  const [tagList, setTagList] = useState<Tags[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [generatingTags, setGeneratingTags] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  // Get the current year for validation
  const currentYear = new Date().getFullYear();

  const auth = firebase.auth();

  const existingFile = (location.state?.file as UserUploadedFile) || null;

  useEffect(() => {
    if (existingFile) {
      setSemesterSeason(existingFile.semester);
      setSemesterYear(existingFile.year.toString());
      setCourseNumber(existingFile.courses.course_number.toString());
      setCourseSubject(existingFile.courses.course_subject);
      setCourseName(existingFile.courses.name);
      setCourseId(existingFile.courses.id.toString());
      setFileID(existingFile.id);
      setFileURL(existingFile.fileurl || "");
      setIsEdit(true);
    }
  }, [existingFile]);

  useEffect(() => {
    const fetchTags = async () => {
      const data = await supabase.from("tags").select("*");
      if (data.error) {
        console.error("Error fetching tags:", data.error);
        return;
      }
      setTagList(data.data || []);
    };
    fetchTags();
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        setUserEmail(user.email);
        setUserName(user.displayName || "Unknown User");
        const data = await supabase
          .from("professors")
          .select("*")
          .eq("firebase_id", user.uid)
          .single();
        if (data.data && data.data.id) {
          setUserId(data.data?.id);
        } else {
          console.error("Professor not found in database.");
        }
      } else {
        setUserEmail(null);
        setUserName(null);
        setUserId(null);
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    fetch("http://127.0.0.1:5001/courses/subjects")
      .then((response) => response.json())
      .then((data) => setCourseSubjects(data));
  }, []);

  useEffect(() => {
    fetch(`http://127.0.0.1:5001/courses/numbers?subject=${courseSubject}`)
      .then((response) => response.json())
      .then((data) => {
        setCourseNumbers(data);
      });
  }, [courseSubject]);

  useEffect(() => {
    if (!courseNumber || !courseSubject) {
      setCourseName("");
      return;
    }
    fetch(
      `http://127.0.0.1:5001/courses/details/${courseSubject}/${courseNumber}`
    )
      .then((response) => response.json())
      .then((data) => {
        setCourseName(data.name);
      });
  }, [courseNumber, courseSubject]);

  const clearForm = () => {
    setCourseName("");
    setCourseSubject("");
    setCourseId("");
    setCourseNumber("");
    setSemesterYear("");
    setSemesterSeason("");
    setFile(null);
    setMessage("");
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  // Function to sanitize filenames for Supabase storage
  const sanitizeFileName = (fileName: string): string => {
    // Replace square brackets, parentheses, and other special characters
    return fileName
      .replace(/[\[\](){}:;*?/\\<>|#%&]/g, "_")
      .replace(/\s+/g, "_");
  };

  // Function for generating tags
  const generateTags = async () => {
    if (!file) {
      console.error("No file provided for generating tags");
      setMessage((prev) => `${prev}\nNo file provided for generating tags`);
      return null;
    }
    try {
      setMessage("");
      setGeneratingTags(true);
      const data = new FormData();
      data.append("file", file);

      const response = await fetch("http://127.0.0.1:5001/tags/generate-tags", {
        method: "POST",
        body: data,
      });

      if (!response.ok) {
        throw new Error("Failed to generate tags");
      }

      const result: {
        tags: {
          [key: string]: {
            is_tagged: boolean;
            db_id: string;
          };
        };
      } = await response.json();
      setSelectedTags(
        Object.keys(result.tags)
          .filter((key) => result.tags[key].is_tagged)
          .map((key) => result.tags[key].db_id)
      );
      // setTagReasoning(result.reasoning);
      return result;
    } catch (error) {
      console.error("Error generating tags:", error);
      setMessage((prev) => `${prev}\nError generating tags: ${error}`);
      return null;
    } finally {
      setGeneratingTags(false);
    }
  };
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!userEmail || !userId) {
      setMessage("You must be logged in to upload files.");
      return;
    }

    try {
      if (isEdit) {
        setUploading(true);
        const updateData = {
          crn: null,
          semester: semesterSeason,
          year: parseInt(semesterYear),
          course_id: parseInt(courseId),
          professor_id: userId,
        };

        const { error: updateError } = await supabase
          .from("uploads")
          .update(updateData)
          .match({ id: fileID });

        // delete existing tags
        await supabase
          .from("uploads_tags")
          .delete()
          .match({ upload_id: fileID });

        // insert new tags
        selectedTags.forEach(async (tagId) => {
          const { error: tagError } = await supabase
            .from("uploads_tags")
            .insert([
              {
                upload_id: fileID,
                tag_id: parseInt(tagId),
              },
            ]);

          if (tagError) throw tagError;
        });

        if (updateError) throw updateError;

        navigate("/files");
        return;
      }
    } catch (error) {
      console.error("Error updating file:", error);
      setMessage("Error updating file. Please try again.");
      setUploading(false);
      return;
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
        lastModified: file.lastModified,
      });

      const { error } = await supabase.storage
        .from("Course Syllabuses")
        .upload(filePath, fileToUpload);

      if (error) throw error;

      const filePublicURL = `https://tsbrojrazwcsjqzvnopi.supabase.co/storage/v1/object/public/Course Syllabuses/${filePath}`;
      const { data: uploadData, error: dbError } = await supabase
        .from("uploads")
        .insert<Database["public"]["Tables"]["uploads"]["Insert"]>(
          {
            crn: null,
            fileurl: filePublicURL,
            semester: semesterSeason,
            year: parseInt(semesterYear),
            course_id: parseInt(courseId),
            professor_id: userId,
          },
        ).select("id").single();
        

      if (dbError) throw dbError;
      // Generate tags for the uploaded file
      // need to insert tags into uploads_tags table (many-to-many relation)
      selectedTags.forEach(async (tagId) => {
          const { error: tagError } = await supabase
            .from("uploads_tags")
            .insert([
              {
                upload_id: uploadData.id,
                tag_id: parseInt(tagId),
              },
            ]);

          if (tagError) throw tagError;
        }
      );

      setMessage("File uploaded successfully!");
      setFileURL(filePublicURL);
      clearForm();
    } catch (error) {
      console.error("Error uploading file:", error);
      // delete file from storage if upload fails
      await supabase.storage.from("Course Syllabuses").remove([filePath]);
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
          <Form.Label>Course Subject</Form.Label>
          <Form.Select
            value={courseSubject}
            onChange={(e) => setCourseSubject(e.target.value)}
            required
          >
            <option value="">Select a subject</option>
            {courseSubjects.map((subject) => (
              <option key={subject} value={subject}>
                {subject}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Course Number</Form.Label>
          <Form.Select
            value={courseId}
            onChange={(e) => {
              setCourseNumber(
                courseNumbers[e.target.value as unknown as number].toString()
              );
              setCourseId(e.target.value);
            }}
            required
            disabled={!courseSubject}
          >
            <option value="">Select a number</option>
            {Object.entries(courseNumbers).map(([id, course_number]) => (
              <option key={id} value={id}>
                {course_number}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        <Alert
          variant={courseSubject && courseNumber ? "success" : "secondary"}
        >
          Selected Course: {courseSubject} {courseNumber} - {courseName}
        </Alert>
        <Form.Group className="mb-3">
          <Form.Label>Semester Year</Form.Label>
          <Form.Control
            type="number"
            value={semesterYear}
            onChange={(e) => setSemesterYear(e.target.value)}
            required
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Semester Season</Form.Label>
          <Form.Select
            value={semesterSeason}
            onChange={(e) => setSemesterSeason(e.target.value)}
            required
          >
            <option value="">Select a season</option>
            <option value="Spring">Spring</option>
            <option value="Summer">Summer</option>
            <option value="Fall">Fall</option>
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
              Note: Special characters in filenames will be replaced with
              underscores.
            </Form.Text>
          </Form.Group>
        )}
        <Form.Group className="mb-3">
          <Form.Label>Tags</Form.Label>
          <Form.Select
            multiple
            value={selectedTags}
            onChange={(e) =>
              setSelectedTags(
                Array.from(e.target.selectedOptions, (option) => option.value)
              )
            }
          >
            <option value="">Select Tags</option>
            {tagList.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        <Col md={2}>
          <Row className="mb-3">
            <Button
              variant="secondary"
              onClick={generateTags}
              disabled={generatingTags}
            >
              {generatingTags ? (
                <Spinner as="span" animation="border" size="sm" />
              ) : (
                "Generate Tags"
              )}
            </Button>
          </Row>
          <Row>
            <Button variant="primary" type="submit" disabled={uploading}>
              {uploading ? (
                <Spinner as="span" animation="border" size="sm" />
              ) : (
                "Submit"
              )}
            </Button>
          </Row>
        </Col>
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
