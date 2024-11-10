import React, { useState, useEffect } from 'react';
import './PlatformSetupModal.css';

const PlatformSetupModal = ({ platform, isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [stepStatuses, setStepStatuses] = useState({
    connection: 'pending',    // pending, loading, success, error
    channelId: 'pending',
    permissions: 'pending'
  });
  const [setupToken, setSetupToken] = useState(null);
  const [botUrl, setBotUrl] = useState(null);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (isOpen && platform.id === 'telegram') {
      console.log('Modal opened, checking all steps...');
      fetchSetupToken();
      checkAllSteps();
    }
  }, [isOpen, platform]);

  const checkAllSteps = async () => {
    try {
      // Проверяем подключение аккаунта
      const connectionResponse = await fetch('http://localhost:8000/api/telegram/setup');
      const connectionData = await connectionResponse.json();
      
      if (connectionData.connected) {
        setIsConnected(true);
        setStepStatuses(prev => ({
          ...prev,
          connection: 'success'
        }));

        // Если аккаунт подключен, проверяем канал
        const channelResponse = await fetch(`http://localhost:8000/api/telegram/check-channel`, {
          headers: {
            'Authorization': `Bearer ${connectionData.token || setupToken}`
          }
        });
        const channelData = await channelResponse.json();
        
        if (channelData.hasChannel) {
          setStepStatuses(prev => ({
            ...prev,
            channelId: 'success'
          }));

          // Если канал подключен, проверяем права
          const permissionsResponse = await fetch(`http://localhost:8000/api/telegram/check-permissions`, {
            headers: {
              'Authorization': `Bearer ${connectionData.token || setupToken}`
            }
          });
          const permissionsData = await permissionsResponse.json();
          
          if (permissionsData.hasPermissions) {
            setStepStatuses(prev => ({
              ...prev,
              permissions: 'success'
            }));
          }
        }
      }
    } catch (error) {
      console.error('Error checking steps:', error);
    }
  };

  const fetchSetupToken = async () => {
    try {
      console.log('Fetching setup token...');
      const response = await fetch('http://localhost:8000/api/telegram/setup');
      const data = await response.json();
      console.log('Received setup data:', data);
      
      if (data.connected) {
        setIsConnected(true);
        setStepStatuses(prev => ({
          ...prev,
          connection: 'success'
        }));
      } else if (data.token && data.bot_url) {
        setSetupToken(data.token);
        setBotUrl(data.bot_url);
      }
    } catch (error) {
      console.error('Error fetching setup token:', error);
    }
  };

  const checkTelegramConnection = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telegram/check-connection`, {
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      const data = await response.json();
      return data.connected;
    } catch (error) {
      console.error('Error checking connection:', error);
      return false;
    }
  };

  const checkChannelPermissions = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telegram/check-permissions`, {
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      const data = await response.json();
      return data.hasPermissions;
    } catch (error) {
      console.error('Error checking permissions:', error);
      return false;
    }
  };

  const checkChannelLink = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telegram/check-channel`, {
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      const data = await response.json();
      return data.hasChannel;
    } catch (error) {
      console.error('Error checking channel link:', error);
      return false;
    }
  };

  const getTelegramSteps = () => {
    console.log('Rendering steps with:', { botUrl, setupToken });
    
    return [
      {
        id: 'connection',
        title: "Connect Your Account",
        description: isConnected ? 
          "Your Telegram account is connected" : 
          "Click the button below to connect your Telegram account:",
        status: stepStatuses.connection,
        checkStatus: checkTelegramConnection,
        content: stepStatuses.connection === 'success' ? (
          <div className="token-section">
            <button 
              className="disconnect-button"
              onClick={disconnectAllTelegram}
            >
              Disconnect Account
            </button>
          </div>
        ) : (
          <div className="token-section">
            {botUrl && setupToken ? (
              <>
                <a 
                  href={botUrl} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="primary-button"
                  onClick={() => handleCheck({
                    id: 'connection',
                    checkStatus: checkTelegramConnection
                  })}
                >
                  Connect Telegram
                </a>
                <div className="token-display">
                  <small>Token: {setupToken}</small>
                </div>
              </>
            ) : (
              <button 
                className="secondary-button"
                onClick={fetchSetupToken}
              >
                Retry Connection
              </button>
            )}
          </div>
        )
      },
      {
        id: 'channelId',
        title: "Link Your Channel",
        description: "Choose your channel to post from",
        status: stepStatuses.channelId,
        disabled: stepStatuses.connection !== 'success',
        checkStatus: checkChannelLink,
        content: stepStatuses.channelId === 'success' ? (
          <div className="channel-link-section">
            <button 
              className="disconnect-button"
              onClick={disconnectChannel}
            >
              Disconnect Channel
            </button>
          </div>
        ) : (
          <div className="channel-link-section">
            <p>Forward any post from it to <a 
              href="https://t.me/feedsAIbot" 
              target="_blank" 
              rel="noopener noreferrer"
              className="bot-link"
            >
              @feedsAIbot
            </a></p>
            <button 
              className="check-button"
              onClick={() => handleCheck({
                id: 'channelId',
                checkStatus: checkChannelLink
              })}
            >
              Check Channel
            </button>
          </div>
        )
      },
      {
        id: 'permissions',
        title: "Grant Permissions",
        description: "Add @feedsAIbot as administrator with these permissions:",
        list: [
          "Read Messages",
          "Send Messages",
          "Edit Messages",
          "Delete Messages"
        ],
        status: stepStatuses.permissions,
        disabled: stepStatuses.channelId !== 'success',
        checkStatus: checkChannelPermissions,
        content: stepStatuses.permissions !== 'success' && (
          <div className="permissions-section">
            <ul>
              {[
                "Read Messages",
                "Send Messages",
                "Edit Messages",
                "Delete Messages"
              ].map((permission, index) => (
                <li key={index}>{permission}</li>
              ))}
            </ul>
            <button 
              className="check-button"
              onClick={() => handleCheck({
                id: 'permissions',
                checkStatus: checkChannelPermissions
              })}
              disabled={stepStatuses.channelId !== 'success'}
            >
              Check Permissions
            </button>
          </div>
        )
      }
    ];
  };

  const getXSteps = () => [
    {
      title: "Coming Soon",
      description: "X (Twitter) integration is coming soon"
    }
  ];

  const getSteps = () => {
    switch (platform.id) {
      case 'telegram':
        return getTelegramSteps();
      case 'twitter':
        return getXSteps();
      default:
        return [];
    }
  };

  const handleCheck = async (step) => {
    if (step.checkStatus) {
      setStepStatuses(prev => ({
        ...prev,
        [step.id]: 'loading'
      }));

      const result = await step.checkStatus();
      
      setStepStatuses(prev => ({
        ...prev,
        [step.id]: result ? 'success' : 'error'
      }));
    }
  };

  const isComplete = () => {
    return Object.values(stepStatuses).every(status => status === 'success');
  };

  const disconnectTelegram = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/telegram/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      if (response.ok) {
        setStepStatuses({
          connection: 'pending',
          channelId: 'pending',
          permissions: 'pending'
        });
        setShowDisconnectConfirm(false);
      }
    } catch (error) {
      console.error('Error disconnecting Telegram:', error);
    }
  };

  const disconnectAllTelegram = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/telegram/disconnect-all', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      if (response.ok) {
        setStepStatuses({
          connection: 'pending',
          channelId: 'pending',
          permissions: 'pending'
        });
        setIsConnected(false);
      }
    } catch (error) {
      console.error('Error disconnecting Telegram:', error);
    }
  };

  const disconnectChannel = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/telegram/disconnect-channel', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      if (response.ok) {
        setStepStatuses(prev => ({
          ...prev,
          channelId: 'pending',
          permissions: 'pending'
        }));
      }
    } catch (error) {
      console.error('Error disconnecting channel:', error);
    }
  };

  if (!isOpen) return null;

  const steps = getSteps();

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <div className="platform-info">
            <img src={platform.icon} alt={platform.name} className="platform-icon" />
            <h2>Connect {platform.name}</h2>
          </div>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          {steps.map((step, index) => (
            <div key={index} className={`setup-step ${step.status} ${step.disabled ? 'disabled' : ''}`}>
              <div className="step-number">{index + 1}</div>
              <div className="step-content">
                <h3>{step.title}</h3>
                <p>{step.description}</p>
                {step.list && (
                  <ul>
                    {step.list.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                )}
                {step.content}
              </div>
              <div className="step-status">
                {step.status === 'success' && '✓'}
                {step.status === 'error' && '✗'}
                {step.status === 'loading' && '...'}
              </div>
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button className="back-button" onClick={onClose}>
            Back
          </button>
          {isComplete() && (
            <>
              <button className="continue-button" onClick={onClose}>
                Continue
              </button>
              <button 
                className="disconnect-button" 
                onClick={() => setShowDisconnectConfirm(true)}
              >
                Disconnect Telegram
              </button>
            </>
          )}
        </div>

        {showDisconnectConfirm && (
          <div className="confirm-dialog">
            <div className="confirm-content">
              <h3>Disconnect Telegram?</h3>
              <p>Are you sure you want to disconnect your Telegram account?</p>
              <div className="confirm-buttons">
                <button 
                  className="cancel-button"
                  onClick={() => setShowDisconnectConfirm(false)}
                >
                  Cancel
                </button>
                <button 
                  className="disconnect-confirm-button"
                  onClick={disconnectTelegram}
                >
                  Disconnect
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlatformSetupModal; 