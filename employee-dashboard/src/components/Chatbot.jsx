import { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: 'Hello! I\'m your Employee Performance Assistant. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickActions = [
    { id: 1, text: 'Show top performers', icon: '🏆' },
    { id: 2, text: 'Explain performance metrics', icon: '📊' },
    { id: 3, text: 'How is ranking calculated?', icon: '🔢' },
    { id: 4, text: 'What is PIP?', icon: '❓' },
  ];

  const getBotResponse = (userMessage) => {
    const message = userMessage.toLowerCase();

    // Performance metrics explanation
    if (message.includes('metric') || message.includes('measure')) {
      return 'We track several key metrics:\n\n💻 Commits - Total code contributions\n🔀 Pull Requests - Code reviews submitted\n👁️ Reviews - PR reviews given\n📅 Active Days - Days with contributions\n📈 Performance Score - Overall rating (0-1)';
    }

    // Ranking explanation
    if (message.includes('ranking') || message.includes('rank') || message.includes('calculate')) {
      return 'Employee ranking is calculated based on:\n\n1. Annual Performance (AP) score (0-2 scale)\n2. PIP count (Performance Improvement Plans)\n3. Activity metrics (commits, PRs, reviews)\n\nThe formula combines these factors to generate a final ranking score between 0 and 1.';
    }

    // PIP explanation
    if (message.includes('pip')) {
      return 'PIP stands for Performance Improvement Plan.\n\n• PIP = 0: Excellent performance\n• PIP = 1: Minor improvement needed\n• PIP = 2+: Significant improvement required\n\nLower PIP counts indicate better performance.';
    }

    // Top performers
    if (message.includes('top') || message.includes('best') || message.includes('performer')) {
      return 'Based on current data:\n\n🥇 #1: Abhishek Basu (Score: 0.93)\n   357 commits, 35 PRs, 60 reviews\n\n🥈 #2-5: Tied at 0.53 score\n   All with 270+ commits\n\nCheck the dashboard for detailed metrics!';
    }

    // Level explanation
    if (message.includes('level') || message.includes('l1') || message.includes('l2')) {
      return 'Employee levels indicate seniority:\n\n• L1: Junior/Entry level\n• L2: Mid-level\n• L3: Senior\n• L4: Staff/Lead\n• L5: Principal/Architect\n\nLevels affect expectations and responsibilities.';
    }

    // GitHub username
    if (message.includes('github') || message.includes('username')) {
      return 'GitHub usernames are used to:\n\n• Track code contributions\n• Link commits to employees\n• Calculate performance metrics\n• Generate activity reports\n\nMake sure your GitHub username is correctly mapped!';
    }

    // Joining date
    if (message.includes('join') || message.includes('date')) {
      return 'Joining dates help us:\n\n• Track tenure\n• Calculate growth over time\n• Adjust expectations for new hires\n• Provide context for performance\n\nNewer employees may have lower metrics initially.';
    }

    // Help/general
    if (message.includes('help') || message.includes('what can you')) {
      return 'I can help you with:\n\n📊 Understanding performance metrics\n🏆 Viewing top performers\n🔢 Explaining ranking calculations\n❓ Answering questions about PIP, levels, etc.\n📈 Interpreting employee data\n\nJust ask me anything!';
    }

    // Default response
    return 'I\'m here to help! You can ask me about:\n\n• Performance metrics\n• Ranking calculations\n• PIP (Performance Improvement Plans)\n• Employee levels\n• Top performers\n• GitHub integration\n\nWhat would you like to know?';
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot thinking and response
    setTimeout(() => {
      const botResponse = {
        type: 'bot',
        text: getBotResponse(inputValue),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 500);
  };

  const handleQuickAction = (actionText) => {
    setInputValue(actionText);
    handleSendMessage();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Chatbot Toggle Button */}
      <button
        className={`chatbot-toggle ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chatbot"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chatbot Window */}
      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="chatbot-header-content">
              <div className="chatbot-avatar">🤖</div>
              <div>
                <h3>Performance Assistant</h3>
                <p className="chatbot-status">
                  <span className="status-dot"></span>
                  Online
                </p>
              </div>
            </div>
            <button
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chatbot"
            >
              ✕
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${message.type}`}
              >
                {message.type === 'bot' && (
                  <div className="message-avatar">🤖</div>
                )}
                <div className="message-content">
                  <div className="message-text">{message.text}</div>
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className="quick-actions">
              <p className="quick-actions-title">Quick questions:</p>
              <div className="quick-actions-grid">
                {quickActions.map(action => (
                  <button
                    key={action.id}
                    className="quick-action-btn"
                    onClick={() => handleQuickAction(action.text)}
                  >
                    <span className="quick-action-icon">{action.icon}</span>
                    <span className="quick-action-text">{action.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="chatbot-input">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              className="chatbot-input-field"
            />
            <button
              onClick={handleSendMessage}
              className="chatbot-send-btn"
              disabled={!inputValue.trim()}
            >
              <span>➤</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default Chatbot;
