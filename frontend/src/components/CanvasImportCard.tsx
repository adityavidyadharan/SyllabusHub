import { Button, Card, Spinner } from "react-bootstrap";
import { CourseItem } from "./CanvasSync";
import { Link } from "react-router";
import { useState } from "react";

export default function CanvasImportCard({ course }: { course: CourseItem }) {
  const alreadyImported = course.upload;
  const [loading, setLoading] = useState(false);
  const [uploadID, setUploadID] = useState<string | null>(null);
  const [section, setSection] = useState("");

  async function triggerUpload(course: CourseItem) {
    setLoading(true);
    try {
      const resp = await fetch("http://127.0.0.1:5001/upload/syllabus/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({...course, section}),
      });
      const data = await resp.json();
      setUploadID(data.upload_id);
    } catch (e) {
      console.error(e);
    }

    setLoading(false);
  }
  return (
    <Card key={course.canvas_course_id} className="mb-3">
      <Card.Body>
        <Card.Title>{course.name}</Card.Title>
        <Card.Text>
          {course.code} - {course.semester} {course.semester_year}
        </Card.Text>
        {alreadyImported ? (
          <Link to={`/details/${course.upload_id}`}>
            <p className="text-muted">Already imported</p>
          </Link>
        ) : loading ? (
          <div className="text-center">
            <Spinner animation="border" />
          </div>
        ) : uploadID ? (
          <Link to={`/details/${uploadID}`}>
            <Button variant="primary">View Upload</Button>
          </Link>
        ) : (
          <div className="mb-3 d-flex justify-content-between flex-column align-items-center">
            <input
              type="text"
              placeholder="Course Section"
              className="mb-2 rounded"
              value={section}
              onChange={(e) => setSection(e.target.value)}
            />
            <Button
              variant="primary"
              disabled={alreadyImported}
              onClick={() => triggerUpload(course)}
            >
              Import Course
            </Button>
          </div>
        )}
      </Card.Body>
    </Card>
  );
}
