import React, { useEffect, useState } from "react";
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  Table,
  Card,
} from "react-bootstrap";
import { supabase } from "../clients/supabase";
import { Tags, UserUploadedFile } from "../types/relations";
import { Link, useSearchParams } from "react-router";

type ValidCourse = {
  course_number: number;
  course_subject: string;
  name: string;
};

export default function Home() {
  const [professorList, setProfessorList] = useState<string[]>([]);
  const [courseSubjectList, setCourseSubjectList] = useState<string[]>([]);
  const [courseNumberList, setCourseNumberList] = useState<string[]>([]);
  const [courseNameList, setCourseNameList] = useState<string[]>([]);
  const [tagList, setTagList] = useState<Tags[]>([]);

  const [professorSearch, setProfessorSearch] = useState("");
  const [courseNameSearch, setCourseNameSearch] = useState("");
  const [courseSubjectSearch, setCourseSubjectSearch] = useState("");
  const [courseNumberSearch, setCourseNumberSearch] = useState("");
  const [semesterSearch, setSemesterSearch] = useState("");
  const [descriptionSearch, setDescriptionSearch] = useState("");
  const [tagSearch, setTagSearch] = useState("");
  const [yearSearch, setYearSearch] = useState("");
  const [results, setResults] = useState<UserUploadedFile[]>([]);
  const [loading, setLoading] = useState(false);

  const validSemesters = ["Spring", "Summer", "Fall"];

  const [searchParams] = useSearchParams();

  useEffect(() => {
    const professor = searchParams.get("professor");
    const courseName = searchParams.get("courseName");
    const courseSubject = searchParams.get("courseSubject");
    const courseNumber = searchParams.get("courseNumber");
    if (professor) {
      setProfessorSearch(professor);
    }
    if (courseName) {
      setCourseNameSearch(courseName);
    }
    if (courseSubject) {
      setCourseSubjectSearch(courseSubject);
    }
    if (courseNumber) {
      setCourseNumberSearch(courseNumber);
    }
  }, [searchParams]);

  useEffect(() => {
    fetch("http://127.0.0.1:5001/courses/professors")
      .then((res) => res.json())
      .then((data) => {
        setProfessorList(data);
      });
  }, []);

  useEffect(() => {
    fetch("http://127.0.0.1:5001/courses/valid/subjects")
      .then((res) => res.json())
      .then((data) => {
        setCourseSubjectList(data);
      });
  }, []);

  useEffect(() => {
    if (courseSubjectSearch) {
      fetch(
        `http://127.0.0.1:5001/courses/valid?subject=${courseSubjectSearch}`
      )
        .then((res) => res.json())
        .then((data: ValidCourse[]) => {
          setCourseNumberList(
            data.map((course) => course.course_number.toString())
          );
          setCourseNameList(data.map((course) => course.name));
        });
    } else {
      setCourseNumberList([]);
      fetch("http://127.0.0.1:5001/courses/valid")
        .then((res) => res.json())
        .then((data: ValidCourse[]) => {
          setCourseNameList(data.map((course) => course.name));
        });
    }
  }, [courseSubjectSearch]);

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

  const handleSearch = async () => {
    console.log("Searching for syllabi...");
    setLoading(true);

    let query = supabase
      .from("uploads")
      .select(
        "id, semester, year, fileurl, courses!inner(course_number, course_subject, name), professors!inner(id, name, firebase_id), uploads_tags!inner(tag_id)"
      );

    if (professorSearch) {
      query = query.eq("professors.name", professorSearch);
    }
    if (courseNameSearch) {
      query = query.ilike("courses.name", `%${courseNameSearch}%`);
    }
    if (courseNumberSearch) {
      query = query.eq(
        "courses.course_number",
        parseInt(courseNumberSearch, 10)
      );
    }
    if (courseSubjectSearch) {
      query = query.eq("courses.course_subject", courseSubjectSearch);
    }
    if (semesterSearch) {
      query = query.eq("semester", semesterSearch);
    }
    if (yearSearch) {
      query = query.eq("year", parseInt(yearSearch, 10));
    }
    if (descriptionSearch) {
      query = query.textSearch(
        "courses.description",
        descriptionSearch.replace(/\s+/g, "+")
      );
    }
    if (tagSearch) {
      query = query.eq("uploads_tags.tag_id", tagSearch);
    }
    const { data, error } = await query;
    console.log("resp", professorSearch, data);
    if (error) {
      console.error("Error fetching syllabi:", error);
    } else {
      setResults(data || []);
    }
    setLoading(false);
  };

  const resetFilters = () => {
    setProfessorSearch("");
    setCourseSubjectSearch("");
    setCourseNumberSearch("");
    setCourseNameSearch("");
    setSemesterSearch("");
    setYearSearch("");
    setDescriptionSearch("");
  };

  return (
    <Container>
      <h1 className="my-4 text-center">📚 Syllabus Search</h1>

      <Card className="shadow-sm p-4 mb-4">
        <h4 className="mb-3">🔍 Search Filters</h4>

        <Row className="g-3">
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Professor</Form.Label>
              <Form.Select
                value={professorSearch}
                onChange={(e) => setProfessorSearch(e.target.value)}
              >
                <option value="">Select a professor</option>
                {professorList.map((prof) => (
                  <option key={prof} value={prof}>
                    {prof}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="courseSubjectSearch">
              <Form.Label>Course Subject</Form.Label>
              <Form.Select
                value={courseSubjectSearch}
                onChange={(e) => setCourseSubjectSearch(e.target.value)}
              >
                <option value="">Select Course Subject</option>
                {courseSubjectList.map((subject) => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="courseSearch">
              <Form.Label>Course Name</Form.Label>
              <Form.Select
                value={courseNameSearch}
                onChange={(e) => setCourseNameSearch(e.target.value)}
              >
                <option value="">Select Course Name</option>
                {courseNameList.map((course_name) => (
                  <option key={course_name} value={course_name}>
                    {course_name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Course Number</Form.Label>
              <Form.Select
                value={courseNumberSearch}
                onChange={(e) => {
                  setCourseNumberSearch(e.target.value);
                }}
                required
                disabled={!courseSubjectSearch}
              >
                <option value="">Select a number</option>
                {courseNumberList.map((course_number) => (
                  <option key={course_number} value={course_number}>
                    {course_number}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="descriptionSearch">
              <Form.Label>Description</Form.Label>
              <Form.Control
                type="text"
                value={descriptionSearch}
                onChange={(e) => setDescriptionSearch(e.target.value)}
              />
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="tagSearch">
              <Form.Label>Tag</Form.Label>
              <Form.Select
                value={tagSearch}
                onChange={(e) => setTagSearch(e.target.value)}
              >
                <option value="">Select Tag</option>
                {tagList.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
        </Row>
        <Row className="g-3 mt-2">
          <Col md={4}>
            <Form.Group controlId="semesterSearch">
              <Form.Label>Semester</Form.Label>
              <Form.Select
                value={semesterSearch}
                onChange={(e) => setSemesterSearch(e.target.value)}
              >
                <option value="">Select Semester</option>
                {validSemesters.map((sem) => (
                  <option key={sem} value={sem}>
                    {sem}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="yearSearch">
              <Form.Label>Year</Form.Label>
              <Form.Select
                value={yearSearch}
                onChange={(e) => setYearSearch(e.target.value)}
              >
                <option value="">Select Year</option>
                {[...Array(new Date().getFullYear() - 1999 + 3)].map((_, i) => (
                  <option
                    key={i}
                    value={(new Date().getFullYear() - i + 2).toString()}
                  >
                    {new Date().getFullYear() - i + 2}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>

          {/* Button Alignment */}
          <Col md={4} className="d-flex align-items-end">
            <Button
              variant="secondary"
              onClick={resetFilters}
              className="w-100"
            >
              Reset
            </Button>
          </Col>
        </Row>

        {/* Buttons are in a single row and properly aligned */}
        <Row className="mt-3">
          <Col className="text-center">
            <Button
              variant="primary"
              onClick={handleSearch}
              disabled={loading}
              className="px-4"
            >
              {loading ? "Searching..." : "Search"}
            </Button>
          </Col>
        </Row>
      </Card>

      {/* RESULTS TABLE */}
      <h2 className="text-center">Results</h2>
      {results.length > 0 ? (
        <Table striped bordered hover responsive className="mt-3">
          <thead>
            <tr>
              <th>Course Name</th>
              <th>Course Number</th>
              <th>Semester</th>
              <th>Year</th>
              <th>Professor</th>
              {/* <th>File</th> */}
            </tr>
          </thead>
          <tbody>
            {results.map((syllabus) => (
              <tr key={syllabus.id}>
                {/* <td>{syllabus.courses.name}</td> */}
                <td>
                  <Link to={`/details/${syllabus.id}`}>
                    {syllabus.courses.name}
                  </Link>
                </td>
                <td>{`${syllabus.courses.course_subject} ${syllabus.courses.course_number}`}</td>
                <td>{syllabus.semester || "N/A"}</td>
                <td>{syllabus.year || "N/A"}</td>
                <td>{syllabus.professors.name || "N/A"}</td>
                {/* <td>
                  <a
                    href={syllabus.fileurl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View File
                  </a>
                </td> */}
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <p className="text-center">No results found.</p>
      )}
    </Container>
  );
}
