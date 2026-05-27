// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCeyQqwDhBmPAk6kjNDlQpzzH-t2bTDXF8",
  authDomain: "dream-analytica.firebaseapp.com",
  projectId: "dream-analytica",
  storageBucket: "dream-analytica.appspot.com",
  messagingSenderId: "337126397798",
  appId: "1:337126397798:web:77b3a97c541a73c122daa7",
  measurementId: "G-5SBPJBQXXJ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);