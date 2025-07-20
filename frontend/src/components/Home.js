import React from 'react';
import { Link } from 'react-router-dom';

const Home = ({ user }) => {
  return (
    <div className="row justify-content-center">
      <div className="col-md-7 col-lg-6">
        <div className="card p-4 mb-4 fade-in">
          <h1 className="mb-3 text-center fw-bold" style={{ color: '#128c7e' }}>
            Welcome to WhatsApp Onboarding Portal
          </h1>
          <p className="lead text-center mb-4">
            Easily onboard your business and connect WhatsApp in a few steps.
          </p>
          <div className="d-flex justify-content-center gap-3">
            {user ? (
              <Link to="/dashboard" className="btn btn-main btn-lg px-4">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn btn-main btn-lg px-4">
                  Register
                </Link>
                <Link to="/login" className="btn btn-outline-success btn-lg px-4">
                  Login
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;