/**
 * 主仪表板页面 - 优化版
 * 使用Ant Design组件 + 自定义样式
 */

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Card, Row, Col, Button, Typography, Input, Checkbox } from 'antd';
import {
  HomeOutlined,
  MessageOutlined,
  DownloadOutlined,
  TeamOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import IMChat from '../components/IMChat';
import ProjectImport from '../components/ProjectImport';
import AgentCollaboration from '../components/AgentCollaboration';
import LanguageSwitcher from '../components/LanguageSwitcher';

const { Header, Sider, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const Dashboard = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('home');

  const menuItems = [
    { key: 'home', icon: <HomeOutlined />, label: '首页' },
    { key: 'chat', icon: <MessageOutlined />, label: 'IM群聊' },
    { key: 'import', icon: <DownloadOutlined />, label: '项目导入' },
    { key: 'collaboration', icon: <TeamOutlined />, label: 'Agent协作' },
    { key: 'settings', icon: <SettingOutlined />, label: '设置' }
  ];

  const userMenu = (
    <Menu items={[
      { key: 'profile', label: '个人资料', icon: <UserOutlined /> },
      { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, danger: true }
    ]} />
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 欢迎卡片 */}
            <Card
              bordered={false}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white'
              }}
            >
              <Title level={2} style={{ color: 'white', marginBottom: 8 }}>
                <RocketOutlined /> 欢迎使用多Agent开发协作平台
              </Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16, marginBottom: 0 }}>
                AI驱动的全流程自动化软件开发系统，让开发更高效
              </Paragraph>
            </Card>

            {/* 统计卡片 */}
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Card className="card-shadow" bordered={false}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, fontWeight: 700, color: '#667eea', marginBottom: 8 }}>
                      7
                    </div>
                    <Text strong style={{ fontSize: 16, color: '#64748b' }}>AI Agent</Text>
                    <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 8 }}>
                      协同工作完成开发任务
                    </div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card className="card-shadow" bordered={false}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, fontWeight: 700, color: '#10b981', marginBottom: 8 }}>
                      19
                    </div>
                    <Text strong style={{ fontSize: 16, color: '#64748b' }}>核心功能</Text>
                    <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 8 }}>
                      覆盖全流程开发需求
                    </div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card className="card-shadow" bordered={false}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, fontWeight: 700, color: '#8b5cf6', marginBottom: 8 }}>
                      95%
                    </div>
                    <Text strong style={{ fontSize: 16, color: '#64748b' }}>完成度</Text>
                    <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 8 }}>
                      生产就绪，可立即使用
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>

            {/* 快速操作 */}
            <Card title={<><ThunderboltOutlined /> 快速操作</>} bordered={false} className="card-shadow">
              <Row gutter={[16, 16]}>
                <Col xs={12} sm={6}>
                  <Button
                    type="dashed"
                    block
                    size="large"
                    icon={<DownloadOutlined style={{ fontSize: 24 }} />}
                    onClick={() => setActiveTab('import')}
                    style={{ height: 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                  >
                    <div style={{ marginTop: 8 }}>导入项目</div>
                  </Button>
                </Col>
                <Col xs={12} sm={6}>
                  <Button
                    type="dashed"
                    block
                    size="large"
                    icon={<MessageOutlined style={{ fontSize: 24 }} />}
                    onClick={() => setActiveTab('chat')}
                    style={{ height: 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                  >
                    <div style={{ marginTop: 8 }}>IM群聊</div>
                  </Button>
                </Col>
                <Col xs={12} sm={6}>
                  <Button
                    type="dashed"
                    block
                    size="large"
                    icon={<TeamOutlined style={{ fontSize: 24 }} />}
                    onClick={() => setActiveTab('collaboration')}
                    style={{ height: 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                  >
                    <div style={{ marginTop: 8 }}>查看协作</div>
                  </Button>
                </Col>
                <Col xs={12} sm={6}>
                  <Button
                    type="dashed"
                    block
                    size="large"
                    icon={<SettingOutlined style={{ fontSize: 24 }} />}
                    onClick={() => setActiveTab('settings')}
                    style={{ height: 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                  >
                    <div style={{ marginTop: 8 }}>系统设置</div>
                  </Button>
                </Col>
              </Row>
            </Card>

            {/* 功能特性 */}
            <Card title={<><CheckCircleOutlined /> 核心特性</>} bordered={false} className="card-shadow">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Card type="inner" size="small">
                    <Text strong>🤖 智能Agent</Text>
                    <Paragraph style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>
                      7个专业AI Agent协同工作
                    </Paragraph>
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card type="inner" size="small">
                    <Text strong>💬 实时协作</Text>
                    <Paragraph style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>
                      IM群聊、@提及、人工介入
                    </Paragraph>
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card type="inner" size="small">
                    <Text strong>🔒 企业级</Text>
                    <Paragraph style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>
                      多租户、RBAC、审计日志
                    </Paragraph>
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card type="inner" size="small">
                    <Text strong>🌍 多语言</Text>
                    <Paragraph style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>
                      支持10种语言切换
                    </Paragraph>
                  </Card>
                </Col>
              </Row>
            </Card>
          </Space>
        );

      case 'chat':
        return <IMChat groupId={1} projectId={1} />;

      case 'import':
        return <ProjectImport />;

      case 'collaboration':
        return <AgentCollaboration taskId={1} />;

      case 'settings':
        return (
          <Card title="系统设置" bordered={false} className="card-shadow">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text strong>API密钥配置</Text>
                <Input.Password
                  placeholder="输入API密钥"
                  style={{ marginTop: 8 }}
                />
              </div>
              <div>
                <Text strong>通知设置</Text>
                <Space direction="vertical" style={{ marginTop: 8 }}>
                  <Checkbox defaultChecked>启用邮件通知</Checkbox>
                  <Checkbox defaultChecked>启用浏览器通知</Checkbox>
                  <Checkbox>启用短信通知</Checkbox>
                </Space>
              </div>
              <Button type="primary" size="large" block>
                保存设置
              </Button>
            </Space>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          background: 'linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%)',
        }}
        trigger={null}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: collapsed ? 16 : 20,
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          {collapsed ? 'MA' : 'Multi-Agent'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeTab]}
          items={menuItems}
          onClick={({ key }) => setActiveTab(key)}
          style={{ background: 'transparent', border: 'none' }}
        />
      </Sider>

      <Layout>
        {/* 顶部栏 */}
        <Header style={{
          background: 'white',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: 16 }}
            />
            <Title level={4} style={{ margin: 0 }}>
              {menuItems.find(item => item.key === activeTab)?.label}
            </Title>
          </Space>

          <Space size="middle">
            <LanguageSwitcher />
            <Dropdown menu={userMenu} placement="bottomRight">
              <Avatar
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  cursor: 'pointer'
                }}
                icon={<UserOutlined />}
              />
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区 */}
        <Content style={{
          margin: '24px',
          minHeight: 280,
        }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
