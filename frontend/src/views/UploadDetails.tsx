import { useEffect, useState } from "react";
import { Card, Container, ListGroup, Spinner } from "react-bootstrap";
import { Link, useParams } from "react-router";
import { supabase } from "../clients/supabase";

type UploadInfo = {
  id: number;
  semester: string;
  year: number;
  fileurl: string;
  courses: {
    name: string;
    description: string;
    course_number: number;
    course_subject: string;
  };
  professors: {
    id: number;
    name: string;
  };
};

export default function UploadDetails() {
  // show the course details
  // professor, course name, description, tags (TODO), and the PDF file
  const { uploadId } = useParams();
  const [upload, setUpload] = useState<UploadInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    if (!uploadId) {
      return;
    }
    async function getCourseInfo() {
      const course = await supabase
        .from("uploads")
        .select(
          "id, semester, year, fileurl, professors(id, name), courses(name, description, course_number, course_subject)"
        )
        .eq("id", parseInt(uploadId!, 10))
        .single();
      setUpload(course.data);
      setLoading(false);
    }
    getCourseInfo();
  }, [uploadId]);

  return (
    <Container className="mt-4">
      <h1 className="my-4 text-center">Syllabus Details</h1>
      {loading ? (
        <Spinner animation="border" />
      ) : (
        <>
          <Card className="shadow-sm p-4 mb-4">
            <Card.Body>
              <Card.Title className="fw-bold">
                <Link to={`/?courseNumber=${upload?.courses.course_number}&courseSubject=${upload?.courses.course_subject}`}>
                  {upload?.courses.course_subject} {upload?.courses.course_number}
                </Link>{" - "}
                {upload?.courses.name}
              </Card.Title>
              <Card.Subtitle className="mb-3 text-muted">{`${upload?.semester} ${upload?.year}`}</Card.Subtitle>

              <ListGroup variant="flush">
                <ListGroup.Item>
                  <strong>Professor:</strong> {<Link to={`/?professor=${upload?.professors.name}`}>{upload?.professors.name}</Link>}
                </ListGroup.Item>
                <ListGroup.Item>
                  <strong>Description:</strong> {upload?.courses.description}
                </ListGroup.Item>
              </ListGroup>
            </Card.Body>
          </Card>
          <Card className="shadow-sm p-4 mb-4">
            <Card.Body>
              <Card.Title className="fw-bold">Syllabus PDF</Card.Title>
              <iframe
                src={upload?.fileurl}
                width="100%"
                height="1000px"
                style={{ border: "none" }}
                title="Syllabus PDF"
              ></iframe>
            </Card.Body>
          </Card>
        </>
      )}
    </Container>
  );
}
