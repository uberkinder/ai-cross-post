import React, { useState, useEffect } from 'react';
import PlatformSetupModal from './PlatformSetupModal';
import './CrossPostMatrix.css';

const platforms = [
  { 
    id: 'telegram', 
    name: 'Telegram',
    icon: '/assets/icons/telegram.svg'
  },
  { 
    id: 'twitter', 
    name: 'X',
    icon: '/assets/icons/twitter.svg'
  }
];

const CrossPostMatrix = ({ posts, onPreview, onApprove, setupToken }) => {
  const [setupModal, setSetupModal] = useState({ isOpen: false, platform: null });
  const [connectedPlatforms, setConnectedPlatforms] = useState({
    telegram: false,
    twitter: false
  });

  // Проверяем статус подключения при загрузке и при изменении токена
  useEffect(() => {
    checkPlatformsConnection();
  }, [setupToken]);

  const checkPlatformsConnection = async () => {
    // Проверяем Telegram
    try {
      const response = await fetch(`http://localhost:8000/api/telegram/check-connection`, {
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      const data = await response.json();
      setConnectedPlatforms(prev => ({
        ...prev,
        telegram: data.connected
      }));
    } catch (error) {
      console.error('Error checking Telegram connection:', error);
    }
    
    // Здесь можно добавить проверку других платформ
  };

  const renderPlatformCell = (platform) => (
    <div className="platform-cell">
      <div className="platform-info">
        <img 
          src={platform.icon} 
          alt={platform.name} 
          className="platform-icon"
        />
        <div className="platform-status">
          <div className="platform-name">{platform.name}</div>
          {connectedPlatforms[platform.id] ? (
            <button 
              className="connected-button"
              onClick={() => setSetupModal({ isOpen: true, platform })}
            >
              Connected
            </button>
          ) : (
            <button 
              className="setup-button"
              onClick={() => setSetupModal({ isOpen: true, platform })}
            >
              Setup
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="cross-post-matrix">
        <table>
          <thead>
            <tr>
              <th>From \ To</th>
              {platforms.map(platform => (
                <th key={platform.id}>
                  <div className="platform-header">
                    <img 
                      src={platform.icon} 
                      alt={platform.name} 
                      className="platform-icon"
                    />
                    {platform.name}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {platforms.map(fromPlatform => (
              <tr key={fromPlatform.id}>
                <td>
                  {renderPlatformCell(fromPlatform)}
                </td>
                {platforms.map(toPlatform => {
                  const isActive = fromPlatform.id === 'telegram' && toPlatform.id === 'twitter';
                  return (
                    <td key={`${fromPlatform.id}-${toPlatform.id}`} className={isActive ? 'active' : 'inactive'}>
                      {fromPlatform.id === toPlatform.id ? (
                        '—'
                      ) : (
                        <div className="cell-content">
                          <div className="direction-icons">
                            <img 
                              src={fromPlatform.icon} 
                              alt={fromPlatform.name} 
                              className="direction-icon"
                            />
                            <span className="arrow">→</span>
                            <img 
                              src={toPlatform.icon} 
                              alt={toPlatform.name} 
                              className="direction-icon"
                            />
                          </div>
                          <div className="cell-actions">
                            <button 
                              onClick={() => onPreview(fromPlatform.id, toPlatform.id)}
                              disabled={!isActive}
                            >
                              Preview
                            </button>
                            <button 
                              onClick={() => onApprove(fromPlatform.id, toPlatform.id)}
                              disabled={!isActive}
                            >
                              Approve
                            </button>
                          </div>
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {setupModal.isOpen && (
        <PlatformSetupModal
          platform={setupModal.platform}
          isOpen={setupModal.isOpen}
          onClose={() => {
            setSetupModal({ isOpen: false, platform: null });
            checkPlatformsConnection(); // Проверяем статус после закрытия модального окна
          }}
          setupToken={setupToken}
        />
      )}
    </>
  );
};

export default CrossPostMatrix; 