import './Challenge.css';
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Challenge = ({ setCurrentWorkflow, selectedChallenge, setSelectedChallenge }) => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [appChallenges, setAppChallenges] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [userLeaderboard, setUserLeaderboard] = useState([]);
  const [workflowLeaderboard, setWorkflowLeaderboard] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleCount, setVisibleCount] = useState(5);
  const [myWorkflow, setMyWorkflow] = useState('');
  const [timeLimit, setTimeLimit] = useState('');
  const [bid, setBid] = useState('');
  const [content, setContent] = useState('');
  const [computePoints, setComputePoints] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState("");
  const [myChallenges, setMyChallenges] = useState([]);
  const [communityChallenges, setCommunityChallenges] = useState([]);
  const [communityForm, setCommunityForm] = useState({
    selectedWorkflow: '',
    entryBid: '',
  });
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;
  const handleCardClick = (card) => {
    setSelectedCard(card);
    setIsModalOpen(true);
  };

  const handleChallengeClick = (challenge) => {
    setSelectedChallenge(challenge);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!selectedWorkflow || !selectedChallenge) {
      return;
    }
    setSelectedChallenge(selectedChallenge);
    setCurrentWorkflow(selectedWorkflow);
    try {
      const check = await handleDeductPoints(selectedChallenge.points);

      if (check === true) {
        navigate('/workflowRun');
      } else {
        alert(check);
      }
    } catch (error) {
      console.error('Error in handleDeductPoints:', error);
    }
    setIsModalOpen(false);
    setSelectedWorkflow("");
  };

  useEffect(() => {
    fetchChallenges();
    fetchWorkflows();
    fetchComputePoints();
    fetchUserLeaderboard();
    fetchWorkflowLeaderboard();
    fetchMyChallenges();
    fetchyCommunityChallenges();
  }, []);

  const fetchChallenges = async () => {
    try {
      const response = await fetch(`${BackendUrl}/app_data/app_challenges`, {
        method: 'GET',
      });
      const data = await response.json();
      console.log("api response app challenges", data, data.challenge_categories);
      setAppChallenges(data.data.challenge_categories);
    } catch (err) {
      setError('Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  const fetchMyChallenges = async () => {
    try {
      const response = await fetch(`${BackendUrl}/my_challenges/${currentUser.uid}?type=mine`, {
        method: 'GET',
      });
      const data = await response.json();
      setMyChallenges(data);
    } catch (err) {
      setError('Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  const fetchyCommunityChallenges = async () => {
    try {
      const response = await fetch(`${BackendUrl}/my_challenges/${currentUser.uid}?type=community`, {
        method: 'GET',
      });
      const data = await response.json();
      setCommunityChallenges(data);
    } catch (err) {
      setError('Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${BackendUrl}/list_my_workflows/${currentUser.uid}?name=${encodeURIComponent(searchTerm)}&timestamp=&visibility=public`, {
        method: 'GET',
      });
      const data = await response.json();
      setWorkflows(data);
    } catch (err) {
      setError('Failed to load workflows');
    }
  };

  const fetchComputePoints = async () => {
    try {
      const response = await fetch(`${BackendUrl}/get_compute_points/${currentUser.uid}`);
      const data = await response.json();
      setComputePoints(data.compute_points);
    } catch (err) {
      setError('Failed to load compute points');
    }
  };

  const fetchUserLeaderboard = async () => {
    try {
      const response = await fetch('/api/leaderboard/users');
      const data = await response.json();
      setUserLeaderboard(data);
    } catch (err) {
      console.log('Failed to load workflow leaderboard');
    }
  };

  const fetchWorkflowLeaderboard = async () => {
    try {
      const response = await fetch('/api/leaderboard/workflows');
      const data = await response.json();
      setWorkflowLeaderboard(data);
    } catch (err) {
      console.log('Failed to load workflow leaderboard');
    }
  };


  const loadMore = () => {
    setVisibleCount(visibleCount + 5);
  };

  const showLess = () => {
    setVisibleCount(5);
  };

  const handlePostChallenge = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BackendUrl}/post_my_challenge/${currentUser.uid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ workflow: JSON.parse(myWorkflow), timelimit: timeLimit, content: content, bid: bid }),
      });
      const data = await response.json();
      setMyWorkflow('');
      setTimeLimit('');
      setContent('');
      setBid('');
      fetchMyChallenges();
    } catch (err) {
      setError('Failed to post challenge');
    }
  };

  const handleDeductPoints = async (entryBid) => {
    try {
      const response = await fetch(`${BackendUrl}/challenge_deduct_points/${currentUser.uid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ compute_points: entryBid }),
      });
      const data = await response.json();
      console.log("DEDUCT",data);
      if (data.response === 'success') {
        return true;
      }else{
        return data.response;
      }
    } catch (err) {
      setError('Failed to deduct points');
    }
  }
  const handleCommunityInput = (e) => {
    const { name, value } = e.target;
    setCommunityForm((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  const handleCommunityChallengeClick = async (challenge) => {
    const { selectedWorkflow, entryBid } = communityForm;
    if (!selectedWorkflow || !entryBid) {
      return;
    }

    const inputChallenge = {
      id: challenge._id,
      content: challenge.metadata.content,
      points: entryBid
    };

    setSelectedChallenge(inputChallenge);
    setCurrentWorkflow(selectedWorkflow);

    try {
      const check = await handleDeductPoints(entryBid);
  
      if (check === true) {
        navigate('/workflowRun');
      } else {
        alert(check);
      }
    } catch (error) {
      console.error('Error in handleDeductPoints:', error);
    }
  };

  return (
    <div className="main-content">
      <div className="main-content-c">
        <div className="main-left">
          <div className="dashboard-overview box">
          <h2>Challenges from CrewTailor</h2>
            <div className="summary-cards">
              {loading ? (
                <div>Loading...</div>
              ) : appChallenges.length > 0 ? (
                appChallenges.map((log) => (
                  <div
                    key={log.key}
                    className="card"
                    onClick={() => handleCardClick(log)}
                    dangerouslySetInnerHTML={{ __html: log.name }}
                  ></div>
                ))
              ) : (
                <div className="card">Stay tuned for app challenges.</div>
              )}
            </div>
            
          </div>
          <div className="box">
            <h2>Challenges from community</h2>
            <div className="community-challenges-box">
      <ul>
        {communityChallenges.length > 0 ? (
          communityChallenges.map((challenge) => (
            <li key={challenge._id} className="community-challenge-item">
              <span className="challenge-workflow-name">{challenge.metadata.workflow.name}</span>
              <span className="challenge-content">{challenge.metadata.content}</span>
              <div className="challenge-actions">
                <select
                  name="selectedWorkflow"
                  value={communityForm.selectedWorkflow}
                  onChange={handleCommunityInput}
                  className="workflow-select"
                >
                  <option value="">Select Public Workflow</option>
                  {workflows.map((workflow) => (
                    <option key={workflow._id} value={workflow._id}>
                      {workflow.metadata.name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  name="entryBid"
                  value={communityForm.entryBid}
                  onChange={handleCommunityInput}
                  placeholder="Enter your stake in points"
                  className="workflow-select"
                />
                <button
                  type="submit"
                  className="enter-button"
                  onClick={() => handleCommunityChallengeClick(challenge)}
                >
                  Enter
                </button>
              </div>
            </li>
          ))
        ) : (
          <p>No community challenges yet!</p>
        )}
      </ul>
    </div>
          </div>


        </div>
        <div className="main-right">
          <div className="compute-points-container">
            <div className="compute-points box">
              <h2>Compute Points</h2>
              <p>{computePoints} points</p>
              {error && <p className="error">{error}</p>}
            </div>
          </div>
          <div className="leaderboard box">
            <h2>User Leaderboard</h2>
            <ul>
              {userLeaderboard.length > 0 ? (
                userLeaderboard.map((user, index) => (
                  <li key={index}>
                    {index + 1}. {user.username} - {user.points} points
                  </li>
                ))
              ) : (
                <p>No users found.</p>
              )}
            </ul>
          </div>
          <div className="leaderboard box">
            <h2>Workflow Leaderboard</h2>
            <ul>
              {workflowLeaderboard.length > 0 ? (
                workflowLeaderboard.map((workflow, index) => (
                  <li key={index}>
                    {index + 1}. {workflow.metadata.name} - {workflow.points} points
                  </li>
                ))
              ) : (
                <p>No workflows found.</p>
              )}
            </ul>
          </div>
          <div className='box'>
              <h2>Challenge my workflow</h2>
              <p>Post a challenge and gain compute points.</p>
              <form className="challenge-form" onSubmit={handlePostChallenge}>
                <select name="myWorkflow" value={myWorkflow} onChange={(e) => setMyWorkflow(e.target.value)}>
                  <option value="">Select Workflow</option>
                  {workflows.map((workflow) => (
                    <option key={workflow._id} value={JSON.stringify({"id": workflow._id, "name": workflow.metadata.name})}>{workflow.metadata.name}</option>
                  ))}
                </select>
                <select name="time-limit" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)}>
                  <option value="">Select Time Limit</option>
                  <option value="1h">1 hour</option>
                  <option value="24h">24 hours</option>
                  <option value="7d">7 days</option>
                </select>
                <input type='text' name='content' value={content} onChange={(e) => setContent(e.target.value)} placeholder='Enter challenge content'/>
                <input
                  type="number"
                  name="bid"
                  value={bid}
                  onChange={(e) => setBid(e.target.value)}
                  placeholder="Enter your stake in points"
                />
                
                <button type="submit">Post</button>
              </form>
            </div>
          <div className="box">
            <h2>My Challenges</h2>
            <ul>
              {myChallenges.length > 0 ? (
                myChallenges.map((challenge) => (
                  <li key={challenge._id}>
                    {challenge.metadata.workflow.name} - Bid: {challenge.metadata.bid} points
                  </li>
                ))
              ) : (
                <p>Create a challenge and get compute points!</p>
              )}
            </ul>
          </div>
        </div>
      </div>
      {isModalOpen && (
        <div className="modal-c">
          <div className="modal-c-content">
            <button className="modal-close" onClick={() => {setIsModalOpen(false); setSelectedChallenge(null)}}>
              &times;
            </button>
            {selectedChallenge ? (
              <div>
                <h2>Enter Challenge</h2>
                <p>{selectedChallenge.content}</p>
                <form onSubmit={handleFormSubmit}>
                  <select
                    name="workflow"
                    value={selectedWorkflow}
                    onChange={(e) => setSelectedWorkflow(e.target.value)}
                    className='challenge-select'
                  >
                    <option value="">Select Public Workflow</option>
                    {workflows.map((workflow) => (
                      <option key={workflow._id} value={workflow._id}>
                        {workflow.metadata.name}
                      </option>
                    ))}
                  </select>
                  <button type="submit">Enter</button>
                </form>
              </div>
            ) : (
              <div>
                <h2>{selectedCard.name}</h2>
                <ul>
                  {selectedCard.challenges.map((challenge) => (
                    <li key={challenge.id} onClick={() => handleChallengeClick(challenge)}>
                      {challenge.content} - Cost: {challenge.points} points - Reward upto {challenge.points * 2} points
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default Challenge;