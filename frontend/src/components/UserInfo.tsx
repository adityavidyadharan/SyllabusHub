import firebase from "firebase/compat/app";
import { useState, useEffect } from "react";
import { Badge, Container, Row } from "react-bootstrap";
import { app } from "../firebase/firebase";

export default function UserInfo() {
        const [role, setRole] = useState("");
    
        useEffect(() => {
            app.auth().onAuthStateChanged(user => {
                console.log(user);
                if (user) {
                    user.getIdTokenResult().then(idTokenResult => {
                        setRole(idTokenResult.claims.role);
                    });
                }
            });
        }, []);

    return (
        <Container>
            <Row>
                <p>Signed in as: {firebase.auth().currentUser?.displayName}</p>
            </Row>
            <Row>
                <p>Email: {firebase.auth().currentUser?.email}</p>
            </Row>
            <Row>
                <p>User Type: <Badge bg="primary">{role}</Badge></p> 
            </Row>
        </Container>
    )
}