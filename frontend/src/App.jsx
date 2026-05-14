// Main App Component
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './store';

import LoginPage from './pages/LoginPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import TaskDetailPage from './pages/TaskDetailPage';
import DecisionsPage from './pages/DecisionsPage';
import Dashboard from './pages/Dashboard';

// 受保护的路由 - 保存原始访问路径
function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    // 保存用户原本想访问的路径
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return children;
}

// 根路径重定向
function RootRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return <Navigate to={isAuthenticated ? "/projects" : "/login"} replace />;
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <ProjectDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tasks/:id"
            element={
              <ProtectedRoute>
                <TaskDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/decisions"
            element={
              <ProtectedRoute>
                <DecisionsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<RootRedirect />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
