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
        // Person logo and name as a dropdown
        <NavDropdown title={<span><Person /> {user}</span>}>
            <NavDropdown.Item as={Link} to="/login">
                {loggedIn ? 
                <Button variant="link" onClick={() => firebase.auth().signOut()}>Sign Out</Button> :
                <Link to="/login">Login</Link>}
            </NavDropdown.Item>
        </NavDropdown>
    )
}