import firebase from "firebase/compat/app";
import { useEffect, useState } from "react";
import { Button, NavDropdown } from "react-bootstrap";
import { Person } from "react-bootstrap-icons";
import { Link } from "react-router";

export default function LoginDropdown() {
    const [user, setUser] = useState<string | null>(null);
    const [loggedIn, setLoggedIn] = useState<boolean>(false);
    
    useEffect(() => {
        firebase.auth().onAuthStateChanged(user => {
            setUser(user?.displayName || null);
            setLoggedIn(!!user);
        });
    }, []);

    useEffect(() => {
        firebase.auth().onAuthStateChanged(user => {
            setUser(user?.displayName || "");
        });
    }, []);

    
    return (
        <NavDropdown title={<span><Person /> {user || "Guest"}</span>}>
            {/* Show Profile and Sign Out only if logged in */}
            {loggedIn ? (
                <>
                    <NavDropdown.Item as={Link} to="/login">
                        Profile
                    </NavDropdown.Item>
                    <NavDropdown.Item>
                        <Button variant="link" onClick={() => firebase.auth().signOut()}>
                            Sign Out
                        </Button>
                    </NavDropdown.Item>
                </>
            ) : (
                /* Show Login only if not logged in */
                <NavDropdown.Item as={Link} to="/login">
                    Login
                </NavDropdown.Item>
            )}
        </NavDropdown>
    )
}