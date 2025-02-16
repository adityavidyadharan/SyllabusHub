// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import firebase from "firebase/compat/app";
import 'firebase/compat/auth';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyB--K5QvKICjhJnHIUvog9INnQmPH5DlTg",
  authDomain: "syllabushub-8c367.firebaseapp.com",
  projectId: "syllabushub-8c367",
  storageBucket: "syllabushub-8c367.firebasestorage.app",
  messagingSenderId: "85846263482",
  appId: "1:85846263482:web:bff92ec8fe093ccef16483"
};


// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);

// const provider = new firebase.auth.OAuthProvider('microsoft.com');
// provider.setCustomParameters({
//     tenant: '482198bb-ae7b-4b25-8b7a-6d7f32faa083'
// });




const uiConfig = {
    // Popup signin flow rather than redirect flow.
    signInFlow: 'popup',
    // Redirect to /signedIn after sign in is successful. Alternatively you can provide a callbacks.signInSuccess function.
    // signInSuccessUrl: '/login',
    // We will display Google and Facebook as auth providers.
    signInOptions: [
      'microsoft.com',
    ],
    callbacks: {
      signInSuccessWithAuthResult: (authResult: firebase.auth.UserCredential) => {
          // if (authResult.additionalUserInfo?.isNewUser) {
            console.log("New user");
            console.log(authResult.user?.uid);
            fetch('http://127.0.0.1:5001/users/new', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                user_id: authResult.user?.uid,
              })
            });
          // }
      }
    }
  };

export { app, uiConfig };