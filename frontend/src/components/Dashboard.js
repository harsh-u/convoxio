import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import WhatsAppDiagnostic from './WhatsAppDiagnostic';

const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [messageLoading, setMessageLoading] = useState(false);
  const [messageForm, setMessageForm] = useState({
    recipient: '',
    template_id: '',
    language: 'en_US'
  });
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/dashboard');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    setUploadLoading(true);

    const formData = new FormData();
    const panFile = document.getElementById('pan_file').files[0];
    const gstFile = document.getElementById('gst_file').files[0];

    if (panFile) formData.append('pan_file', panFile);
    if (gstFile) formData.append('gst_file', gstFile);

    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      addAlert('Documents uploaded successfully!', 'success');
      fetchDashboardData();
    } catch (error) {
      addAlert(error.response?.data?.error || 'Upload failed', 'danger');
    } finally {
      setUploadLoading(false);
    }
  };

  const startOnboarding = async () => {
    try {
      const response = await axios.get('/onboard/start');
      window.location.href = response.data.oauth_url;
    } catch (error) {
      addAlert(error.response?.data?.error || 'Failed to start onboarding', 'danger');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    setMessageLoading(true);

    try {
      await axios.post('/send-message', messageForm);
      addAlert('Message sent successfully!', 'success');
      setMessageForm({ recipient: '', template_id: '', language: 'en_US' });
      fetchDashboardData();
    } catch (error) {
      addAlert(error.response?.data?.error || 'Failed to send message', 'danger');
    } finally {
      setMessageLoading(false);
    }
  };

  const addAlert = (message, type) => {
    const id = Date.now();
    setAlerts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(alert => alert.id !== id));
    }, 5000);
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center">
        <div className="spinner-border text-success" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return <div>Error loading dashboard</div>;
  }

  return (
    <div>
      {alerts.map(alert => (
        <div key={alert.id} className={`alert alert-${alert.type} alert-dismissible fade show`} role="alert">
          {alert.message}
          <button type="button" className="btn-close" onClick={() => setAlerts(prev => prev.filter(a => a.id !== alert.id))}></button>
        </div>
      ))}

      <div className="row justify-content-center g-4">
        {/* Left Column: Uploads */}
        <div className="col-lg-6">
          <div className="card p-4 fade-in mb-4">
            <h4 className="mb-3">
              📤 Upload Business Documents
            </h4>
            <form onSubmit={handleFileUpload} className="mb-3">
              <div className="row g-3">
                <div className="col-md-6">
                  <label htmlFor="pan_file" className="form-label">Upload PAN</label>
                  <input type="file" className="form-control" id="pan_file" accept=".pdf,.jpg,.png,.jpeg" />
                </div>
                <div className="col-md-6">
                  <label htmlFor="gst_file" className="form-label">Upload GST</label>
                  <input type="file" className="form-control" id="gst_file" accept=".pdf,.jpg,.png,.jpeg" />
                </div>
              </div>
              <div className="d-grid mt-3">
                <button type="submit" className="btn btn-main btn-lg" disabled={uploadLoading}>
                  {uploadLoading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
            {dashboardData.docs_uploaded ? (
              <div className="alert alert-success mt-2">Documents uploaded. Please proceed with WhatsApp Setup.</div>
            ) : (
              <div className="alert alert-info mt-2">Upload both PAN and GST to continue.</div>
            )}
          </div>

          <div className="card p-4 fade-in mb-4">
            <h5 className="mb-3">📁 Your Uploaded Documents</h5>
            {dashboardData.uploads.length > 0 ? (
              <ul className="list-group">
                {dashboardData.uploads.map(upload => (
                  <li key={upload.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <span>{upload.filetype}</span>
                    <span className="fw-bold">{upload.filename}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-muted">No documents uploaded yet.</div>
            )}
          </div>
        </div>

        {/* Right Column: WhatsApp */}
        <div className="col-lg-6">
          <div className="card p-4 fade-in mb-4">
            <h4 className="mb-3">
              📱 WhatsApp Business Setup
            </h4>
            {!dashboardData.docs_uploaded ? (
              <div className="alert alert-warning">Please upload your business documents to enable WhatsApp onboarding.</div>
            ) : dashboardData.user.onboarding_status !== 'Verified' ? (
              <div>
                <p>Connect your WhatsApp Business Account to enable messaging features.</p>
                <button onClick={startOnboarding} className="btn btn-outline-success btn-lg mb-2">
                  🔗 Start WhatsApp Setup via Meta
                </button>
                <div className="mt-2">
                  <span className="badge bg-info">Status: {dashboardData.user.onboarding_status}</span>
                </div>
              </div>
            ) : (
              <div>
                <div className="alert alert-success">WhatsApp onboarding complete! You can now send messages.</div>
                <div className="mt-2">
                  <span className="badge bg-success">Status: {dashboardData.user.onboarding_status}</span>
                </div>
              </div>
            )}
          </div>

          <div className="card p-4 fade-in mb-4">
            <h4 className="mb-3">
              💬 Send WhatsApp Test Message
            </h4>
            {dashboardData.can_send ? (
              <form onSubmit={handleSendMessage} className="mb-2">
                <div className="row g-2">
                  <div className="col-md-6">
                    <label htmlFor="recipient" className="form-label">Phone Number (with country code)</label>
                    <input
                      type="text"
                      className="form-control"
                      id="recipient"
                      value={messageForm.recipient}
                      onChange={(e) => setMessageForm({...messageForm, recipient: e.target.value})}
                      placeholder="+1234567890"
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="template" className="form-label">Template</label>
                    <select
                      className="form-select"
                      id="template"
                      value={messageForm.template_id}
                      onChange={(e) => setMessageForm({...messageForm, template_id: e.target.value})}
                      required
                    >
                      <option value="">Select Template</option>
                      {dashboardData.templates.map(template => (
                        <option key={template.id} value={template.id}>
                          {template.name} ({template.status})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="d-grid mt-3">
                  <button type="submit" className="btn btn-main btn-lg" disabled={messageLoading}>
                    {messageLoading ? 'Sending...' : 'Send Message'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="alert alert-info">Complete WhatsApp onboarding to enable messaging.</div>
            )}
          </div>

          {dashboardData.user.onboarding_status === 'Verified' ? (
            <>
              <div className="card p-4 fade-in mb-4">
                <h4 className="mb-3">
                  📝 Manage Message Templates
                </h4>
                <p>Create and manage your WhatsApp message templates for approval and use.</p>
                <Link to="/templates" className="btn btn-outline-primary btn-lg mb-2">
                  ✏️ Manage Templates
                </Link>
              </div>

              <div className="card p-4 fade-in mb-4">
                <h4 className="mb-3">
                  📊 Message History
                </h4>
                {dashboardData.message_history.length > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-striped align-middle">
                      <thead>
                        <tr>
                          <th scope="col">Sent At</th>
                          <th scope="col">Recipient</th>
                          <th scope="col">Template ID</th>
                          <th scope="col">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dashboardData.message_history.map(msg => (
                          <tr key={msg.id}>
                            <td>{new Date(msg.created_at).toLocaleString()}</td>
                            <td>{msg.recipient}</td>
                            <td>{msg.template_id}</td>
                            <td>
                              {msg.status === 'delivered' ? (
                                <span className="badge bg-success">Delivered</span>
                              ) : msg.status === 'read' ? (
                                <span className="badge bg-info">Read</span>
                              ) : msg.status === 'failed' ? (
                                <span className="badge bg-danger">Failed</span>
                              ) : (
                                <span className="badge bg-secondary">{msg.status}</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-muted">No messages sent yet.</div>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="card p-4 fade-in mb-4">
                <h4 className="mb-3">
                  📝 Manage Message Templates
                </h4>
                <div className="alert alert-warning mb-0">You must complete WhatsApp onboarding before managing templates.</div>
              </div>

              <div className="card p-4 fade-in mb-4">
                <h4 className="mb-3">
                  📊 Message History
                </h4>
                <div className="alert alert-warning mb-0">You must complete WhatsApp onboarding before viewing message history.</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 