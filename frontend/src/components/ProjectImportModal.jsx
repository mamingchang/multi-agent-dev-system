/**
 * 项目导入Modal组件
 *
 * 改进：导入项目后自动创建数据库项目记录，与新建项目统一
 */

import { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, message, Steps } from 'antd';
import { GitBranch, Download } from 'lucide-react';
import axios from 'axios';

const { Step } = Steps;

export default function ProjectImportModal({ visible, onCancel, onSuccess }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (visible) {
      loadOrganizations();
      setCurrentStep(0);
      form.resetFields();
    }
  }, [visible]);

  const loadOrganizations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/organizations', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrganizations(response.data);

      // 如果只有一个组织，自动选中
      if (response.data.length === 1) {
        form.setFieldsValue({ organization_id: response.data[0].id });
      }
    } catch (error) {
      message.error('加载组织失败');
    }
  };

  const handleImport = async (values) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      const response = await axios.post('http://localhost:8000/api/import/clone', {
        repo_url: values.repo_url,
        project_name: values.project_name,
        organization_id: values.organization_id,
        branch: values.branch || null,
        description: values.description || null,
        depth: 1  // 浅克隆，加快速度
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      message.success('项目导入成功！');

      // 调用成功回调
      if (onSuccess) {
        onSuccess(response.data.project);
      }

      // 关闭Modal
      onCancel();
    } catch (error) {
      console.error('Import error:', error);
      message.error('导入失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center">
          <Download className="w-5 h-5 mr-2" />
          导入Git项目
        </div>
      }
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      okText="导入"
      cancelText="取消"
      confirmLoading={loading}
      width={600}
    >
      <div className="mb-6">
        <Steps current={currentStep} size="small">
          <Step title="填写信息" />
          <Step title="克隆代码" />
          <Step title="创建项目" />
        </Steps>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleImport}
      >
        <Form.Item
          name="organization_id"
          label="所属组织"
          rules={[{ required: true, message: '请选择组织' }]}
        >
          <Select
            placeholder="选择组织"
            options={organizations.map(org => ({
              label: org.name,
              value: org.id
            }))}
          />
        </Form.Item>

        <Form.Item
          name="repo_url"
          label="Git仓库URL"
          rules={[
            { required: true, message: '请输入仓库URL' },
            { type: 'url', message: '请输入有效的URL' }
          ]}
          extra="支持GitHub、GitLab等Git仓库"
        >
          <Input
            prefix={<GitBranch className="w-4 h-4 text-gray-400" />}
            placeholder="https://github.com/username/repo.git"
          />
        </Form.Item>

        <Form.Item
          name="project_name"
          label="项目名称"
          rules={[
            { required: true, message: '请输入项目名称' },
            { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线' }
          ]}
          extra="用于标识项目，建议使用仓库名称"
        >
          <Input placeholder="my-project" />
        </Form.Item>

        <Form.Item
          name="branch"
          label="分支名称（可选）"
          extra="不填写则使用默认分支"
        >
          <Input placeholder="main 或 master" />
        </Form.Item>

        <Form.Item
          name="description"
          label="项目描述（可选）"
        >
          <Input.TextArea
            rows={3}
            placeholder="简要描述项目用途..."
          />
        </Form.Item>
      </Form>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>提示：</strong>
          导入后的项目将自动创建为正式项目，可以：
        </p>
        <ul className="text-sm text-blue-700 mt-2 ml-4 list-disc">
          <li>创建任务和会话</li>
          <li>使用Agent工作流</li>
          <li>添加团队成员</li>
          <li>进行权限管理</li>
        </ul>
      </div>
    </Modal>
  );
}
