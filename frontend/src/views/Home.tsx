import React, { useState } from "react";
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
import { UserUploadedFile } from "../types/relations";

export default function Home() {
  const [professorSearch, setProfessorSearch] = useState("");
  const [courseSearch, setCourseSearch] = useState("");
  const [courseNumberSearch, setCourseNumberSearch] = useState("");
  const [semesterSearch, setSemesterSearch] = useState("");
  const [yearSearch, setYearSearch] = useState("");
  const [results, setResults] = useState<UserUploadedFile[]>([]);
  const [loading, setLoading] = useState(false);

  const validSemesters = ["Spring", "Summer", "Fall"];

  const handleSearch = async () => {
    console.log("Searching for syllabi...");
    setLoading(true);

    let query = supabase
      .from("uploads")
      .select(
        "id, semester, year, fileurl, courses(course_number, course_subject, name), professors(name, firebase_id)"
      );

    if (professorSearch) {
      query = query.ilike("uploaded_by_name", `%${professorSearch}%`);
    }
    if (courseSearch) {
      query = query.ilike("subname", `%${courseSearch}%`);
    }
    if (courseNumberSearch) {
      query = query.ilike("courseid", `%${courseNumberSearch}%`);
    }
    if (semesterSearch) {
      query = query.eq("semester", semesterSearch);
    }
    if (yearSearch) {
      query = query.eq("year", parseInt(yearSearch, 10));
    }

    const { data, error } = await query;
    if (error) {
      console.error("Error fetching syllabi:", error);
    } else {
      setResults(data || []);
    }
    setLoading(false);
  };

  const resetFilters = () => {
    setProfessorSearch("");
    setCourseSearch("");
    setCourseNumberSearch("");
    setSemesterSearch("");
    setYearSearch("");
  };

  return (
    <Container>
      <h1 className="my-4 text-center">📚 Syllabus Search</h1>

      <Card className="shadow-sm p-4 mb-4">
        <h4 className="mb-3">🔍 Search Filters</h4>

        <Row className="g-3">
          <Col md={4}>
            <Form.Group controlId="professorSearch">
              <Form.Label>Professor Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter professor name"
                value={professorSearch}
                onChange={(e) => setProfessorSearch(e.target.value)}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="courseSearch">
              <Form.Label>Course Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter course name"
                value={courseSearch}
                onChange={(e) => setCourseSearch(e.target.value)}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group controlId="courseNumberSearch">
              <Form.Label>Course Number</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter course number"
                value={courseNumberSearch}
                onChange={(e) => setCourseNumberSearch(e.target.value)}
              />
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
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {results.map((syllabus) => (
              <tr key={syllabus.id}>
                <td>{syllabus.courses.name}</td>
                <td>{`${syllabus.courses.course_subject} ${syllabus.courses.course_number}`}</td>
                <td>{syllabus.semester || "N/A"}</td>
                <td>{syllabus.year || "N/A"}</td>
                <td>{syllabus.professors.name || "N/A"}</td>
                <td>
                  <a
                    href={syllabus.fileurl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View File
                  </a>
                </td>
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
