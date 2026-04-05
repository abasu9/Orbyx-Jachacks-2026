import { useState } from 'react';
import Chatbot from './Chatbot';
import './Dashboard.css';

const Dashboard = ({ onLogout }) => {
  const [employees] = useState([
    {
      id: 1,
      name: 'Abhishek Basu',
      commits: 357,
      prs: 35,
      reviews: 60,
      activeDays: 205,
      score: 0.93,
      rank: 1
    },
    {
      id: 2,
      name: 'Anand Singh',
      commits: 281,
      prs: 0,
      reviews: 0,
      activeDays: 160,
      score: 0.53,
      rank: 2
    },
    {
      id: 3,
      name: 'Bhavani Shankar',
      commits: 299,
      prs: 0,
      reviews: 0,
      activeDays: 159,
      score: 0.53,
      rank: 3
    },
    {
      id: 4,
      name: 'Soureesh Dalal',
      commits: 293,
      prs: 0,
      reviews: 0,
      activeDays: 165,
      score: 0.53,
      rank: 4
    },
    {
      id: 5,
      name: 'Vinayak Baghel',
      commits: 273,
      prs: 0,
      reviews: 0,
      activeDays: 171,
      score: 0.53,
      rank: 5
    }
  ]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>Employee Performance Dashboard</h1>
            <p>Software Development Metrics</p>
          </div>
          <button onClick={onLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="stats-overview">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>Total Employees</h3>
              <p className="stat-value">{employees.length}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">💻</div>
            <div className="stat-content">
              <h3>Total Commits</h3>
              <p className="stat-value">{employees.reduce((sum, e) => sum + e.commits, 0)}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">🔀</div>
            <div className="stat-content">
              <h3>Total PRs</h3>
              <p className="stat-value">{employees.reduce((sum, e) => sum + e.prs, 0)}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">👁️</div>
            <div className="stat-content">
              <h3>Total Reviews</h3>
              <p className="stat-value">{employees.reduce((sum, e) => sum + e.reviews, 0)}</p>
            </div>
          </div>
        </div>

        <div className="employees-section">
          <h2>Employee Performance Rankings</h2>
          <div className="employees-grid">
            {employees.map((employee) => (
              <div key={employee.id} className="employee-card">
                <div className="card-header">
                  <div className="rank-badge">#{employee.rank}</div>
                  <h3>{employee.name}</h3>
                </div>
                
                <div className="card-body">
                  <div className="metric-row">
                    <span className="metric-label">Performance Score</span>
                    <span className="metric-value score">{employee.score.toFixed(2)}</span>
                  </div>
                  
                  <div className="metrics-grid">
                    <div className="metric-item">
                      <span className="metric-icon">💻</span>
                      <div>
                        <p className="metric-number">{employee.commits}</p>
                        <p className="metric-text">Commits</p>
                      </div>
                    </div>
                    
                    <div className="metric-item">
                      <span className="metric-icon">🔀</span>
                      <div>
                        <p className="metric-number">{employee.prs}</p>
                        <p className="metric-text">Pull Requests</p>
                      </div>
                    </div>
                    
                    <div className="metric-item">
                      <span className="metric-icon">👁️</span>
                      <div>
                        <p className="metric-number">{employee.reviews}</p>
                        <p className="metric-text">Reviews</p>
                      </div>
                    </div>
                    
                    <div className="metric-item">
                      <span className="metric-icon">📅</span>
                      <div>
                        <p className="metric-number">{employee.activeDays}</p>
                        <p className="metric-text">Active Days</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Chatbot Component */}
      <Chatbot />
    </div>
  );
};

export default Dashboard;
