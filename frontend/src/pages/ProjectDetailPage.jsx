// Project Detail Page - 完整功能版
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout, Card, Descriptions, Button, Space, Spin, message,
  Modal, Form, Input, Select, Table, Tag, Tabs, List, Avatar, Breadcrumb
} from 'antd';
import {
  ArrowLeftOutlined, PlusOutlined, UserOutlined,
  PlayCircleOutlined, TeamOutlined, FileTextOutlined, EditOutlined, DeleteOutlined, HomeOutlined
} from '@ant-design/icons';
import { projectsAPI } from '../api/client';
import axios from 'axios';

const { Header, Content } = Layout;
const { TextArea } = Input;

export default function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [taskModalVisible, setTaskModalVisible] = useState(false);
  const [memberModalVisible, setMemberModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [memberForm] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadProject();
    loadMembers();
    loadTasks();
  }, [id]);

  const loadProject = async () => {
    setLoading(true);
    try {
      const response = await projectsAPI.get(id);
      setProject(response.data);
    } catch (error) {
      message.error('加载项目失败');
      console.error('Load project error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async () => {
    try {
      const response = await projectsAPI.getMembers(id);
      setMembers(response.data);
    } catch (error) {
      console.error('Load members error:', error);
    }
  };

  const loadTasks = async () => {
    try {
      const token = localStorage.getItem('token');
      // 获取项目的所有会话（任务）
      const response = await axios.get(`http://localhost:8000/workflow/tasks?project_id=${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTasks(response.data);
    } catch (error) {
      console.error('Load tasks error:', error);
      // 如果API不存在，使用空数组
      setTasks([]);
    }
  };

  const handleCreateTask = async (values) => {
    try {
      const token = localStorage.getItem('token');
      // 先创建会话
      const sessionResponse = await axios.post('http://localhost:8000/workflow/sessions', {
        project_id: parseInt(id),
        meta_data: { priority: values.priority || 'medium' }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // 然后创建任务
      await axios.post('http://localhost:8000/workflow/tasks', {
        session_id: sessionResponse.data.id,
        title: values.title,
        description: values.requirement
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      message.success('任务创建成功');
      setTaskModalVisible(false);
      form.resetFields();
      loadTasks();
    } catch (error) {
      message.error('创建任务失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleAddMember = async (values) => {
    try {
      await projectsAPI.addMember(id, values);
      message.success('成员添加成功');
      setMemberModalVisible(false);
      memberForm.resetFields();
      loadMembers();
    } catch (error) {
      message.error('添加成员失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditProject = async (values) => {
    try {
      await projectsAPI.update(id, values);
      message.success('项目更新成功');
      setEditModalVisible(false);
      loadProject();
    } catch (error) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const showEditModal = () => {
    editForm.setFieldsValue({
      name: project.name,
      description: project.description
    });
    setEditModalVisible(true);
  };

  const handleDeleteProject = () => {
    Modal.confirm({
      title: '确认删除项目',
      content: `确定要删除项目"${project.name}"吗？此操作不可恢复，将删除所有相关数据（任务、成员等）。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await projectsAPI.delete(id);
          message.success('项目已删除');
          navigate('/projects');
        } catch (error) {
          message.error('删除失败: ' + (error.response?.data?.detail || error.message));
        }
      }
    });
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

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      ellipsis: true
    },
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => navigate(`/tasks/${record.id}`)}>
          查看详情
        </Button>
      )
    }
  ];

  const memberColumns = [
    {
      title: '用户',
      dataIndex: 'user_id',
      key: 'user_id',
      render: (userId, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <span>用户 {userId}</span>
        </Space>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const colors = { owner: 'gold', admin: 'blue', member: 'green', viewer: 'default' };
        return <Tag color={colors[role]}>{role}</Tag>;
      }
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (time) => new Date(time).toLocaleString('zh-CN')
    }
  ];

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin size="large" />
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <Card>
            <p>项目不存在</p>
            <Button onClick={() => navigate('/projects')}>返回项目列表</Button>
          </Card>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
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
                title: project.name
              }
            ]}
          />
          <h2 style={{ margin: 0 }}>{project.name}</h2>
        </Space>
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={showEditModal}
          >
            编辑项目
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setTaskModalVisible(true)}
          >
            创建任务
          </Button>
          <Button
            icon={<TeamOutlined />}
            onClick={() => setMemberModalVisible(true)}
          >
            添加成员
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleDeleteProject}
          >
            删除项目
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Tabs
          defaultActiveKey="info"
          items={[
            {
              key: 'info',
              label: <span><FileTextOutlined /> 项目信息</span>,
              children: (
                <Card>
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="项目名称" span={2}>{project.name}</Descriptions.Item>
                    <Descriptions.Item label="项目描述" span={2}>
                      {project.description || '暂无描述'}
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">
                      {new Date(project.created_at).toLocaleString('zh-CN')}
                    </Descriptions.Item>
                    <Descriptions.Item label="更新时间">
                      {new Date(project.updated_at).toLocaleString('zh-CN')}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              )
            },
            {
              key: 'tasks',
              label: <span><PlayCircleOutlined /> 任务列表 ({tasks.length})</span>,
              children: (
                <Card>
                  <Table
                    columns={taskColumns}
                    dataSource={tasks}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                  />
                </Card>
              )
            },
            {
              key: 'members',
              label: <span><TeamOutlined /> 成员管理 ({members.length})</span>,
              children: (
                <Card>
                  <Table
                    columns={memberColumns}
                    dataSource={members}
                    rowKey="id"
                    pagination={false}
                  />
                </Card>
              )
            }
          ]}
        />
      </Content>

      {/* 创建任务Modal */}
      <Modal
        title="创建新任务"
        open={taskModalVisible}
        onCancel={() => setTaskModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} onFinish={handleCreateTask} layout="vertical">
          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="例如：用户登录功能" />
          </Form.Item>
          <Form.Item
            name="requirement"
            label="需求描述"
            rules={[{ required: true, message: '请输入需求描述' }]}
          >
            <TextArea
              rows={6}
              placeholder="请详细描述您的需求，例如：创建一个用户登录功能，包含用户名密码验证..."
            />
          </Form.Item>
          <Form.Item
            name="priority"
            label="优先级"
            initialValue="medium"
          >
            <Select>
              <Select.Option value="low">低</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="high">高</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setTaskModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">
                创建任务
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑项目Modal */}
      <Modal
        title="编辑项目"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        <Form form={editForm} onFinish={handleEditProject} layout="vertical">
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="输入项目名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="项目描述"
          >
            <TextArea rows={4} placeholder="输入项目描述" />
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setEditModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加成员Modal */}
      <Modal
        title="添加项目成员"
        open={memberModalVisible}
        onCancel={() => setMemberModalVisible(false)}
        footer={null}
      >
        <Form form={memberForm} onFinish={handleAddMember} layout="vertical">
          <Form.Item
            name="user_id"
            label="用户ID"
            rules={[{ required: true, message: '请输入用户ID' }]}
          >
            <Input type="number" placeholder="输入要添加的用户ID" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            initialValue="member"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="owner">所有者</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
              <Select.Option value="member">成员</Select.Option>
              <Select.Option value="viewer">查看者</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setMemberModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">
                添加成员
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
}
