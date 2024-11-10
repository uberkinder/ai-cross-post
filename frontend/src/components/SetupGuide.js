import React from 'react';
import './SetupGuide.css';

const SetupGuide = () => {
  return (
    <div className="setup-guide">
      <h2>Setup Guide</h2>
      <div className="setup-steps">
        <div className="step">
          <div className="step-number">1</div>
          <div className="step-content">
            <h3>Add Bot to Channel</h3>
            <p>Add @YourBotName to your Telegram channel as an administrator</p>
          </div>
        </div>
        <div className="step">
          <div className="step-number">2</div>
          <div className="step-content">
            <h3>Get Channel ID</h3>
            <p>Either:</p>
            <ul>
              <li>Forward any message from your channel to the bot</li>
              <li>Or type /getid in your channel</li>
            </ul>
          </div>
        </div>
        <div className="step">
          <div className="step-number">3</div>
          <div className="step-content">
            <h3>Start Cross-Posting</h3>
            <p>New posts in your channel will automatically appear in the queue below</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetupGuide; 