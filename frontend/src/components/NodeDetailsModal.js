import React from 'react';
import './NodeDetailsModal.css';

const NodeDetailsModal = ({ node, onClose, onSave }) => {
  const [details, setDetails] = React.useState(node.data.workerDetails || {});

  const handleChange = (e) => {
    const { name, value, checked, type, options } = e.target;
    if (name === 'toolkits') {
      // Handle multiple select
      const selectedValues = Array.from(options).filter(option => option.selected).map(option => option.value);
      setDetails((prevDetails) => ({
        ...prevDetails,
        [name]: selectedValues,
      }));
    } else {
      setDetails((prevDetails) => ({
        ...prevDetails,
        [name]: value,
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(node.id, details);
    onClose();
  };

  return (
    <div className="modal overlay">
      <div className="modal-content">
        <h3>Edit Worker Details</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              name="name"
              value={details.name || ''}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>Toolkits:</label>
            <select
              name="toolkits"
              value={details.toolkits || []}
              onChange={handleChange}
              multiple
            >
              <option value="" disabled>General Text and General Tools Only</option>
              <option value="database_management">Database Management</option>
              <option value="file_management">File Management</option>
              <option value="task_management">Task Management</option>
              <option value="event_management">Event Management</option>
              <option value="project_management">Project Management</option>
              <option value="finance&economics_apipack">Finance and Economics API Pack</option>
            </select>
          </div>
          <div className="form-group">
            <label>Human Direction:</label>
            <select name="humanDirection" value={details.humanDirection || 'no'} onChange={handleChange}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
          <div className="form-group">
            <label>Description:</label>
            <textarea
              name="description"
              value={details.description || ''}
              onChange={handleChange}
            ></textarea>
          </div>
          <div className="form-group">
            <label>To-Do List:</label>
            <textarea
              name="workerTodoList"
              value={details.workerTodoList || ''}
              onChange={handleChange}
            ></textarea>
          </div>
          <div className="form-group">
            <label>People Involved:</label>
            <textarea
              name="peopleInvolved"
              value={details.peopleInvolved || ''}
              onChange={handleChange}
            ></textarea>
          </div>
          <button type="submit">Save</button>
          <button type="button" onClick={onClose}>
            Cancel
          </button>
        </form>
      </div>
    </div>
  );
};

export default NodeDetailsModal;