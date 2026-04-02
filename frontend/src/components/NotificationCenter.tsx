/**
 * 通知中心组件
 *
 * 功能:
 * - 显示通知列表
 * - 实时 WebSocket 通知推送
 * - 标记通知为已读
 * - 通知类型图标和颜色
 */
import React, { useState, useEffect, useRef } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  related_id: string | null;
  metadata: Record<string, any> | null;
  created_at: string;
}

export interface NotificationCenterProps {
  onNotificationClick?: (notification: Notification) => void;
}

// ============================================================================
// Notification Icon Helper
// ============================================================================

const getNotificationIcon = (type: string): string => {
  const icons: Record<string, string> = {
    email_status: '📧',
    agent_progress: '🤖',
    approval_request: '✅',
    system: '⚙️',
  };
  return icons[type] || '🔔';
};

const getNotificationColor = (level: string): string => {
  const colors: Record<string, string> = {
    info: 'bg-[rgba(59,130,246,0.2)] border-[#3b82f6] text-[#60a5fa]',
    success: 'bg-[rgba(16,185,129,0.2)] border-[#10b981] text-[#10b981]',
    warning: 'bg-[rgba(245,158,11,0.2)] border-[#f59e0b] text-[#f59e0b]',
    error: 'bg-[rgba(239,68,68,0.2)] border-[#ef4444] text-[#ef4444]',
  };
  return colors[level] || colors.info;
};

// ============================================================================
// Notification Card Component
// ============================================================================

interface NotificationCardProps {
  notification: Notification;
  onMarkRead: (id: number) => void;
  onClick?: () => void;
}

const NotificationCard: React.FC<NotificationCardProps> = ({
  notification,
  onMarkRead,
  onClick,
}) => {
  const colorClass = getNotificationColor(notification.level);
  const icon = getNotificationIcon(notification.type);

  return (
    <div
      className={`p-3 rounded-lg border transition-all cursor-pointer ${
        notification.is_read
          ? 'bg-[#0f172a] border-[#1e293b] opacity-70'
          : `${colorClass} bg-opacity-20`
      } hover:border-[#3b82f6]`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 flex-1">
          <span className="text-lg">{icon}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-[#e2e8f0]">{notification.title}</h4>
              {!notification.is_read && (
                <span className="w-2 h-2 rounded-full bg-[#3b82f6]" />
              )}
            </div>
            <p className="text-xs text-[#94a3b8] mt-1">{notification.message}</p>
            <div className="text-xs text-[#64748b] mt-2">
              {new Date(notification.created_at).toLocaleString()}
            </div>
          </div>
        </div>
        {!notification.is_read && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMarkRead(notification.id);
            }}
            className="text-xs text-[#3b82f6] hover:text-[#60a5fa] px-2 py-1"
          >
            标记为已读
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Notification Bell Component
// ============================================================================

interface NotificationBellProps {
  unreadCount: number;
  onClick: () => void;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ unreadCount, onClick }) => (
  <button
    onClick={onClick}
    className="relative p-2 text-[#94a3b8] hover:text-[#e2e8f0] transition-colors"
  >
    <span className="text-xl">🔔</span>
    {unreadCount > 0 && (
      <span className="absolute -top-1 -right-1 bg-[#ef4444] text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
        {unreadCount > 9 ? '9+' : unreadCount}
      </span>
    )}
  </button>
);

// ============================================================================
// Main Component
// ============================================================================

const NotificationCenter: React.FC<NotificationCenterProps> = ({ onNotificationClick }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const wsRef = useRef<WebSocket | null>(null);

  // Load notifications
  const loadNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/notifications');
      const data = await response.json();
      setNotifications(data.notifications || []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId: number) => {
    try {
      await fetch(`/api/notifications/${notificationId}/read`, { method: 'POST' });
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    const unreadIds = notifications.filter(n => !n.is_read).map(n => n.id);
    await Promise.all(unreadIds.map(id => markAsRead(id)));
  };

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const wsUrl = `ws://localhost:8080/ws/notifications?client_id=${clientId}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          setNotifications(prev => [data.notification, ...prev]);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Initial load
  useEffect(() => {
    loadNotifications();
  }, []);

  // Filter notifications
  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <>
      {/* Notification Bell in Header */}
      <NotificationBell unreadCount={unreadCount} onClick={() => setShowPanel(!showPanel)} />

      {/* Notification Panel */}
      {showPanel && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowPanel(false)}
          />

          {/* Panel */}
          <div className="fixed top-16 right-6 w-96 max-h-[600px] bg-[#1e293b] border border-[#334155] rounded-xl shadow-2xl z-50 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-4 py-3 border-b border-[#475569]">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-[#e2e8f0]">
                  🔔 通知中心 | Notification Center
                </h3>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-[#3b82f6] hover:text-[#60a5fa]"
                    >
                      全部已读 | Mark all read
                    </button>
                  )}
                  <button
                    onClick={() => setShowPanel(false)}
                    className="text-[#94a3b8] hover:text-[#e2e8f0]"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex border-b border-[#334155]">
              <button
                className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
                  filter === 'all'
                    ? 'text-[#3b82f6] border-b-2 border-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                    : 'text-[#94a3b8] hover:text-[#e2e8f0]'
                }`}
                onClick={() => setFilter('all')}
              >
                全部 | All ({notifications.length})
              </button>
              <button
                className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
                  filter === 'unread'
                    ? 'text-[#3b82f6] border-b-2 border-[#3b82f6] bg-[rgba(59,130,246,0.1)]'
                    : 'text-[#94a3b8] hover:text-[#e2e8f0]'
                }`}
                onClick={() => setFilter('unread')}
              >
                未读 | Unread ({unreadCount})
              </button>
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[480px] p-3 space-y-2">
              {isLoading ? (
                <div className="text-center text-[#94a3b8] py-8">
                  <div className="text-2xl mb-2">⏳</div>
                  <div>加载中 | Loading...</div>
                </div>
              ) : filteredNotifications.length === 0 ? (
                <div className="text-center text-[#94a3b8] py-8">
                  <div className="text-4xl mb-2">📭</div>
                  <div>暂无通知 | No Notifications</div>
                </div>
              ) : (
                filteredNotifications.map(notification => (
                  <NotificationCard
                    key={notification.id}
                    notification={notification}
                    onMarkRead={markAsRead}
                    onClick={() => {
                      onNotificationClick?.(notification);
                      setShowPanel(false);
                    }}
                  />
                ))
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default NotificationCenter;
