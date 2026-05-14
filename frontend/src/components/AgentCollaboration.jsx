/**
 * Agent协作可视化组件
 *
 * 显示Agent工作流和协作状态
 */

import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import api from '../api/client';

const AgentCollaboration = ({ taskId }) => {
  const [workflow, setWorkflow] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  const agentColors = {
    'Requester': 'bg-blue-500',
    'ProductManager': 'bg-green-500',
    'Architect': 'bg-purple-500',
    'Developer': 'bg-yellow-500',
    'CodeReviewer': 'bg-red-500',
    'Tester': 'bg-pink-500',
    'DevOps': 'bg-indigo-500'
  };

  const statusIcons = {
    'pending': <Clock className="w-4 h-4" />,
    'in_progress': <Activity className="w-4 h-4 animate-spin" />,
    'completed': <CheckCircle className="w-4 h-4" />,
    'failed': <AlertCircle className="w-4 h-4" />
  };

  useEffect(() => {
    loadWorkflow();
    const interval = setInterval(loadWorkflow, 5000);
    return () => clearInterval(interval);
  }, [taskId]);

  const loadWorkflow = async () => {
    try {
      // 模拟数据（实际应该从API获取）
      setAgents([
        { name: 'Requester', status: 'completed', progress: 100 },
        { name: 'ProductManager', status: 'completed', progress: 100 },
        { name: 'Architect', status: 'in_progress', progress: 60 },
        { name: 'Developer', status: 'pending', progress: 0 },
        { name: 'CodeReviewer', status: 'pending', progress: 0 },
        { name: 'Tester', status: 'pending', progress: 0 },
        { name: 'DevOps', status: 'pending', progress: 0 }
      ]);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load workflow:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-6">Agent协作流程</h2>

      {/* 流程图 */}
      <div className="space-y-4">
        {agents.map((agent, index) => (
          <div key={agent.name}>
            {/* Agent卡片 */}
            <div className="flex items-center space-x-4">
              {/* Agent图标 */}
              <div className={`w-12 h-12 ${agentColors[agent.name]} rounded-full flex items-center justify-center text-white font-bold`}>
                {agent.name[0]}
              </div>

              {/* Agent信息 */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{agent.name}</span>
                    <span className={`text-sm ${
                      agent.status === 'completed' ? 'text-green-600' :
                      agent.status === 'in_progress' ? 'text-blue-600' :
                      agent.status === 'failed' ? 'text-red-600' :
                      'text-gray-500'
                    }`}>
                      {statusIcons[agent.status]}
                    </span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {agent.progress}%
                  </span>
                </div>

                {/* 进度条 */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      agent.status === 'completed' ? 'bg-green-500' :
                      agent.status === 'in_progress' ? 'bg-blue-500' :
                      agent.status === 'failed' ? 'bg-red-500' :
                      'bg-gray-400'
                    }`}
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
              </div>
            </div>

            {/* 连接线 */}
            {index < agents.length - 1 && (
              <div className="ml-6 h-8 w-0.5 bg-gray-300" />
            )}
          </div>
        ))}
      </div>

      {/* 统计信息 */}
      <div className="mt-6 grid grid-cols-4 gap-4">
        <div className="text-center p-3 bg-green-50 rounded">
          <div className="text-2xl font-bold text-green-600">
            {agents.filter(a => a.status === 'completed').length}
          </div>
          <div className="text-sm text-gray-600">已完成</div>
        </div>
        <div className="text-center p-3 bg-blue-50 rounded">
          <div className="text-2xl font-bold text-blue-600">
            {agents.filter(a => a.status === 'in_progress').length}
          </div>
          <div className="text-sm text-gray-600">进行中</div>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded">
          <div className="text-2xl font-bold text-gray-600">
            {agents.filter(a => a.status === 'pending').length}
          </div>
          <div className="text-sm text-gray-600">待开始</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(agents.reduce((sum, a) => sum + a.progress, 0) / agents.length)}%
          </div>
          <div className="text-sm text-gray-600">总进度</div>
        </div>
      </div>
    </div>
  );
};

export default AgentCollaboration;
