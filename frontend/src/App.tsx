import "./App.css";
import { BrowserRouter, Route, Routes } from "react-router";
import Login from "./views/Login";
import Home from "./views/Home";
import Navbar from "./components/Navbar";
import FileUpload from "./views/FileUpload";  // Import FileUpload

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/upload" element={<FileUpload />} /> {/* Add this line */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
