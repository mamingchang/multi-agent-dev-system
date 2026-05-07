// Decisions Page - 决策中心
import { useEffect, useState } from 'react';
import { Layout, Card, List, Button, Modal, Form, Input, Radio, message, Tag, Space } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { decisionsAPI } from '../api/client';
import { useDecisionStore } from '../store';
import dayjs from 'dayjs';

const { Content } = Layout;

export default function DecisionsPage() {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentDecision, setCurrentDecision] = useState(null);
  const [form] = Form.useForm();

  const { pendingDecisions, setPendingDecisions, removeDecision } = useDecisionStore();

  useEffect(() => {
    loadDecisions();
  }, []);

  const loadDecisions = async () => {
    setLoading(true);
    try {
      const response = await decisionsAPI.getPending();
      setPendingDecisions(response.data);
    } catch (error) {
      message.error('加载决策失败');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = (decision) => {
    setCurrentDecision(decision);
    setModalVisible(true);
  };

  const onFinish = async (values) => {
    try {
      await decisionsAPI.resolve(currentDecision.id, values);
      message.success('决策已提交');
      removeDecision(currentDecision.id);
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('提交失败');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <Card title="待处理决策" extra={<Button onClick={loadDecisions}>刷新</Button>}>
          <List
            loading={loading}
            dataSource={pendingDecisions}
            renderItem={(decision) => (
              <List.Item
                actions={[
                  <Button
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => handleResolve(decision)}
                  >
                    处理
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{decision.agent_name}</span>
                      <Tag>{decision.decision_type}</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <div>任务ID: {decision.task_id}</div>
                      <div>创建时间: {dayjs(decision.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>

        <Modal
          title="处理决策"
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          footer={null}
        >
          <Form form={form} onFinish={onFinish} layout="vertical">
            <Form.Item name="approved" label="决策结果" rules={[{ required: true }]}>
              <Radio.Group>
                <Radio value={true}>批准</Radio>
                <Radio value={false}>拒绝</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="message" label="备注" rules={[{ required: true }]}>
              <Input.TextArea rows={4} />
            </Form.Item>
            <Form.Item name="next_agent" label="下一个Agent（可选）">
              <Input placeholder="留空则继续正常流程" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" block>
                提交决策
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
}
