import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  Card,
  Spinner,
  Alert,
  Accordion
} from "react-bootstrap";
import ReactMarkdown from 'react-markdown';

export default function Recommendations() {
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [userSkills, setUserSkills] = useState("");
  const [seniorityLevel, setSeniorityLevel] = useState("Mid-Level");
  const [apiKey, setApiKey] = useState("");
  const [recommendations, setRecommendations] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [errorDetails, setErrorDetails] = useState("");
  const [relevantMajors, setRelevantMajors] = useState([]);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  // Load API key from localStorage on component mount
  useEffect(() => {
    const savedApiKey = localStorage.getItem("geminiApiKey");
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }
  }, []);

  // Save API key to localStorage when it changes
  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("geminiApiKey", apiKey);
    }
  }, [apiKey]);

  // Fetch relevant majors when job title changes
  useEffect(() => {
    if (jobTitle.trim()) {
      fetchRelevantMajors(jobTitle);
    } else {
      setRelevantMajors([]);
    }
  }, [jobTitle]);

  const fetchRelevantMajors = async (title) => {
    if (!title) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:5001/rec/relevant-majors?jobTitle=${encodeURIComponent(title)}`);
      if (response.ok) {
        const data = await response.json();
        setRelevantMajors(data.relevantMajors || []);
      }
    } catch (err) {
      console.error("Error fetching relevant majors:", err);
    }
  };

  const configureApi = async () => {
    if (!apiKey) return false;
    
    try {
      const response = await fetch("http://127.0.0.1:5001/rec/configure", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          apiKey: apiKey,
          apiType: "gemini",
          modelName: "models/gemini-2.0-flash-lite"
        }),
      });
      
      return response.ok;
    } catch (err) {
      console.error("Error configuring API:", err);
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!apiKey) {
      setError("Please enter your Gemini API key in the Advanced Settings section");
      setShowAdvancedSettings(true);
      return;
    }
    
    setLoading(true);
    setError("");
    setErrorDetails("");
    setRecommendations("");
    
    try {
      // First configure the API
      await configureApi();
      
      // Then get recommendations
      const response = await fetch("http://127.0.0.1:5001/rec/getrec", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jobTitle,
          jobDescription,
          userSkills,
          seniorityLevel,
          apiKey // Send API key with each request
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || "Failed to get recommendations");
      }
      
      if (data.error) {
        setError(data.error);
        setErrorDetails(data.details || "");
      } else if (!data.recommendations || data.recommendations.trim() === "") {
        setError("No recommendations were returned. Please try a different job description.");
      } else {
        setRecommendations(data.recommendations);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <h1 className="my-4 text-center">Course Recommender</h1>
      
      <Accordion className="mb-4" activeKey={showAdvancedSettings ? "0" : null}>
        <Accordion.Item eventKey="0">
          <Accordion.Header onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}>
            Advanced Settings
          </Accordion.Header>
          <Accordion.Body>
            <Form.Group className="mb-3">
              <Form.Label>
                <strong>Gemini API Key</strong>
                <span className="text-danger"> *</span>
              </Form.Label>
              <Form.Control
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Gemini API key"
              />
              <Form.Text className="text-muted">
                Your API key is required for skill extraction. 
                Get a key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a>.
                It will be saved locally for convenience.
              </Form.Text>
            </Form.Group>
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
      
      <Card className="shadow-sm p-4 mb-4">
        <h4 className="mb-3">Enter Job Details</h4>
        
        <Form onSubmit={handleSubmit}>
          <Row className="g-3">
            <Col md={12}>
              <Form.Group className="mb-3">
                <Form.Label>Job Title</Form.Label>
                <Form.Control
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  required
                  placeholder="e.g., Data Scientist"
                />
              </Form.Group>
              
              {relevantMajors.length > 0 && (
                <div className="mb-3">
                  <small className="text-muted">
                    Relevant academic areas: {relevantMajors.join(", ")}
                  </small>
                </div>
              )}
            </Col>
            {/*
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Seniority Level</Form.Label>
                <Form.Select
                  value={seniorityLevel}
                  onChange={(e) => setSeniorityLevel(e.target.value)}
                >
                  <option value="Entry-Level">Entry-Level</option>
                  <option value="Mid-Level">Mid-Level</option>
                  <option value="Senior">Senior</option>
                </Form.Select>
              </Form.Group>
            </Col>
            */}
            <Col md={12}>
              <Form.Group className="mb-3">
                <Form.Label>Job Description</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={5}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  required
                  placeholder="Paste job description here..."
                />
              </Form.Group>
            </Col>
            
            <Col md={12}>
              <Form.Group className="mb-3">
                <Form.Label>Additional Skills (comma-separated)</Form.Label>
                <Form.Control
                  type="text"
                  value={userSkills}
                  onChange={(e) => setUserSkills(e.target.value)}
                  placeholder="e.g., Python, AWS, TensorFlow"
                />
              </Form.Group>
            </Col>
          </Row>
          
          <div className="text-center mt-3">
            <Button
              variant="primary"
              type="submit"
              disabled={loading}
              className="px-4"
            >
              {loading ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                  />
                  {" "}Processing...
                </>
              ) : (
                "Get Course Recommendations"
              )}
            </Button>
          </div>
        </Form>
      </Card>
      
      {error && (
        <Alert variant="danger">
          <Alert.Heading>Error</Alert.Heading>
          <p>{error}</p>
          {errorDetails && (
            <Accordion>
              <Accordion.Item eventKey="0">
                <Accordion.Header>Error Details</Accordion.Header>
                <Accordion.Body>
                  <pre style={{ whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'auto' }}>
                    {errorDetails}
                  </pre>
                </Accordion.Body>
              </Accordion.Item>
            </Accordion>
          )}
        </Alert>
      )}
      
      {loading && (
        <div className="text-center my-5">
          <Spinner animation="border" role="status" />
          <p className="mt-2">Generating course recommendations...<br/>
          <small className="text-muted">This may take up to 30 seconds.</small></p>
        </div>
      )}
      
      {recommendations && (
        <Card className="shadow-sm p-4">
          <h4 className="mb-3">📋 Course Recommendations</h4>
          <div className="recommendations-content">
            <ReactMarkdown>{recommendations}</ReactMarkdown>
          </div>
          <div className="text-center mt-3">
            <Button
              variant="outline-primary"
              onClick={() => {
                const blob = new Blob([recommendations], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${jobTitle.replace(/\s+/g, '_')}_course_recommendations.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
              }}
            >
              Download Recommendations
            </Button>
          </div>
        </Card>
      )}
    </Container>
  );
}