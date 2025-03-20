import "./App.css";
import { BrowserRouter, Route, Routes } from "react-router"; // ✅ Correct Import
import Login from "./views/Login";
import Home from "./views/Home";
import Navbar from "./components/Navbar";
import FileUpload from "./views/FileUpload";
import ViewFiles from "./views/ViewFiles"; // ✅ Import ViewFiles
import { initializeApp } from "./clients/firebase";
import UploadDetails from "./views/UploadDetails";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function App() {
  initializeApp();
  const queryClient = new QueryClient();

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<FileUpload />} />
          <Route path="/files" element={<ViewFiles />} />
          <Route path="/details/:uploadId" element={<UploadDetails />} />
        </Routes>
      </QueryClientProvider>
    </BrowserRouter>
  );
}

export default App;
