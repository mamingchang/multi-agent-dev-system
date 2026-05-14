"""
通知系统核心模块

支持邮件、Slack等多种通知渠道。
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..database.models import NotificationType, NotificationChannel, NotificationStatus


class EmailNotifier:
    """邮件通知器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        use_tls: bool = True
    ):
        """
        初始化邮件通知器

        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP端口
            smtp_user: SMTP用户名
            smtp_password: SMTP密码
            from_email: 发件人邮箱
            use_tls: 是否使用TLS
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.use_tls = use_tls

    def send(
        self,
        to_email: str,
        subject: str,
        content: str,
        html: bool = False
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式

        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # 添加内容
            if html:
                part = MIMEText(content, 'html')
            else:
                part = MIMEText(content, 'plain')
            msg.attach(part)

            # 发送邮件
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()

            return True

        except Exception as e:
            print(f"邮件发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False


class SlackNotifier:
    """Slack通知器"""

    def __init__(self, webhook_url: str):
        """
        初始化Slack通知器

        Args:
            webhook_url: Slack Webhook URL
        """
        self.webhook_url = webhook_url

    def send(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        发送Slack消息

        Args:
            text: 消息文本
            blocks: 消息块（Slack Block Kit）
            attachments: 附件

        Returns:
            bool: 是否发送成功
        """
        try:
            payload = {
                "text": text
            }

            if blocks:
                payload["blocks"] = blocks

            if attachments:
                payload["attachments"] = attachments

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Slack消息发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False


class NotificationService:
    """通知服务"""

    @staticmethod
    def format_quota_alert(
        organization_name: str,
        usage_percentage: int,
        tokens_used: int,
        tokens_quota: int,
        alert_level: str
    ) -> Dict[str, str]:
        """
        格式化配额告警通知

        Args:
            organization_name: 组织名称
            usage_percentage: 使用百分比
            tokens_used: 已使用Token
            tokens_quota: Token配额
            alert_level: 告警级别

        Returns:
            dict: 包含subject和content的字典
        """
        level_text = {
            'warning': '⚠️ 警告',
            'critical': '🔴 严重',
            'exceeded': '❌ 超限'
        }.get(alert_level, '通知')

        subject = f"{level_text}: {organization_name} Token配额告警"

        content = f"""
{level_text}

组织: {organization_name}
Token使用情况:
- 已使用: {tokens_used:,}
- 配额: {tokens_quota:,}
- 使用率: {usage_percentage}%

请及时处理，避免影响正常使用。
"""

        return {
            'subject': subject,
            'content': content.strip()
        }

    @staticmethod
    def format_task_completed(
        task_id: str,
        task_title: str,
        project_name: str
    ) -> Dict[str, str]:
        """
        格式化任务完成通知

        Args:
            task_id: 任务ID
            task_title: 任务标题
            project_name: 项目名称

        Returns:
            dict: 包含subject和content的字典
        """
        subject = f"✅ 任务完成: {task_title}"

        content = f"""
任务已完成

项目: {project_name}
任务: {task_title}
任务ID: {task_id}
完成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

查看详情请登录系统。
"""

        return {
            'subject': subject,
            'content': content.strip()
        }

    @staticmethod
    def format_task_failed(
        task_id: str,
        task_title: str,
        project_name: str,
        error_message: str
    ) -> Dict[str, str]:
        """
        格式化任务失败通知

        Args:
            task_id: 任务ID
            task_title: 任务标题
            project_name: 项目名称
            error_message: 错误信息

        Returns:
            dict: 包含subject和content的字典
        """
        subject = f"❌ 任务失败: {task_title}"

        content = f"""
任务执行失败

项目: {project_name}
任务: {task_title}
任务ID: {task_id}
失败时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

错误信息:
{error_message}

请检查并重试。
"""

        return {
            'subject': subject,
            'content': content.strip()
        }

    @staticmethod
    def format_member_added(
        organization_name: str,
        member_name: str,
        role: str
    ) -> Dict[str, str]:
        """
        格式化成员添加通知

        Args:
            organization_name: 组织名称
            member_name: 成员名称
            role: 角色

        Returns:
            dict: 包含subject和content的字典
        """
        subject = f"👥 新成员加入: {organization_name}"

        content = f"""
新成员已加入组织

组织: {organization_name}
成员: {member_name}
角色: {role}
时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

        return {
            'subject': subject,
            'content': content.strip()
        }

    @staticmethod
    def format_slack_quota_alert(
        organization_name: str,
        usage_percentage: int,
        tokens_used: int,
        tokens_quota: int,
        alert_level: str
    ) -> Dict[str, Any]:
        """
        格式化Slack配额告警消息

        Args:
            organization_name: 组织名称
            usage_percentage: 使用百分比
            tokens_used: 已使用Token
            tokens_quota: Token配额
            alert_level: 告警级别

        Returns:
            dict: Slack消息payload
        """
        color = {
            'warning': '#FFA500',  # 橙色
            'critical': '#FF0000',  # 红色
            'exceeded': '#8B0000'   # 深红色
        }.get(alert_level, '#808080')

        level_emoji = {
            'warning': '⚠️',
            'critical': '🔴',
            'exceeded': '❌'
        }.get(alert_level, '📢')

        return {
            'text': f"{level_emoji} Token配额告警",
            'attachments': [{
                'color': color,
                'title': f"{organization_name} - Token使用告警",
                'fields': [
                    {
                        'title': '使用率',
                        'value': f"{usage_percentage}%",
                        'short': True
                    },
                    {
                        'title': '告警级别',
                        'value': alert_level.upper(),
                        'short': True
                    },
                    {
                        'title': '已使用',
                        'value': f"{tokens_used:,} tokens",
                        'short': True
                    },
                    {
                        'title': '配额',
                        'value': f"{tokens_quota:,} tokens",
                        'short': True
                    }
                ],
                'footer': 'Multi-Agent Dev System',
                'ts': int(datetime.utcnow().timestamp())
            }]
        }
