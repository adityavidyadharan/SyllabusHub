import { Navbar as BNavbar, Container, Nav } from "react-bootstrap";
import { Link } from "react-router";
import LoginDropdown from "./LoginDropdown";

export default function Navbar() {
    return (
        <BNavbar bg="light" expand="lg">
            <Container>
                <BNavbar.Toggle aria-controls="basic-navbar-nav" />
                <BNavbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto">
                        <Nav.Link as={Link} to="/">Home</Nav.Link>
                    </Nav>
                </BNavbar.Collapse>
                <BNavbar.Collapse className="justify-content-end">
                    <LoginDropdown />
                </BNavbar.Collapse>
            </Container>
        </BNavbar>
    )
}