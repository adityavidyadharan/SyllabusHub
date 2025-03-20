import { useState } from "react";
import { Accordion, Button, Modal, Spinner } from "react-bootstrap";
import CanvasImportCard from "./CanvasImportCard";
import { useQuery } from "@tanstack/react-query";

export type CourseItem = {
  code: string;
  created_at: string;
  canvas_course_id: number;
  link: string;
  semester_year: string;
  semester: string;
  name: string;
  number: string;
  subject: string;
} & (
  | {
      upload: false;
    }
  | {
      upload: true;
      upload_id: string;
    }
);

type CourseResponse = {
  courses: Record<string, Record<string, CourseItem[]>>,
  years: string[]
};

export default function CanvasSync() {
  const [show, setShow] = useState(false);
  // const [courses, setCourses] = useState<CourseResponse>({});

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  const { data, isLoading: loading, isSuccess } = useQuery({
    queryKey: ["canvas_courses"],
    queryFn: () => {
      return fetch("http://127.0.0.1:5001/canvas/courses")
      .then((response) => response.json())
      .then((data): CourseResponse => {
        return {
          courses: data,
          years: Object.keys(data).sort((a, b) => parseInt(b) - parseInt(a)),
        }
      })
    },
    staleTime: 1000 * 60 * 60, // 1 hour
  });

  // useEffect(() => {
  //   setLoading(true);
  //   fetch("http://127.0.0.1:5001/canvas/courses")
  //     .then((response) => response.json())
  //     .then((data) => {
  //       setCourses(data);
  //       setYears(Object.keys(data).sort((a, b) => parseInt(b) - parseInt(a)));
  //       setLoading(false);
  //     });
  // }, []);

  return (
    <>
      <div>
        <Button variant="primary" onClick={handleShow}>
          Canvas Sync
        </Button>
      </div>
      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Canvas Sync</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="text-center">
            {loading && <Spinner animation="border" />}
          </div>
          {isSuccess && data.years.map((year: string) => (
            <Accordion key={year} alwaysOpen>
              <Accordion.Item eventKey={year}>
                <Accordion.Header>{year}</Accordion.Header>
                <Accordion.Body>
                  {Object.keys(data.courses[year]).map((semester) => (
                    <Accordion key={`${year}-${semester}`} alwaysOpen>
                      <Accordion.Item eventKey={`${year}-${semester}`}>
                        <Accordion.Header>{semester}</Accordion.Header>
                        <Accordion.Body>
                          {data.courses[year][semester].map((course) => (
                            <CanvasImportCard course={course} />
                          ))}
                        </Accordion.Body>
                      </Accordion.Item>
                    </Accordion>
                  ))}
                </Accordion.Body>
              </Accordion.Item>
            </Accordion>
          ))}

          {/* {courses.map(course => (
            <Card key={course.id}>
              <Card.Body>
                <Card.Title>{course.name}</Card.Title>
                <Card.Text>
                  {course.subject} {course.number} - {course.year} {course.month}
                </Card.Text>
                <Button variant="primary">Import Course</Button>
              </Card.Body>
            </Card>
          ))} */}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
