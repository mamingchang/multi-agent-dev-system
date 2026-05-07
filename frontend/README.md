# Frontend - Multi-Agent Dev System

React + Vite + Ant Design 前端应用

## 技术栈

- **React 18** - UI框架
- **Vite** - 构建工具
- **React Router** - 路由
- **Zustand** - 状态管理
- **Ant Design** - UI组件库
- **Axios** - HTTP客户端
- **Recharts** - 图表库
- **Day.js** - 日期处理

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API客户端
│   │   └── client.js     # Axios配置和API方法
│   ├── components/       # 可复用组件
│   ├── pages/            # 页面组件
│   │   ├── LoginPage.jsx
│   │   ├── ProjectsPage.jsx
│   │   └── DecisionsPage.jsx
│   ├── store/            # Zustand状态管理
│   │   └── index.js
│   ├── hooks/            # 自定义Hooks
│   ├── utils/            # 工具函数
│   ├── types/            # TypeScript类型定义
│   ├── App.jsx           # 主应用组件
│   ├── main.jsx          # 入口文件
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML模板
├── vite.config.js        # Vite配置
└── package.json          # 依赖配置
```

## 功能模块

### 1. 认证系统
- 用户登录
- 用户注册
- JWT Token管理
- 自动登出（401）

### 2. 项目管理
- 项目列表
- 创建项目
- 查看项目详情
- 成员管理
- 角色权限展示

### 3. 决策中心
- 待处理决策列表
- 决策详情查看
- 决策处理（批准/拒绝）
- 实时刷新

### 4. 任务追溯
- 任务时间线
- 事件日志展示
- Agent操作历史

## 状态管理

使用Zustand进行全局状态管理：

```javascript
// 认证状态
const { user, token, isAuthenticated, setAuth, logout } = useAuthStore();

// 项目状态
const { projects, currentProject, setProjects } = useProjectStore();

// 决策状态
const { pendingDecisions, setPendingDecisions } = useDecisionStore();
```

## API集成

所有API调用通过`src/api/client.js`：

```javascript
import { authAPI, projectsAPI, decisionsAPI, tasksAPI } from './api/client';

// 登录
const response = await authAPI.login(username, password);

// 获取项目列表
const projects = await projectsAPI.list();

// 处理决策
await decisionsAPI.resolve(decisionId, response);
```

## 环境变量

创建`.env`文件：

```env
VITE_API_URL=http://localhost:8000
```

## 开发指南

### 添加新页面

1. 在`src/pages/`创建页面组件
2. 在`src/App.jsx`添加路由
3. 如需保护路由，使用`<ProtectedRoute>`

### 添加新API

在`src/api/client.js`添加API方法：

```javascript
export const newAPI = {
  method: (params) => apiClient.get('/api/endpoint', { params }),
};
```

### 样式定制

Ant Design主题配置在`src/App.jsx`的`ConfigProvider`中。

## 部署

### 静态部署

```bash
npm run build
# 将dist/目录部署到CDN或静态服务器
```

### Docker部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

## 浏览器支持

- Chrome (最新)
- Firefox (最新)
- Safari (最新)
- Edge (最新)

## 许可证

MIT
