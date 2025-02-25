import './MainContent2.css';
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import parseLogMessage from './parseLogMessage';
const MainContent = ({ setCurrentWorkflow }) => {
  const [myWorkflows, setMyWorkflows] = useState([]);
  const [communityWorkflows, setCommunityWorkflows] = useState([]);
  const [storeWorkflows, setStoreWorkflows] = useState([]);
  const [searchTermMine, setSearchTermMine] = useState('');
  const [searchTermCommunity, setSearchTermCommunity] = useState('');
  const [visibleCountMine, setVisibleCountMine] = useState(5);
  const [visibleCountCommunity, setVisibleCountCommunity] = useState(5);
  const [totalWorkflows, setTotalWorkflows] = useState(0);
  const [communityChallenges, setCommunityChallenges] = useState([]);
  const [computePoints, setComputePoints] = useState('');
  const [logs, setLogs] = useState([]);
  const { currentUser } = useAuth();
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;
  const navigate = useNavigate();
  
  
  useEffect(() => {
    if (currentUser) {
      console.log("id:", currentUser.uid); 
      const uid = currentUser.uid;
    }
    const fetchComputePoints = async () => {
      try {
        const response = await fetch(`${BackendUrl}/get_compute_points/${currentUser.uid}`);
        const data = await response.json();
        setComputePoints(data.compute_points);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };
    fetchComputePoints();
  }, [currentUser]);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        console.log('Fetching workflows...: ', currentUser.uid, searchTermMine, searchTermCommunity);
        const response_mine = await fetch(`${BackendUrl}/list_my_workflows/${currentUser.uid}?name=${encodeURIComponent(searchTermMine)}&timestamp=&visibility=`, {
          method: 'GET',
        });
        const response_community = await fetch(`${BackendUrl}/list_community_workflows/${currentUser.uid}?name=${encodeURIComponent(searchTermCommunity)}&timestamp=`, {
          method: 'GET',
        });
      
        if (!response_mine.ok || !response_community.ok) {
          throw new Error(`HTTP error! status: ${response_mine.status} | ${response_community.status}`);
        }
      
        const data_mine = await response_mine.json();
        const data_community = await response_community.json();
        console.log('API Response:', data_mine, data_community);
        setMyWorkflows(data_mine);
        setCommunityWorkflows(data_community);
        setTotalWorkflows(data_mine.length + data_community.length);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };

    fetchWorkflows();
  }, [searchTermMine, searchTermCommunity, currentUser.uid]);

  useEffect(() => {
    const fetchStoreWorkflows = async () => {
      try {
        const response = await fetch(`${BackendUrl}/store/list_public_workflows?uid=${currentUser.uid}&tags=trending`, {
          method: 'GET',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response store workflows:', data);
        setStoreWorkflows(data);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };

    fetchStoreWorkflows();
  }, [currentUser.uid]);
  
  useEffect(() => {
    const fetchyCommunityChallenges = async () => {
      try {
        const response = await fetch(`${BackendUrl}/my_challenges/${currentUser.uid}?type=community`, {
          method: 'GET',
        });
        const data = await response.json();
        setCommunityChallenges(data);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };

    fetchyCommunityChallenges();
  }, [currentUser.uid]);
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${BackendUrl}/get_recent_logs/${currentUser.uid}`, {
          method: 'GET',
        });
      
        if (!response) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      
        const data = await response.json();

        console.log('API Response:', data);
        setLogs(data);
      } catch (err) {
        console.log('Error while accessing API: ' + err);
      }
    };

    fetchLogs();
  }, []);
  const loadMore = (type) => {
    if (type == "mine"){  
      setVisibleCountMine((prevCount) => prevCount + 5);
    } else {
      setVisibleCountCommunity((prevCount) => prevCount + 5);
    }
    
  };

  const showLess = (type) => {
    if (type == "mine"){  
      setVisibleCountMine((prevCount) => Math.max(prevCount - 5, 5));
    } else {
      setVisibleCountCommunity((prevCount) => Math.max(prevCount - 5, 5));
    }
    
  };

  const handleWorkflowClick = (workflow_id) => {
    setCurrentWorkflow(workflow_id);
    navigate('/workflowView');
  };

  const handleNewWorkflowClick = () => {
    navigate('/newWorkflows');
  }

  const handleStoreClick = () => {
    navigate('/store');
  }

  return (
    <div className="main-content-main1">
      <div className="main-left">
        <div className="dashboard-overview box">
          <h2>Dashboard Overview</h2>
          <div className="summary-cards">
            <div className="card">Total Workflows: {totalWorkflows}</div>
            <div className="card">Recent Executions: _</div>
          </div>
          <div className="recent-activity">
            <h3>Recent Activity</h3>
            <ul>
            {logs.length > 0 ? (
              <>
                {logs.map((log) => (
                  <li key={log.timestamp} className="log-item">
                    <span className="log-message" dangerouslySetInnerHTML={{ __html: parseLogMessage(log) }}></span>
                  </li>
                ))}
              </>
            ) : (
              <li className='log-item'>No recent activity. You need to lighten up!!!</li>
            )}
          </ul>
          </div>
        </div>

        <div className="my-workflows box">
          <h2>My Workflows</h2>
          <div className="workflows-section">
            <h3>Created</h3>
            <div className="workflow-list">
              <input
                type="text"
                placeholder="Search Created Workflows..."
                value={searchTermMine}
                className='search-bar'
                onChange={(e) => setSearchTermMine(e.target.value)}
              />
              <ul>
                {myWorkflows.length > 0 ? (
                <>
                  {myWorkflows.slice(0, visibleCountMine).map((workflow) => (
                    <li key={workflow._id} onClick={() => handleWorkflowClick(workflow._id)} className='workflow-list'>
                    <div className='workflow-name2'>{workflow.metadata.name}</div>
                    <div className='workflow-timestamp'>{workflow.timestamp}</div>
                  </li>
                  
                  ))}
                  {visibleCountMine < myWorkflows.length && (
                    <button onClick={() => loadMore('mine')} className='visibleToggleButton'>Load More</button>
                  )}
                  {visibleCountMine > 5 && (
                    <button onClick={() => showLess('mine')} className='visibleToggleButton'>Show Less</button>
                  )}
                </>
              ) : searchTermMine ? (
                <li>No workflows match your search criteria.</li>
              ) : (
                <li onClick={handleNewWorkflowClick}>No personal workflows found. CLICK HERE to get started!</li>
              )}
              </ul>
            </div>
          </div>
          <div className="workflows-section">
            <h3>From Community</h3>
            <div className="workflow-list">
              <input
                type="text"
                placeholder="Search Community Workflows..."
                value={searchTermCommunity}
                className='search-bar'
                onChange={(e) => setSearchTermCommunity(e.target.value)}
              />
              <ul>
              {communityWorkflows.length > 0 ? (
                  <>
                    {communityWorkflows.slice(0, visibleCountCommunity).map((workflow) => (
                      <li key={workflow._id} onClick={() => handleWorkflowClick(workflow._id)} className='workflow-list'>
                      <div className='workflow-name2'>{workflow.metadata.name}</div>
                      <div className='workflow-timestamp'>{workflow.timestamp}</div>
                    </li>
                    
                    ))}
                    <div className='buttonsHolder'>
                    {visibleCountCommunity < communityWorkflows.length && (
                      <button onClick={() => loadMore('community')} className='visibleToggleButton'>Load More</button>
                    )}
                    {visibleCountCommunity > 5 && (
                      <button onClick={() => showLess('community')} className='visibleToggleButton'>Show Less</button>
                    )}
                    </div>
                  </>
                  ) : searchTermCommunity ? (
                    <li>No workflows match your search criteria.</li>
                  ) : (
                  <li onClick={handleStoreClick}>No community workflows found. CLICK HERE to explore!</li>
                  )}
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="main-right">
      <div className="compute-points-container">
            <div className="compute-points box">
              <h2>Compute Points</h2>
              <p>{computePoints} points</p>
            </div>
          </div>
        <div className="box">
          <h2>Workflows you may like</h2>
          <div className="workflow-section">
            <h3>Trending</h3>
            <ul>
                {storeWorkflows.slice(0, 5).map((workflow) => (
                  <li key={workflow._id} className='workflow-list' onClick={handleStoreClick}>
                    <div className="workflow-info">
                      <p>{workflow.name}</p>
                      <span>Likes: {workflow.likes.length}</span>
                      <span>  Downloads: {workflow.downloads.length}</span>
                    </div>
                  </li>
                ))}
              </ul>
          </div>
        </div>

        <div className="comm-challenges-container box">
  <h2>Challenge your workflow</h2>
  <div className="comm-challenges-box">
    <ul>
      <li class="comm-challenges-item" onClick={() => navigate("/challenge")}>
      <span class="challenge-content">Task Automation</span>
    </li>
    <li class="comm-challenges-item" onClick={() => navigate("/challenge")}>
      <span class="challenge-content">Content Creation</span>
    </li>
    <li class="comm-challenges-item" onClick={() => navigate("/challenge")}>
      <span class="challenge-content">Event Planning</span>
    </li>
      {communityChallenges.length > 0 ? (
        communityChallenges.slice(0, 5).map((challenge) => (
          <li key={challenge._id} className="comm-challenges-item" onClick={() => navigate("/challenge")}>
            <span className="challenge-content">{challenge.metadata.content}</span>
          </li>
        ))
      ) : (
        <p>No community challenges yet!</p>
      )}
    </ul>
  </div>
</div>


        <div className="help-documentation box">
        <h2>Help and Documentation</h2>
        
        <div className="guides-tutorials">
          <h3>Guides and Tutorials</h3>
          <a href="https://github.com/adonaydem/CrewTailor" target="_blank" rel="noopener noreferrer">
          Access the user guide and tutorials here:
          </a>
        </div>
        <div className="support">
          <h3>Support</h3>
          <p>If you need help or want to provide feedback, contact us at:</p>
          <a href="mailto:crewtailor.ai@gmail.com">
            crewtailor.ai@gmail.com
          </a>
        </div>
      </div>
      </div>
    </div>
  );
};

export default MainContent;