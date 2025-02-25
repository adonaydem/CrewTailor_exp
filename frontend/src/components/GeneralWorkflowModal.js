import React from 'react';
import './GeneralWorkflowModal.css';

const GeneralWorkflowModal = ({ workflowData = {}, handleInputChange, handleFormSubmit, style }) => {
  return (
    <div className="general-workflow-modal" style={style}>
      <h3>General Workflow Details</h3>
      <form onSubmit={handleFormSubmit} className="general-workflow-form">
        <div className="form-group">
          <label>Name:</label>
          <input type="text" name="name" value={workflowData.name || ''} onChange={handleInputChange} required />
        </div>
        <div className="form-group">
          <label>Description:</label>
          <textarea name="description" value={workflowData.description || ''} onChange={handleInputChange} required></textarea>
        </div>
        <div className="form-group">
          <label>General To-Do List:</label>
          <textarea name="todoList" value={workflowData.todoList || ''} onChange={handleInputChange} required></textarea>
        </div>
        <div className="form-group">
          <label>People Involved:</label>
          <input type="text" name="peopleInvolved" value={workflowData.peopleInvolved || ''} onChange={handleInputChange} />
        </div>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="public"
              checked={workflowData.public}
              onChange={(e) => handleInputChange(e)}
            />
            Public
          </label>
        </div>
        <button type="submit">Save Workflow</button>
      </form>
    </div>
  );
};

export default GeneralWorkflowModal;