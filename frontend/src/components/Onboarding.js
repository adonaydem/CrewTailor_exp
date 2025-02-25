import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Onboarding.css';
import logo from '../static/logo4.png';
function Onboarding() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [email2, setEmail2] = useState('');
    const [password2, setPassword2] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [need, setNeed] = useState('leisure');
    const { signup, login } = useAuth();
    const navigate = useNavigate();
    const [signupStep, setSignupStep] = useState(0);
    const [signinStep, setSigninStep] = useState(0);
    const BackendUrl = process.env.REACT_APP_BACKEND_URL;
    const [signinError, setSigninError] = useState('');
    const [signupError, setSignupError] = useState('');
    const [showErrorPopup, setShowErrorPopup] = useState(false);
    const [isLoading, setIsLoading] = useState(false); // Loading state

    const signinContainerRef = useRef(null);
    const signupContainerRef = useRef(null);

    const getFriendlyErrorMessage = (error) => {
        console.log(error.code);
        switch (error.code) {
            case 'auth/invalid-credential':
                return 'Invalid email or password. Please try again.';
            case 'auth/invalid-email':
                return 'Invalid email format';
            case 'auth/user-not-found':
                return 'No account found with this email. Please sign up.';
            case 'auth/wrong-password':
                return 'Incorrect password. Please try again.';
            case 'auth/weak-password':
                return 'Please use a strong password.';
            case 'auth/network-request-failed':
                return 'Connection error. Please try again.';
            case 'auth/email-already-in-use':
                return 'The email address is already in use, please use other credentials.';
            default:
                return 'An unexpected error occurred. Please try again later.';
        }
    };

    const handleSubmitSignup = async (e) => {
        e.preventDefault();
        setSignupError('');
        setIsLoading(true); // Start loading
        try {
            const userCredential = await signup(email2, password2);
            const userId = userCredential.user.uid;

            // Save additional details to MongoDB
            const response = await fetch(`${BackendUrl}/add_user`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    uid: userId,
                    email: email2,
                    firstname: firstName,
                    lastname: lastName,
                    need: need,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save user details');
            }

            navigate('/');
        } catch (error) {
            console.log("err:", error.message);
            const friendlyError = getFriendlyErrorMessage(error);
            setSignupError(friendlyError);
            setShowErrorPopup(true);
        } finally {
            setIsLoading(false); // Stop loading
        }
    };

    const handleSubmitSignin = async (e) => {
        e.preventDefault();
        setSigninError('');
        setIsLoading(true); // Start loading
        try {
            await login(email, password);
            navigate('/');
        } catch (error) {
            console.log("err:", error.message);
            const friendlyError = getFriendlyErrorMessage(error);
            setSigninError(friendlyError);
            setShowErrorPopup(true);
        } finally {
            setIsLoading(false); // Stop loading
        }
    };

    const handleNextSignupStep = (e) => {
        e.preventDefault();
        setSignupStep(signupStep + 1);
    };

    const handleNextSigninStep = (e) => {
        e.preventDefault();
        setSigninStep(signinStep + 1);
    };

    useEffect(() => {
        if (signinContainerRef.current) {
            signinContainerRef.current.scrollTop = signinContainerRef.current.scrollHeight;
        }
    }, [signinStep]);

    useEffect(() => {
        if (signupContainerRef.current) {
            signupContainerRef.current.scrollTop = signupContainerRef.current.scrollHeight;
        }
    }, [signupStep]);

    return (
        <div className="onboarding-container">
           <div className="onboarding-wrapper">
            <div className="onboarding-header">
                <img src={logo} alt="CrewTailor Logo" className="onboarding-logo" />
                <h1>CrewTailor</h1>
            </div>
            <div className="onboarding-motto">
                <p>Recruit The Future!</p>
            </div>
           </div>


            <div className="onboarding-form-wrapper custom-scrollbar">
                <div className="onboarding-signin-container custom-scrollbar" ref={signinContainerRef}>
                    <h2>Signin</h2>
                    <form className="onboarding-form custom-scrollbar" onSubmit={handleSubmitSignin}>
                        {signinStep >= 0 && (
                            <>
                                <p className="onboarding-paragraph">PAM: What is your email?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="Email"
                                            required
                                            autoFocus={signinStep === 0}
                                        />
                                    </div>
                                </div>
                                {signinStep === 0 && <button className="onboarding-button" onClick={handleNextSigninStep}>Next</button>}
                            </>
                        )}
                        {signinStep >= 1 && (
                            <>
                                <p className="onboarding-paragraph">PAM: What is your password?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="Password"
                                            required
                                            autoFocus={signinStep === 1}
                                        />
                                    </div>
                                </div>
                                {signinStep === 1 && <button className="onboarding-button" type="submit">Sign In</button>}
                            </>
                        )}
                    </form>
                </div>
                <div className="onboarding-separator" />
                <div className="onboarding-signup-container" ref={signupContainerRef}>
                    <h2>Signup</h2>
                    <form className="onboarding-form" onSubmit={handleSubmitSignup}>
                        {signupStep >= 0 && (
                            <>
                                <p className="onboarding-paragraph">PAM: Welcome! If you are new, I am going to ask you some questions.</p>
                                <p className="onboarding-paragraph">What is your first name?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="text"
                                            value={firstName}
                                            onChange={(e) => setFirstName(e.target.value)}
                                            placeholder="First Name"
                                            required
                                            autoFocus={signinStep === 0}
                                        />
                                    </div>
                                </div>
                                {signupStep === 0 && <button className="onboarding-button" onClick={handleNextSignupStep}>Next</button>}
                            </>
                        )}
                        {signupStep >= 1 && (
                            <>
                                <p className="onboarding-paragraph">PAM: What is your last name?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="text"
                                            value={lastName}
                                            onChange={(e) => setLastName(e.target.value)}
                                            placeholder="Last Name"
                                            required
                                            autoFocus
                                        />
                                    </div>
                                </div>
                                {signupStep === 1 && <button className="onboarding-button" onClick={handleNextSignupStep}>Next</button>}
                            </>
                        )}
                        {signupStep >= 2 && (
                            <>
                                <p className="onboarding-paragraph">PAM: What is your email?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="email"
                                            value={email2}
                                            onChange={(e) => setEmail2(e.target.value)}
                                            placeholder="Email"
                                            required
                                            autoFocus
                                        />
                                    </div>
                                </div>
                                {signupStep === 2 && <button className="onboarding-button" onClick={handleNextSignupStep}>Next</button>}
                            </>
                        )}
                        {signupStep >= 3 && (
                            <>
                                <p className="onboarding-paragraph">PAM: Create a password</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <input
                                            className="onboarding-input"
                                            type="password"
                                            value={password2}
                                            onChange={(e) => setPassword2(e.target.value)}
                                            placeholder="Password"
                                            required
                                            autoFocus
                                        />
                                    </div>
                                </div>
                                {signupStep === 3 && <button className="onboarding-button" onClick={handleNextSignupStep}>Next</button>}
                            </>
                        )}
                        {signupStep >= 4 && (
                            <>
                                <p className="onboarding-paragraph">PAM: What is your need?</p>
                                <div className="input-group">
                                    <div className="input-field">
                                        <select
                                            className="onboarding-select"
                                            value={need}
                                            onChange={(e) => setNeed(e.target.value)}
                                        >
                                            <option value="leisure">Leisure</option>
                                            <option value="student">Student</option>
                                            <option value="work">Work</option>
                                        </select>
                                    </div>
                                </div>
                                {signupStep === 4 && <button className="onboarding-button" type="submit">Sign Up</button>}
                            </>
                        )}
                    </form>
                </div>
            </div>
            {showErrorPopup && (
                <div className="error-popup">
                    <div className="error-popup-content">
                        <p>{signinError || signupError}</p>
                        <button className="onboarding-popup-button" onClick={() => setShowErrorPopup(false)}>Close</button>
                    </div>
                </div>
            )}
            {isLoading && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                </div>
            )}
        </div>
    );
}

export default Onboarding;