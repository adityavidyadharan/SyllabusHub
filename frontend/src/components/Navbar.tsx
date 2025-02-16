import { Link, useLocation } from "react-router-dom";
import "../App.css";

function Navbar() {
  const location = useLocation(); // Get the current route

  return (
    <nav className="navbar">
      <ul className="nav-list">
        <li className="nav-item">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
          >
            Home
          </Link>
        </li>
        <li className="nav-item">
          <Link 
            to="/login" 
            className={`nav-link ${location.pathname === "/login" ? "active" : ""}`}
          >
            Login
          </Link>
        </li>
        <li className="nav-item">
          <Link 
            to="/upload" 
            className={`nav-link ${location.pathname === "/upload" ? "active" : ""}`}
          >
            File Upload
          </Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
