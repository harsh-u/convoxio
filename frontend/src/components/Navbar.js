import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = ({ user, onLogout }) => {
  return (
    <nav className="navbar navbar-expand-lg mb-4">
      <div className="container">
        <Link className="navbar-brand fw-bold" to="/">WhatsApp Onboarding</Link>
        <span className="navbar-text ms-auto">
          {user ? (
            <div className="d-flex align-items-center">
              <span className="me-3">Welcome, {user.email}</span>
              <button 
                onClick={onLogout} 
                className="btn btn-outline-light btn-sm"
              >
                Logout
              </button>
            </div>
          ) : (
            "Empowering Your Business"
          )}
        </span>
      </div>
    </nav>
  );
};

export default Navbar; 