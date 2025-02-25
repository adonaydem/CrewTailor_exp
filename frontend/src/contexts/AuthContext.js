// AuthContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth } from '../firebase/firebase';
import { onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

// Create a context for authentication
const AuthContext = createContext();

// Custom hook to use the AuthContext
export const useAuth = () => {
  return useContext(AuthContext);
};

// AuthProvider component to wrap around parts of your app that need access to the authentication state
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Effect to subscribe to authentication state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user);
      setLoading(false);
    });

    // Cleanup subscription on unmount
    return unsubscribe;
  }, []);

  // Function to handle user login
  const login = async (email, password) => {
    if (!email || !password) {
      throw new Error('Email and password are required');
    }
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error) {
      console.error('Failed to login:', error);
      throw error;
    }
  };

  // Function to handle user signup
  const signup = async (email, password) => {
    if (!email || !password) {
      throw new Error('Email and password are required');
    }
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      return userCredential;
    } catch (error) {
      console.error('Failed to sign up:', error);
      throw error;
    }
  };

  // Function to handle user logout
  const logout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Failed to logout:', error);
      throw error;
    }
  };

  // Value to be provided by the AuthContext
  const value = {
    currentUser,
    login,
    signup,
    logout,
  };

  // Ensure children are only rendered after loading is complete
  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};