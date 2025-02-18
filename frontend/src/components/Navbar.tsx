import { Navbar as BNavbar, Container, Nav } from "react-bootstrap";
import { Link } from "react-router";
import LoginDropdown from "./LoginDropdown";
import firebase from "firebase/compat/app";
import { useState, useEffect } from "react";

function Navbar() {
  // const location = useLocation(); // Get the current route
  const [loggedIn, setLoggedIn] = useState<boolean>(false);
  const [isProfessor, setIsProfessor] = useState<boolean>(false);
  
  useEffect(() => {
      firebase.auth().onAuthStateChanged(user => {
          setLoggedIn(!!user);
          if (user) {
              user.getIdTokenResult().then(idTokenResult => {
                console.log(idTokenResult.claims.role);
                  if (idTokenResult.claims.role === "professor") {
                      setIsProfessor(true);
                  } else {
                      setIsProfessor(false);
                  }
              });
          }
      });
    }, []);

  useEffect(() => {
      firebase.auth().onAuthStateChanged(user => {
          setLoggedIn(!!user);
      });
  }, []);

  return (
    <BNavbar bg="primary" expand="lg">
      <Container>
        <BNavbar.Toggle aria-controls="basic-navbar-nav" />
        <BNavbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">
              Home
            </Nav.Link>
          </Nav>
          {!loggedIn && (
            <Nav className="me-auto">
              <Nav.Link as={Link} to="/login">
                Login
              </Nav.Link>
            </Nav>
          )}
          {isProfessor && (
            <Nav className="me-auto">
              <Nav.Link as={Link} to="/upload">
                File Upload
              </Nav.Link>
            </Nav>
          )}
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/files">
              View Files
            </Nav.Link>
          </Nav>
        </BNavbar.Collapse>
        <BNavbar.Collapse className="justify-content-end">
          <LoginDropdown />
        </BNavbar.Collapse>
      </Container>
    </BNavbar>

    // <nav className="navbar">
    //   <ul className="nav-list">
    //     <li className="nav-item">
    //       <Link
    //         to="/"
    //         className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
    //       >
    //         Home
    //       </Link>
    //     </li>
    //     <li className="nav-item">
    //       <Link
    //         to="/login"
    //         className={`nav-link ${location.pathname === "/login" ? "active" : ""}`}
    //       >
    //         Login
    //       </Link>
    //     </li>
    //     <li className="nav-item">
    //       <Link
    //         to="/upload"
    //         className={`nav-link ${location.pathname === "/upload" ? "active" : ""}`}
    //       >
    //         File Upload
    //       </Link>
    //     </li>
    //     <li className="nav-item">
    //       <Link
    //         to="/files"
    //         className={`nav-link ${location.pathname === "/files" ? "active" : ""}`}
    //       >
    //         View Files
    //       </Link>
    //     </li>
    //   </ul>
    // </nav>
  );
}

export default Navbar;
