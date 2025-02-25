// Signin.js
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function Signin({ setCurrentPage }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      setCurrentPage('main');
    } catch (error) {
      console.error('Failed to sign in', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Signin</h2>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Sign In</button>
    </form>
  );
}

export default Signin;