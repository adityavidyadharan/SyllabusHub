import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Table } from 'react-bootstrap';
import { supabase } from '../clients/supabase';
import { FileData } from '../types/FileTypes';

export default function Home () {
  const [professorSearch, setProfessorSearch] = useState('');
  const [courseSearch, setCourseSearch] = useState('');
  const [results, setResults] = useState<FileData[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    console.log('Searching for syllabi...');
    setLoading(true);
    
    let query = supabase.from<FileData>('uploads').select('*');

    if (professorSearch) {
      query = query.ilike('uploaded_by_name', `%${professorSearch}%`);
    }
    if (courseSearch) {
      query = query.ilike('subname', `%${courseSearch}%`);
    }
    console.log('Query:', query);

    const { data, error } = await query;
    if (error) {
      console.error('Error fetching syllabi:', error);
    } else {
      setResults(data || []);
    }
    setLoading(false);
  };

  return (
    <Container>
      <h1 className="my-4">Syllabus Search</h1>
      <Row>
        <Col md={6}>
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
        <Col md={6}>
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
      </Row>
      <Button className="mt-3" variant="primary" onClick={handleSearch} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </Button>
      <hr />
      <h2>Results</h2>
      {results.length > 0 ? (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>ID</th>
              <th>Course ID</th>
              <th>Course Name</th>
              <th>Credits</th>
              <th>Professor Name</th>
              <th>File URL</th>
            </tr>
          </thead>
          <tbody>
            {results.map((syllabus) => (
              <tr key={syllabus.id}>
                <td>{syllabus.id}</td>
                <td>{syllabus.courseid}</td>
                <td>{syllabus.subname}</td>
                <td>{syllabus.credits}</td>
                <td>{syllabus.uploaded_by_name}</td>
                <td>
                  <a href={syllabus.fileurl} target="_blank" rel="noopener noreferrer">
                    View
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <p>No results found.</p>
      )}
    </Container>
  );
};
