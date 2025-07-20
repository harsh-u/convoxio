import React, { useState } from 'react';
import axios from 'axios';

const WhatsAppDiagnostic = ({ user }) => {
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(false);

  const runDiagnostics = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/diagnose-whatsapp');
      setDiagnostics(response.data);
    } catch (error) {
      console.error('Diagnostic error:', error);
      setDiagnostics({ error: error.response?.data?.error || 'Failed to run diagnostics' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-4 fade-in mb-4">
      <h4 className="mb-3">🔧 WhatsApp API Diagnostics</h4>
      <button 
        onClick={runDiagnostics} 
        className="btn btn-outline-primary mb-3"
        disabled={loading}
      >
        {loading ? 'Running Diagnostics...' : 'Run Diagnostics'}
      </button>

      {diagnostics && (
        <div className="mt-3">
          <h5>Diagnostic Results:</h5>
          <pre className="bg-light p-3 rounded" style={{ fontSize: '12px', maxHeight: '400px', overflow: 'auto' }}>
            {JSON.stringify(diagnostics, null, 2)}
          </pre>
          
          {diagnostics.error && (
            <div className="alert alert-danger mt-3">
              <strong>Error:</strong> {diagnostics.error}
            </div>
          )}

          {diagnostics.waba_test && (
            <div className="mt-3">
              <h6>WhatsApp Business Account Test:</h6>
              <div className={`badge ${diagnostics.waba_test.status_code === 200 ? 'bg-success' : 'bg-danger'}`}>
                Status: {diagnostics.waba_test.status_code}
              </div>
            </div>
          )}

          {diagnostics.phone_test && (
            <div className="mt-3">
              <h6>Phone Number Test:</h6>
              <div className={`badge ${diagnostics.phone_test.status_code === 200 ? 'bg-success' : 'bg-danger'}`}>
                Status: {diagnostics.phone_test.status_code}
              </div>
            </div>
          )}

          {diagnostics.templates_test && (
            <div className="mt-3">
              <h6>Templates Test:</h6>
              <div className={`badge ${diagnostics.templates_test.status_code === 200 ? 'bg-success' : 'bg-danger'}`}>
                Status: {diagnostics.templates_test.status_code}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WhatsAppDiagnostic; 