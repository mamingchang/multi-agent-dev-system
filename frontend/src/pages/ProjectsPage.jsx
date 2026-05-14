// Projects List Page - 现代化设计
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layout, Card, Button, Modal, Form, Input, message, Space, Select,
  Row, Col, Typography, Avatar, Statistic, Badge, Empty, Dropdown
} from 'antd';
import {
  PlusOutlined, TeamOutlined, FolderOutlined, DeleteOutlined,
  SettingOutlined, LogoutOutlined, UserOutlined, RocketOutlined,
  CheckCircleOutlined, ClockCircleOutlined, FundOutlined, DownloadOutlined
} from '@ant-design/icons';
import { projectsAPI, organizationsAPI } from '../api/client';
import { useProjectStore, useAuthStore } from '../store';
import ProjectImportModal from '../components/ProjectImportModal';

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

export default function ProjectsPage() {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { projects, setProjects, addProject } = useProjectStore();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    loadProjects();
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      const response = await organizationsAPI.list();
      setOrganizations(response.data);
      if (response.data.length === 1) {
        form.setFieldsValue({ organization_id: response.data[0].id });
      }
    } catch (error) {
      message.error('加载组织失败');
    }
  };

  const loadProjects = async () => {
    setLoading(true);
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (error) {
      message.error('加载项目失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (values) => {
    try {
      const response = await projectsAPI.create(values);
      addProject(response.data);
      message.success('项目创建成功');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('创建项目失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteProject = async (projectId) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除项目将同时删除所有相关数据，此操作不可恢复。确定要删除吗？',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await projectsAPI.delete(projectId);
          setProjects(projects.filter(p => p.id !== projectId));
          message.success('项目已删除');
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置'
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: () => {
        logout();
        navigate('/login');
      }
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Header style={{
        background: 'white',
        padding: '0 48px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <Space size="large">
          <div style={{
            fontSize: 24,
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            🤖 Multi-Agent System
          </div>
        </Space>
        <Space size="large">
          <Button
            type="primary"
            size="large"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: 8,
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
            }}
          >
            新建项目
          </Button>
          <Button
            type="default"
            size="large"
            icon={<DownloadOutlined />}
            onClick={() => setImportModalVisible(true)}
            style={{
              borderRadius: 8,
              borderColor: '#667eea',
              color: '#667eea'
            }}
          >
            导入项目
          </Button>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar
              size="large"
              style={{
                backgroundColor: '#1890ff',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
              }}
              icon={<UserOutlined />}
            />
          </Dropdown>
        </Space>
      </Header>

      <Content style={{ padding: '48px' }}>
        {/* 统计卡片 */}
        <Row gutter={24} style={{ marginBottom: 32 }}>
          <Col span={8}>
            <Card
              style={{
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              }}
              bodyStyle={{ padding: 24 }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>总项目数</span>}
                value={projects.length}
                prefix={<FolderOutlined />}
                valueStyle={{ color: 'white', fontSize: 32 }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card
              style={{
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
              }}
              bodyStyle={{ padding: 24 }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>活跃任务</span>}
                value={0}
                prefix={<RocketOutlined />}
                valueStyle={{ color: 'white', fontSize: 32 }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card
              style={{
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
              }}
              bodyStyle={{ padding: 24 }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>完成任务</span>}
                value={0}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: 'white', fontSize: 32 }}
              />
            </Card>
          </Col>
        </Row>

        {/* 项目列表 */}
        <Card
          title={
            <Space>
              <FolderOutlined style={{ fontSize: 20, color: '#1890ff' }} />
              <span style={{ fontSize: 18, fontWeight: 600 }}>我的项目</span>
            </Space>
          }
          style={{
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
          }}
          bodyStyle={{ padding: 24 }}
        >
          {projects.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Space direction="vertical" size="small">
                  <Text type="secondary">还没有项目</Text>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setModalVisible(true)}
                  >
                    创建第一个项目
                  </Button>
                </Space>
              }
              style={{ padding: '60px 0' }}
            />
          ) : (
            <Row gutter={[24, 24]}>
              {projects.map(project => (
                <Col key={project.id} xs={24} sm={12} lg={8} xl={6}>
                  <Card
                    hoverable
                    style={{
                      borderRadius: 12,
                      border: '1px solid #f0f0f0',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer'
                    }}
                    bodyStyle={{ padding: 20 }}
                    onClick={() => navigate(`/projects/${project.id}`)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-4px)';
                      e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.12)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Avatar
                          size={48}
                          style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
                          }}
                          icon={<FolderOutlined />}
                        />
                        <Dropdown
                          menu={{
                            items: [
                              {
                                key: 'delete',
                                icon: <DeleteOutlined />,
                                label: '删除项目',
                                danger: true,
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  handleDeleteProject(project.id);
                                }
                              }
                            ]
                          }}
                          trigger={['click']}
                        >
                          <Button
                            type="text"
                            icon={<SettingOutlined />}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Dropdown>
                      </div>

                      <div>
                        <Title level={5} style={{ marginBottom: 4 }}>
                          {project.name}
                        </Title>
                        <Paragraph
                          type="secondary"
                          ellipsis={{ rows: 2 }}
                          style={{ marginBottom: 0, fontSize: 13 }}
                        >
                          {project.description || '暂无描述'}
                        </Paragraph>
                      </div>

                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        paddingTop: 12,
                        borderTop: '1px solid #f0f0f0'
                      }}>
                        <Space size="small">
                          <TeamOutlined style={{ color: '#999' }} />
                          <Text type="secondary" style={{ fontSize: 12 }}>1 成员</Text>
                        </Space>
                        <Space size="small">
                          <ClockCircleOutlined style={{ color: '#999' }} />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(project.created_at).toLocaleDateString('zh-CN')}
                          </Text>
                        </Space>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          )}
        </Card>
      </Content>

      {/* 创建项目Modal */}
      <Modal
        title={
          <Space>
            <PlusOutlined style={{ color: '#1890ff' }} />
            <span>创建新项目</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="organization_id"
            label="所属组织"
            rules={[{ required: true, message: '请选择组织' }]}
          >
            <Select
              placeholder="选择组织"
              size="large"
              options={organizations.map(org => ({
                label: org.name,
                value: org.id
              }))}
            />
          </Form.Item>

          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input
              placeholder="输入项目名称"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <Input.TextArea
              placeholder="简要描述项目目标和内容"
              rows={4}
              size="large"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 32 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setModalVisible(false);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none'
                }}
              >
                创建项目
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入项目Modal */}
      <ProjectImportModal
        visible={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        onSuccess={(project) => {
          addProject(project);
          loadProjects();
        }}
      />
    </Layout>
  );
}
