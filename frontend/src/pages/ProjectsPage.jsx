// Projects List Page
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Card, Button, List, Tag, Modal, Form, Input, message, Space } from 'antd';
import { PlusOutlined, TeamOutlined, FolderOutlined } from '@ant-design/icons';
import { projectsAPI } from '../api/client';
import { useProjectStore, useAuthStore } from '../store';

const { Header, Content } = Layout;

export default function ProjectsPage() {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { projects, setProjects, addProject } = useProjectStore();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    loadProjects();
  }, []);

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

  const handleCreate = async (values) => {
    try {
      const response = await projectsAPI.create(values);
      addProject(response.data);
      message.success('项目创建成功');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const getRoleColor = (role) => {
    const colors = { owner: 'gold', admin: 'blue', member: 'green', viewer: 'default' };
    return colors[role] || 'default';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Multi-Agent Dev System</h2>
        <Space>
          <span>欢迎, {user?.username}</span>
          <Button onClick={logout}>退出</Button>
        </Space>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Card
          title="我的项目"
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
              新建项目
            </Button>
          }
        >
          <List
            loading={loading}
            dataSource={projects}
            renderItem={(project) => (
              <List.Item
                actions={[
                  <Button type="link" onClick={() => navigate(`/projects/${project.id}`)}>
                    查看详情
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<FolderOutlined style={{ fontSize: 32 }} />}
                  title={
                    <Space>
                      {project.name}
                      <Tag color={getRoleColor(project.role)}>{project.role}</Tag>
                    </Space>
                  }
                  description={project.description || '暂无描述'}
                />
              </List.Item>
            )}
          />
        </Card>

        <Modal
          title="创建新项目"
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          footer={null}
        >
          <Form form={form} onFinish={handleCreate} layout="vertical">
            <Form.Item name="name" label="项目名称" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="项目描述">
              <Input.TextArea rows={4} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" block>
                创建
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
}
