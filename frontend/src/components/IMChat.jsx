/**
 * IM群聊组件
 *
 * 提供群组聊天、@提及、人工介入功能
 */

import React, { useState, useEffect, useRef } from 'react';
import { Send, AtSign, AlertCircle, Users } from 'lucide-react';
import api from '../api/client';

const IMChat = ({ groupId, projectId }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [members, setMembers] = useState([]);
  const [mentions, setMentions] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);

  // 加载消息
  useEffect(() => {
    loadMessages();
    loadMembers();
    loadUnreadCount();

    // 设置轮询
    const interval = setInterval(() => {
      loadMessages();
      loadUnreadCount();
    }, 3000);

    return () => clearInterval(interval);
  }, [groupId]);

  const loadMessages = async () => {
    try {
      const response = await api.get('/api/im/messages', {
        params: { group_id: groupId, limit: 50 }
      });
      setMessages(response.data.messages);
      scrollToBottom();
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const loadMembers = async () => {
    try {
      const response = await api.get(`/api/im/groups/${groupId}/members`);
      setMembers(response.data.members);
    } catch (error) {
      console.error('Failed to load members:', error);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await api.get('/api/im/messages/unread/count', {
        params: { group_id: groupId }
      });
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      await api.post('/api/im/messages', {
        group_id: groupId,
        content: newMessage,
        message_type: 'text'
      });

      setNewMessage('');
      loadMessages();
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAtMention = () => {
    setShowMentions(!showMentions);
  };

  const insertMention = (username) => {
    setNewMessage(prev => prev + `@${username} `);
    setShowMentions(false);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <Users className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold">项目群组</h3>
          <span className="text-sm text-gray-500">({members.length} 成员)</span>
        </div>
        {unreadCount > 0 && (
          <span className="px-2 py-1 text-xs bg-red-500 text-white rounded-full">
            {unreadCount} 未读
          </span>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className="flex space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">
                {msg.sender.username[0].toUpperCase()}
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-baseline space-x-2">
                <span className="font-medium text-sm">{msg.sender.username}</span>
                <span className="text-xs text-gray-500">{formatTime(msg.sent_at)}</span>
              </div>
              <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <div className="relative flex-1">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息... (Shift+Enter 换行)"
              className="w-full px-3 py-2 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
            />

            {/* @提及下拉菜单 */}
            {showMentions && (
              <div className="absolute bottom-full mb-2 w-64 bg-white border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {members.map((member) => (
                  <div
                    key={member.user_id}
                    onClick={() => insertMention(member.username)}
                    className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                  >
                    <div className="font-medium">{member.username}</div>
                    <div className="text-xs text-gray-500">{member.email}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col space-y-2">
            <button
              onClick={handleAtMention}
              className="p-2 text-gray-500 hover:text-blue-500 hover:bg-blue-50 rounded"
              title="@提及"
            >
              <AtSign className="w-5 h-5" />
            </button>
            <button
              onClick={handleSendMessage}
              className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              title="发送"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IMChat;
