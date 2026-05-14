// Login Page - 现代化设计
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, RobotOutlined } from '@ant-design/icons';
import { authAPI } from '../api/client';
import { useAuthStore } from '../store';

const { Title, Text, Paragraph } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((state) => state.setAuth);

  // 获取用户原本想访问的路径
  const from = location.state?.from || '/projects';

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await authAPI.login(values.username, values.password);
      const { access_token, user } = response.data;
      setAuth(user, access_token);
      message.success('登录成功！');

      // 跳转回用户原本想访问的页面
      navigate(from, { replace: true });
    } catch (error) {
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '24px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 480,
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          border: 'none'
        }}
        bodyStyle={{ padding: 48 }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          {/* Logo和标题 */}
          <div>
            <div style={{
              width: 80,
              height: 80,
              margin: '0 auto 24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 20,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)'
            }}>
              <RobotOutlined style={{ fontSize: 40, color: 'white' }} />
            </div>
            <Title level={2} style={{ marginBottom: 8 }}>
              Multi-Agent System
            </Title>
            <Paragraph type="secondary" style={{ fontSize: 14 }}>
              AI驱动的自动化软件开发协作平台
            </Paragraph>
          </div>

          {/* 登录表单 */}
          <Form
            name="login"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
            style={{ marginTop: 24 }}
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: '#999' }} />}
                placeholder="用户名"
                style={{ borderRadius: 8 }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#999' }} />}
                placeholder="密码"
                style={{ borderRadius: 8 }}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 48,
                  fontSize: 16,
                  fontWeight: 500,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: 8,
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
                }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          {/* 提示信息 */}
          <div style={{
            marginTop: 24,
            padding: 16,
            background: '#f5f7fa',
            borderRadius: 8,
            textAlign: 'left'
          }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              💡 测试账号
            </Text>
            <div style={{ marginTop: 8 }}>
              <Text style={{ fontSize: 12, display: 'block' }}>
                用户名: <Text code>admin</Text>
              </Text>
              <Text style={{ fontSize: 12, display: 'block' }}>
                密码: <Text code>admin123</Text>
              </Text>
            </div>
          </div>

          {/* 功能特性 */}
          <div style={{
            marginTop: 24,
            textAlign: 'left',
            padding: 16,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
            borderRadius: 8
          }}>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
              ✨ 核心功能
            </Text>
            <Space direction="vertical" size="small">
              <Text style={{ fontSize: 12 }}>🤖 多Agent智能协作</Text>
              <Text style={{ fontSize: 12 }}>💬 实时对话与反馈</Text>
              <Text style={{ fontSize: 12 }}>🎯 需求锚点防偏离</Text>
              <Text style={{ fontSize: 12 }}>👥 人工介入机制</Text>
            </Space>
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <a onClick={() => navigate('/register')} style={{ color: '#667eea', fontSize: 14 }}>
              注册新账号
            </a>
          </div>
        </Space>
      </Card>
    </div>
  );
}
