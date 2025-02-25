import React, { useState, useEffect } from 'react';
import './Store.css';
import { useAuth } from '../contexts/AuthContext';
import useSocketStore from '../hooks/useSocketStore';
import { useNavigate } from 'react-router-dom';

const Store = ({ setCurrentWorkflow }) => {
  const { workflows, handleLike, handleSubmitFeedback, setWorkflows, isFeedbackPopupOpen, setIsFeedbackPopupOpen, currentFeedbackWorkflow, setCurrentFeedbackWorkflow, feedbackContent, setFeedbackContent, feedbackList, setFeedbackList } = useSocketStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleCount, setVisibleCount] = useState(5);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [popularTags, setPopularTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [topContributors, setTopContributors] = useState([]);
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await fetch(`${BackendUrl}/store/list_public_workflows?uid=${currentUser.uid}&name=${encodeURIComponent(searchTerm)}&category=${encodeURIComponent(selectedCategory)}&tags=${encodeURIComponent(selectedTags.join(','))}`, {
          method: 'GET',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response public workflows:', data);
        setWorkflows(data);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };

    fetchWorkflows();
  }, [searchTerm, selectedCategory, selectedTags, setWorkflows, currentUser.uid]);

  useEffect(() => {
    const fetchStoreMetadata = async () => {
      try {
        const response = await fetch(`${BackendUrl}/app_data/store_metadata`, );

        if (!response.ok) {
          throw new Error('Error fetching store metadata');
        }

        const data = await response.json();
        console.log('API Response store metadata:', data);
        setCategories(data.data.categories || []);
        setPopularTags(data.data.popular_tags || []);
        setTopContributors(data.data.top_contributors || []);
      } catch (err) {
        console.log('Error while accessing fetchStoreMetadata API: ' + err);
      }
    };

    fetchStoreMetadata();
  }, []);

  const handleDownload = async (workflowId, uid) => {
    try {
      const response = await fetch(`${BackendUrl}/store/add_public_workflow`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: workflowId,
          uid: uid,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Save Response:', data.new_workflow_id);
      alert('Workflow added successfully!');

      setCurrentWorkflow(data.new_workflow_id);
      navigate('/workflowView');
    } catch (err) {
      console.log("Error while accessing download API: " + err);
    }
  };

  const loadMore = () => {
    setVisibleCount((prevCount) => prevCount + 5);
  };

  const showLess = () => {
    setVisibleCount((prevCount) => Math.max(prevCount - 5, 5));
  };

  const handleFeedbackOpen = (workflowId) => {
    setCurrentFeedbackWorkflow(workflowId);
    setIsFeedbackPopupOpen(true);
    fetchFeedbacks(workflowId);
    console.log("feedbackList", feedbackList, "from", workflowId);
  };

  async function fetchFeedbacks(workflowId) {
    try {
      console.log('Fetching feedbacks...', currentFeedbackWorkflow);
      const response = await fetch(`${BackendUrl}/store/get_feedbacks?workflowId=${workflowId}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      if (data == null) {
        setFeedbackList(null);
      } else {
        setFeedbackList(data.feedbacks);
      }
    } catch (error) {
      console.error('Error while fetching feedbacks:', error);
    }
  }

  const renderFeedbackPopup = () => {
    if (!isFeedbackPopupOpen) return null;

    return (
      <div className="feedback-popup">
        <div className="feedback-popup-content">
          <h2>Feedbacks</h2>
          <ul>
          {feedbackList ? (
            feedbackList.map((feedback) => (
              <li key={feedback.timestamp}>
                {feedback.content} - {feedback.user} - {feedback.timestamp}
              </li>
            ))
          ) : (
            <li>Be the first to give feedback!!!</li>
          )}
          </ul>
          <textarea
            value={feedbackContent}
            onChange={(e) => setFeedbackContent(e.target.value)}
            placeholder="Enter your feedback..."
          />
          <button onClick={() => { handleSubmitFeedback(currentFeedbackWorkflow, currentUser.uid, feedbackContent); fetchFeedbacks(currentFeedbackWorkflow) }}>Submit Feedback</button>
          <button onClick={() => setIsFeedbackPopupOpen(false)}>Close</button>
        </div>
      </div>
    );
  };

  const handleTagClick = (tag) => {
    setSelectedTags((prevTags) =>
      prevTags.includes(tag) ? prevTags.filter((t) => t !== tag) : [...prevTags, tag]
    );
    console.log("selectedTags", selectedTags);
  };

  return (
    <div className='main-content'>
      <div className="main-content-main">
        <div className="store-left box">
          <div className="workflows-section">
            <h2>Workflows Store</h2>
            <input
              type="text"
              placeholder="Search Workflows..."
              className='search-bar'
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="workflow-list">
              <h3>Featured Workflows</h3>
              <ul>
                {workflows.slice(0, visibleCount).map((workflow) => (
                  <li key={workflow._id} className='workflow-item'>
                    <div className="workflow-info">
                      <h4>{workflow.name}</h4>
                      <p>{workflow.description}</p>
                      <p>Categories: {workflow.categories}</p>
                      <p>Likes: {workflow.likes.length}</p>
                      <p>Downloads: {workflow.downloads.length}</p>
                    </div>
                    <div className="workflow-actions">
                      {workflow.likes.includes(currentUser.uid) ? (
                        <button disabled>Already Liked</button>
                      ) : (
                        <button onClick={() => handleLike(workflow.workflow_id, currentUser.uid)}>Like</button>
                      )}
                      <button onClick={() => handleFeedbackOpen(workflow.workflow_id)}>Feedback</button>
                      {workflow.downloads.includes(currentUser.uid) ? (
                        <button onClick={() => handleDownload(workflow.workflow_id, currentUser.uid)}>Download Again</button>
                      ) : (
                        <button onClick={() => handleDownload(workflow.workflow_id, currentUser.uid)}>Download</button>
                      )}

                    </div>
                  </li>
                ))}
              </ul>
              {visibleCount < workflows.length && (
                <button onClick={loadMore}>Load More</button>
              )}
              {visibleCount > 5 && (
                <button onClick={showLess}>Show Less</button>
              )}
            </div>
          </div>
        </div>

        <div className="store-right box">
          <div className="filters-section">
            <h2>Filters</h2>
            <div className="category-filter">
              <h3>Categories</h3>
              <select onChange={(e) => setSelectedCategory(e.target.value)} value={selectedCategory}>
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
            <div className="tag-filter">
              <h3>Popular Tags</h3>
              <ul>
                {popularTags.map((tag) => (
                  <li key={tag} onClick={() => handleTagClick(tag)} className={selectedTags.includes(tag) ? 'selected' : ''}>
                    {tag}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="contributors-section">
            <h2>Top Contributors</h2>
            <ul>
              {topContributors.map((contributor) => (
                <li key={contributor}>{contributor}</li>
              ))}
            </ul>
          </div>

          <div className="highlight-section">
            <h2>Workflow of the Day</h2>
            {workflows.length > 0 && (
              <div className="highlight-workflow">
                <h3>{workflows[0].name}</h3>
                <p>{workflows[0].description}</p>
                <p>Categories: {workflows[0].categories}</p>
                <p>Downloads: {workflows[0].downloads.length}</p>
                <p>Likes: {workflows[0].likes.length}</p>
              </div>
            )}
          </div>
        </div>
      </div>
      {renderFeedbackPopup()}
    </div>
  );
};

export default Store;