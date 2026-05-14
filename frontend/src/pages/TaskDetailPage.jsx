// 任务详情页 - 现代化Agent协作界面
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout, Card, Button, Space, Spin, message, Input,
  Avatar, Typography, Tag, Divider, Empty, Modal, Badge, Timeline, Progress, Breadcrumb, Mentions
} from 'antd';
import {
  ArrowLeftOutlined, PlayCircleOutlined, SendOutlined,
  RobotOutlined, UserOutlined, CheckCircleOutlined,
  CloseCircleOutlined, LoadingOutlined, ThunderboltOutlined,
  CommentOutlined, EyeOutlined, WarningOutlined, HomeOutlined, FolderOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Header, Content, Sider } = Layout;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

// Agent列表
const AGENTS = [
  { name: 'RequirementAnalyst', label: '需求分析师', color: '#1890ff' },
  { name: 'Architect', label: '架构师', color: '#722ed1' },
  { name: 'Developer', label: '开发工程师', color: '#52c41a' },
  { name: 'CodeReviewer', label: '代码审查员', color: '#fa8c16' },
  { name: 'Tester', label: '测试工程师', color: '#eb2f96' }
];

export default function TaskDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [task, setTask] = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [executing, setExecuting] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadTask();
    loadHistory();
    // 自动连接WebSocket
    connectWebSocket();

    // 清理函数：组件卸载时关闭WebSocket
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [id]);

  // 当messages变化时自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 页面加载完成后也滚动一次（确保初始加载时能看到最新消息）
  useEffect(() => {
    if (!loading && messages.length > 0) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 200);
    }
  }, [loading]);

  const loadTask = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:8000/workflow/tasks/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTask(response.data);

      // 获取session信息以获取project_id
      const sessionResponse = await axios.get(`http://localhost:8000/workflow/sessions/${response.data.session_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjectId(sessionResponse.data.project_id);

      if (['in_requirement', 'in_design', 'in_development', 'in_review', 'in_testing', 'in_deployment'].includes(response.data.status)) {
        setExecuting(true);
      }
    } catch (error) {
      message.error('加载任务失败');
      console.error('Load task error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:8000/workflow/tasks/${id}/events`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const msgs = response.data.map(event => ({
        id: event.id,
        type: event.agent_name ? 'agent' : 'system',
        sender: event.agent_name || 'System',
        content: typeof event.content === 'object' ? event.content.message : event.content,
        timestamp: event.created_at,
        eventType: event.event_type
      }));

      setMessages(msgs);

      // 加载完历史消息后，延迟滚动到底部
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      console.error('Load history error:', error);
    }
  };

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    const wsUrl = `ws://localhost:8000/ws/tasks/${id}?token=${token}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'agent_message') {
        // 为什么：WebSocket收到消息后，数据库也会保存这条消息
        // 为了避免重复显示，我们使用临时ID，并在下次loadHistory时会被数据库的真实消息替换
        // 或者更好的方案：收到WebSocket消息后，重新加载历史（但要防止频繁刷新）

        // 方案1：直接添加临时消息（可能重复）
        const tempMsg = {
          id: `temp-${Date.now()}`,  // 临时ID
          type: 'agent',
          sender: data.agent_name,
          content: data.content,
          timestamp: new Date().toISOString(),
          eventType: data.event_type
        };

        // 检查是否已存在相同内容的消息（简单去重）
        setMessages(prev => {
          const exists = prev.some(msg =>
            msg.sender === data.agent_name &&
            msg.content === data.content &&
            Math.abs(new Date(msg.timestamp) - new Date()) < 5000  // 5秒内的消息
          );

          if (exists) {
            console.log('消息已存在，跳过添加');
            return prev;
          }

          return [...prev, tempMsg];
        });
      } else if (data.type === 'status_update') {
        setTask(prev => ({ ...prev, status: data.status, current_agent: data.current_agent }));
      } else if (data.type === 'workflow_complete') {
        setExecuting(false);
        message.success('工作流执行完成');
      } else if (data.type === 'error') {
        message.error('执行出错: ' + data.message);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error);
      message.error('实时连接出错');
    };

    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
      setWs(null);
    };

    setWs(websocket);
  };

  const handleStartWorkflow = () => {
    Modal.confirm({
      title: '🚀 启动多Agent协作',
      content: (
        <div>
          <Paragraph>系统将启动以下Agent进行协作：</Paragraph>
          <Timeline
            items={[
              { children: '需求分析师 - 分析需求' },
              { children: '架构师 - 设计架构' },
              { children: '开发工程师 - 编写代码' },
              { children: '代码审查员 - 审查代码' },
              { children: '测试工程师 - 测试验证' }
            ]}
          />
          <Paragraph type="secondary" style={{ marginTop: 16 }}>
            Agent之间会进行讨论和审查，确保高质量交付。
          </Paragraph>
        </div>
      ),
      okText: '启动',
      cancelText: '取消',
      width: 600,
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');

          await axios.post(`http://localhost:8000/workflow/tasks/${id}/execute`, {
            agents: ['RequirementAnalyst', 'Architect', 'Developer', 'CodeReviewer', 'Tester'],
            max_iterations: 10,
            llm_config: {
              type: 'claude',
              model: 'claude-sonnet-4-5',
              temperature: 0.7
            }
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });

          setExecuting(true);
          message.success('工作流已启动');
          connectWebSocket();

          setMessages(prev => [...prev, {
            id: Date.now(),
            type: 'system',
            sender: 'System',
            content: '🚀 多Agent协作工作流已启动，Agent开始协作...',
            timestamp: new Date().toISOString()
          }]);

        } catch (error) {
          message.error('启动失败: ' + (error.response?.data?.detail || error.message));
        }
      }
    });
  };

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    // 提取@提及的Agent
    const mentionedAgents = [];
    const mentionRegex = /@(\w+)/g;
    let match;
    while ((match = mentionRegex.exec(userInput)) !== null) {
      mentionedAgents.push(match[1]);
    }

    const userMsg = {
      id: Date.now(),
      type: 'user',
      sender: 'You',
      content: userInput,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);

    // 立即清空输入框（无论发送成功还是失败）
    const messageToSend = userInput;
    setUserInput('');

    try {
      const token = localStorage.getItem('token');

      console.log('发送消息:', messageToSend);
      console.log('提及的Agent:', mentionedAgents);

      // 检查工作流是否已启动（通过检查active_orchestrators）
      // 如果未启动，先启动工作流
      try {
        const response = await axios.post(`http://localhost:8000/workflow/tasks/${id}/human_message`, {
          content: messageToSend,
          mentioned_agents: mentionedAgents,
          action: 'continue'
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('消息发送成功:', response.data);
      } catch (error) {
        console.log('消息发送失败:', error.response?.status, error.response?.data);
        // 如果返回"工作流未运行"，则先启动工作流
        if (error.response?.status === 400 && error.response?.data?.detail?.includes('工作流未运行')) {
          console.log('工作流未启动，正在启动...');

          // 启动工作流
          await axios.post(`http://localhost:8000/workflow/tasks/${id}/execute`, {
            agents: ['RequirementAnalyst', 'Architect', 'Developer', 'CodeReviewer', 'Tester'],
            max_iterations: 10,
            llm_config: {
              type: 'claude',
              model: 'claude-sonnet-4-5',
              temperature: 0.7
            }
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });

          // 等待一下让工作流启动
          await new Promise(resolve => setTimeout(resolve, 1000));

          // 重新发送消息
          await axios.post(`http://localhost:8000/workflow/tasks/${id}/human_message`, {
            content: messageToSend,
            mentioned_agents: mentionedAgents,
            action: 'continue'
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
        } else {
          throw error;
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      created: 'default',
      in_requirement: 'blue',
      in_design: 'cyan',
      in_development: 'orange',
      in_review: 'purple',
      in_testing: 'geekblue',
      in_deployment: 'gold',
      completed: 'green',
      rejected: 'red'
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status) => {
    const texts = {
      created: '已创建',
      in_requirement: '需求分析中',
      in_design: '设计中',
      in_development: '开发中',
      in_review: '代码审查中',
      in_testing: '测试中',
      in_deployment: '部署中',
      completed: '已完成',
      rejected: '已拒绝'
    };
    return texts[status] || status;
  };

  const getAgentAvatar = (agentName) => {
    const colors = {
      'RequirementAnalyst': '#1890ff',
      'Architect': '#722ed1',
      'Developer': '#52c41a',
      'CodeReviewer': '#fa8c16',
      'Tester': '#eb2f96',
      'DevOps': '#13c2c2',
      'ProjectManager': '#faad14'
    };
    return colors[agentName] || '#999';
  };

  const getEventIcon = (eventType) => {
    const icons = {
      'started': <ThunderboltOutlined style={{ color: '#1890ff' }} />,
      'output': <CommentOutlined style={{ color: '#52c41a' }} />,
      'thinking': <LoadingOutlined style={{ color: '#faad14' }} />,
      'approval': <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      'objection': <WarningOutlined style={{ color: '#ff4d4f' }} />
    };
    return icons[eventType] || <CommentOutlined />;
  };

  const renderMessage = (msg) => {
    if (msg.type === 'system') {
      return (
        <div key={msg.id} style={{
          textAlign: 'center',
          margin: '24px 0',
          padding: '16px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
        }}>
          <Text style={{
            color: 'white',
            fontSize: 14,
            fontWeight: 500
          }}>
            {msg.content}
          </Text>
        </div>
      );
    }

    const isUser = msg.type === 'user';
    const isAgent = msg.type === 'agent';

    return (
      <div
        key={msg.id}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 20,
          animation: 'fadeIn 0.3s ease-in'
        }}
      >
        {!isUser && (
          <Avatar
            size={40}
            style={{
              backgroundColor: isAgent ? getAgentAvatar(msg.sender) : '#999',
              marginRight: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }}
            icon={<RobotOutlined />}
          />
        )}

        <div style={{ maxWidth: '70%' }}>
          <div style={{ marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text strong style={{ fontSize: 13 }}>
              {msg.sender}
            </Text>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {new Date(msg.timestamp).toLocaleTimeString('zh-CN')}
            </Text>
            {msg.eventType && (
              <Tag
                icon={getEventIcon(msg.eventType)}
                color={msg.eventType === 'approval' ? 'success' : msg.eventType === 'objection' ? 'error' : 'processing'}
                style={{ fontSize: 11, marginLeft: 4 }}
              >
                {msg.eventType}
              </Tag>
            )}
          </div>
          <Card
            size="small"
            style={{
              backgroundColor: isUser ? '#1890ff' : '#ffffff',
              color: isUser ? 'white' : 'inherit',
              borderRadius: 12,
              border: isUser ? 'none' : '1px solid #f0f0f0',
              boxShadow: isUser
                ? '0 4px 12px rgba(24, 144, 255, 0.3)'
                : '0 2px 8px rgba(0,0,0,0.08)'
            }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            <Paragraph
              style={{
                marginBottom: 0,
                whiteSpace: 'pre-wrap',
                color: isUser ? 'white' : 'inherit',
                fontSize: 14,
                lineHeight: 1.6
              }}
            >
              {msg.content}
            </Paragraph>
          </Card>
        </div>

        {isUser && (
          <Avatar
            size={40}
            style={{
              backgroundColor: '#1890ff',
              marginLeft: 12,
              boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
            }}
            icon={<UserOutlined />}
          />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Spin size="large" />
      </Layout>
    );
  }

  if (!task) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <Card>
            <Empty description="任务不存在" />
            <Button onClick={() => navigate(-1)}>返回</Button>
          </Card>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Header style={{
        background: 'white',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <Space direction="vertical" size="small" style={{ flex: 1 }}>
          {/* 面包屑导航 */}
          <Breadcrumb
            items={[
              {
                title: (
                  <a onClick={() => navigate('/projects')}>
                    <HomeOutlined /> 项目列表
                  </a>
                )
              },
              {
                title: projectId ? (
                  <a onClick={() => navigate(`/projects/${projectId}`)}>
                    <FolderOutlined /> 项目详情
                  </a>
                ) : '...'
              },
              {
                title: task?.title || '任务详情'
              }
            ]}
          />

          {/* 任务标题和状态 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Title level={4} style={{ margin: 0 }}>{task.title}</Title>
            <Tag color={getStatusColor(task.status)}>{getStatusText(task.status)}</Tag>
            {executing && (
              <Badge status="processing" text="执行中" />
            )}
          </div>
        </Space>
        <Space>
          {task.current_agent && (
            <Tag color="blue" icon={<RobotOutlined />}>
              当前: {task.current_agent}
            </Tag>
          )}
          <Tag color="cyan" icon={<RobotOutlined />}>
            💬 使用@提及Agent开始协作
          </Tag>
        </Space>
      </Header>

      <Content style={{
        padding: '24px',
        display: 'flex',
        gap: 24,
        height: 'calc(100vh - 120px)',  // 固定高度：视口高度减去Header高度
        overflow: 'hidden'  // 防止Content本身滚动
      }}>
        {/* 主对话区域 */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',  // 占满Content高度
          overflow: 'hidden'
        }}>
          <Card
            style={{
              height: '100%',  // 占满父容器
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}
            bodyStyle={{
              flex: 1,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              padding: 24,
              height: 0  // 关键：配合flex: 1使用
            }}
          >
            {/* 任务描述 */}
            <Card
              size="small"
              style={{
                marginBottom: 16,
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                border: 'none',
                borderRadius: 12,
                flexShrink: 0  // 不允许收缩
              }}
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong style={{ fontSize: 13, color: '#666' }}>📋 任务需求</Text>
                <Paragraph style={{ marginBottom: 0, marginTop: 8, fontSize: 14 }}>
                  {task.description}
                </Paragraph>
              </Space>
            </Card>

            {/* 消息列表 - 可滚动区域 */}
            <div style={{
              flex: 1,
              overflow: 'auto',
              marginBottom: 16,
              paddingRight: 8,
              minHeight: 0  // 关键：允许flex子元素滚动
            }}>
              {messages.length === 0 ? (
                <Empty
                  description="暂无对话记录，使用@提及Agent开始协作"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  style={{ marginTop: 60 }}
                />
              ) : (
                <>
                  {messages.map(renderMessage)}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* 人工介入输入框 - 固定在底部 */}
            <div style={{
              padding: 16,
              background: '#fafafa',
              borderRadius: 12,
              border: '1px solid #f0f0f0',
              flexShrink: 0  // 不允许收缩，始终显示
            }}>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <Mentions
                  value={userInput}
                  onChange={setUserInput}
                  placeholder="💬 输入您的意见或决策，使用@提及特定Agent唤醒工作流..."
                  autoSize={{ minRows: 2, maxRows: 4 }}
                  style={{ width: '100%' }}
                  options={AGENTS.map(agent => ({
                    value: agent.name,
                    label: (
                      <Space>
                        <Avatar
                          size="small"
                          style={{ backgroundColor: agent.color }}
                          icon={<RobotOutlined />}
                        />
                        <span>{agent.label}</span>
                      </Space>
                    )
                  }))}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    💡 使用@提及Agent，按Ctrl+Enter发送
                  </Text>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    disabled={!userInput.trim()}
                    size="small"
                  >
                    发送
                  </Button>
                </div>
              </Space>
            </div>
          </Card>
        </div>

        {/* 右侧信息面板 */}
        <div style={{ width: 320 }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 进度卡片 */}
            <Card
              title="📊 执行进度"
              size="small"
              style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>当前状态</Text>
                  <div style={{ marginTop: 8 }}>
                    <Tag color={getStatusColor(task.status)} style={{ fontSize: 13 }}>
                      {getStatusText(task.status)}
                    </Tag>
                  </div>
                </div>
                {task.current_agent && (
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>当前Agent</Text>
                    <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Avatar
                        size="small"
                        style={{ backgroundColor: getAgentAvatar(task.current_agent) }}
                        icon={<RobotOutlined />}
                      />
                      <Text strong>{task.current_agent}</Text>
                    </div>
                  </div>
                )}
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>消息数量</Text>
                  <div style={{ marginTop: 8 }}>
                    <Badge count={messages.length} showZero color="#1890ff" />
                  </div>
                </div>
              </Space>
            </Card>

            {/* Agent列表 */}
            <Card
              title="🤖 参与Agent"
              size="small"
              style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {['RequirementAnalyst', 'Architect', 'Developer', 'CodeReviewer', 'Tester'].map(agent => (
                  <div
                    key={agent}
                    style={{
                      padding: '8px 12px',
                      background: task.current_agent === agent ? '#e6f7ff' : '#fafafa',
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      border: task.current_agent === agent ? '1px solid #1890ff' : '1px solid transparent'
                    }}
                  >
                    <Avatar
                      size="small"
                      style={{ backgroundColor: getAgentAvatar(agent) }}
                      icon={<RobotOutlined />}
                    />
                    <Text style={{ fontSize: 12 }}>{agent}</Text>
                    {task.current_agent === agent && (
                      <LoadingOutlined style={{ marginLeft: 'auto', color: '#1890ff' }} />
                    )}
                  </div>
                ))}
              </Space>
            </Card>
          </Space>
        </div>
      </Content>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </Layout>
  );
}
