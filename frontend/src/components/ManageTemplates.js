import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const ManageTemplates = ({ user }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    language: 'en_US',
    category: 'TRANSACTIONAL',
    header_type: 'NONE',
    header_text: '',
    header_image_url: '',
    footer_text: '',
    content: '',
    button1_type: '',
    button1_text: '',
    button1_url: '',
    button2_type: '',
    button2_text: '',
    button2_url: '',
    button3_type: '',
    button3_text: '',
    button3_url: ''
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get('/templates');
      setTemplates(response.data.templates);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitLoading(true);

    try {
      await axios.post('/templates', formData);
      addAlert('Template created successfully!', 'success');
      setFormData({
        name: '',
        language: 'en_US',
        category: 'TRANSACTIONAL',
        header_type: 'NONE',
        header_text: '',
        header_image_url: '',
        footer_text: '',
        content: '',
        button1_type: '',
        button1_text: '',
        button1_url: '',
        button2_type: '',
        button2_text: '',
        button2_url: '',
        button3_type: '',
        button3_text: '',
        button3_url: ''
      });
      fetchTemplates();
    } catch (error) {
      addAlert(error.response?.data?.error || 'Failed to create template', 'danger');
    } finally {
      setSubmitLoading(false);
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

  return (
    <div className="row justify-content-center g-4">
      <div className="col-lg-7">
        {alerts.map(alert => (
          <div key={alert.id} className={`alert alert-${alert.type} alert-dismissible fade show`} role="alert">
            {alert.message}
            <button type="button" className="btn-close" onClick={() => setAlerts(prev => prev.filter(a => a.id !== alert.id))}></button>
          </div>
        ))}

        <div className="card p-4 fade-in mb-4">
          <h3 className="mb-3">📝 Create New Template</h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="name" className="form-label">Template Name</label>
              <input
                type="text"
                className="form-control"
                id="name"
                name="name"
                placeholder="Template Name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="language" className="form-label">Language Code</label>
              <input
                type="text"
                className="form-control"
                id="language"
                name="language"
                placeholder="en_US"
                value={formData.language}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="category" className="form-label">Category</label>
              <select
                className="form-select"
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                required
              >
                <option value="TRANSACTIONAL">Transactional</option>
                <option value="MARKETING">Marketing</option>
                <option value="OTP">OTP</option>
                <option value="UTILITY">Utility</option>
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="content" className="form-label">Message Content</label>
              <textarea
                className="form-control"
                id="content"
                name="content"
                rows="3"
                placeholder="Message Content"
                value={formData.content}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="header_type" className="form-label">Header Type</label>
              <select
                className="form-select"
                id="header_type"
                name="header_type"
                value={formData.header_type}
                onChange={handleChange}
              >
                <option value="NONE">None</option>
                <option value="TEXT">Text</option>
                <option value="IMAGE">Image</option>
              </select>
            </div>
            {formData.header_type === 'TEXT' && (
              <div className="mb-3">
                <label htmlFor="header_text" className="form-label">Header Text</label>
                <input
                  type="text"
                  className="form-control"
                  id="header_text"
                  name="header_text"
                  placeholder="Header Text"
                  value={formData.header_text}
                  onChange={handleChange}
                />
              </div>
            )}
            {formData.header_type === 'IMAGE' && (
              <div className="mb-3">
                <label htmlFor="header_image_url" className="form-label">Header Image URL</label>
                <input
                  type="url"
                  className="form-control"
                  id="header_image_url"
                  name="header_image_url"
                  placeholder="Header Image URL"
                  value={formData.header_image_url}
                  onChange={handleChange}
                />
              </div>
            )}
            <div className="mb-3">
              <label htmlFor="footer_text" className="form-label">Footer Text</label>
              <input
                type="text"
                className="form-control"
                id="footer_text"
                name="footer_text"
                placeholder="Footer Text (optional)"
                value={formData.footer_text}
                onChange={handleChange}
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Buttons (up to 3, optional)</label>
              {[1, 2, 3].map(num => (
                <div key={num} className="row g-2 mb-2">
                  <div className="col-md-4">
                    <label htmlFor={`button${num}_type`} className="form-label">Button {num} Type</label>
                    <select
                      className="form-select"
                      id={`button${num}_type`}
                      name={`button${num}_type`}
                      value={formData[`button${num}_type`]}
                      onChange={handleChange}
                    >
                      <option value="">None</option>
                      <option value="QUICK_REPLY">Quick Reply</option>
                      <option value="CALL_TO_ACTION">Call To Action</option>
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label htmlFor={`button${num}_text`} className="form-label">Button {num} Text</label>
                    <input
                      type="text"
                      className="form-control"
                      id={`button${num}_text`}
                      name={`button${num}_text`}
                      placeholder={`Button ${num} Text`}
                      value={formData[`button${num}_text`]}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="col-md-4">
                    <label htmlFor={`button${num}_url`} className="form-label">Button {num} URL</label>
                    <input
                      type="url"
                      className="form-control"
                      id={`button${num}_url`}
                      name={`button${num}_url`}
                      placeholder={`Button ${num} URL (for CTA)`}
                      value={formData[`button${num}_url`]}
                      onChange={handleChange}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="d-grid">
              <button type="submit" className="btn btn-main btn-lg" disabled={submitLoading}>
                {submitLoading ? 'Creating...' : 'Create Template'}
              </button>
            </div>
          </form>
        </div>

        <div className="card p-4 fade-in mb-4">
          <h3 className="mb-3">📋 Your Templates</h3>
          {templates.length > 0 ? (
            <ul className="list-group">
              {templates.map(template => (
                <li key={template.id} className="list-group-item">
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <span className="fw-bold">{template.name}</span>
                      <span className="badge bg-secondary ms-2">{template.language}</span>
                      <span className="badge bg-info ms-1">{template.status}</span>
                      <span className="badge bg-warning ms-1">{template.category}</span>
                    </div>
                    <span className="text-muted small">{new Date(template.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="mt-2">{template.content}</div>
                  {template.header_type !== 'NONE' && (
                    <div className="mt-1">
                      <b>Header:</b> {template.header_type}
                      {template.header_text && ` - ${template.header_text}`}
                      {template.header_image_url && (
                        <span> - <a href={template.header_image_url} target="_blank" rel="noopener noreferrer">Image</a></span>
                      )}
                    </div>
                  )}
                  {template.footer_text && (
                    <div className="mt-1"><b>Footer:</b> {template.footer_text}</div>
                  )}
                  {template.buttons_json && (
                    <div className="mt-1"><b>Buttons:</b> <code>{template.buttons_json}</code></div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-muted">No templates created yet.</div>
          )}
        </div>

        <div className="text-end mt-3">
          <Link to="/dashboard" className="btn btn-outline-primary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ManageTemplates;