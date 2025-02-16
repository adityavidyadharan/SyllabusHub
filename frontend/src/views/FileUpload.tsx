import { useState } from "react";

function FileUpload() {
  const [courseNumber, setCourseNumber] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [credits, setCredits] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!file) {
      setMessage("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setMessage("");

    // Prepare Form Data
    const formData = new FormData();
    formData.append("courseNumber", courseNumber);
    formData.append("subjectName", subjectName);
    formData.append("credits", credits);
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setMessage("File uploaded successfully!");
        setCourseNumber("");
        setSubjectName("");
        setCredits("");
        setFile(null);
      } else {
        setMessage(result.error || "File upload failed.");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessage("Error uploading file. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2>Upload a File</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Course Number:</label>
          <input
            type="text"
            value={courseNumber}
            onChange={(e) => setCourseNumber(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Subject Name:</label>
          <input
            type="text"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Number of Credits:</label>
          <input
            type="number"
            value={credits}
            onChange={(e) => setCredits(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Upload File (PDF or DOCX123):</label>
          <input type="file" accept=".pdf,.docx" onChange={handleFileChange} required />
        </div>
        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading..." : "Submit"}
        </button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}

export default FileUpload;
