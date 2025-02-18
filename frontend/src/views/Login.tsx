import { StyledFirebaseAuth } from "react-firebaseui";
import { uiConfig } from "../firebase/firebase";
import firebase from "firebase/compat/app";
import { useState } from "react";
import { Button } from "react-bootstrap";
import UserInfo from "../components/UserInfo";

export default function Login() {
    const [signedIn, setSignedIn] = useState(false);


    // console.log(firebase.auth().currentUser);
    // print out the custom claims of the user
    // firebase.auth().currentUser?.getIdTokenResult().then((idTokenResult) => {
    //     console.log(idTokenResult.claims);
    // }  );

    firebase.auth().onAuthStateChanged(user => {
        setSignedIn(!!user);
    });
    
    return (
        <div>
            <h1>Login</h1>
            {
                !signedIn && <StyledFirebaseAuth uiConfig={uiConfig} firebaseAuth={firebase.auth()} />
            }
            {
                signedIn &&
                <div>
                    <UserInfo />
                    <Button variant="secondary" onClick={() => firebase.auth().signOut()}>Sign Out</Button>
                </div>
            }
            
        </div>
    )
}