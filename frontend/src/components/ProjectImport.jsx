/**
 * 项目导入组件
 *
 * 提供Git仓库导入、代码分析、知识提取功能
 */

import React, { useState, useEffect } from 'react';
import { GitBranch, Download, Search, FileText, Trash2 } from 'lucide-react';
import api from '../api/client';

const ProjectImport = () => {
  const [projects, setProjects] = useState([]);
  const [repoUrl, setRepoUrl] = useState('');
  const [projectName, setProjectName] = useState('');
  const [branch, setBranch] = useState('');
  const [importing, setImporting] = useState(false);
  const [analyzing, setAnalyzing] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.get('/api/import/projects');
      setProjects(response.data.projects);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleImport = async () => {
    if (!repoUrl || !projectName) {
      alert('请填写仓库URL和项目名称');
      return;
    }

    setImporting(true);
    try {
      await api.post('/api/import/clone', {
        repo_url: repoUrl,
        project_name: projectName,
        branch: branch || null
      });

      alert('导入成功！');
      setRepoUrl('');
      setProjectName('');
      setBranch('');
      loadProjects();
    } catch (error) {
      alert('导入失败: ' + error.message);
    } finally {
      setImporting(false);
    }
  };

  const handleAnalyze = async (name) => {
    setAnalyzing(name);
    try {
      const response = await api.post(`/api/import/analyze/${name}`);
      setAnalysisResult(response.data);
    } catch (error) {
      alert('分析失败: ' + error.message);
    } finally {
      setAnalyzing(null);
    }
  };

  const handleDelete = async (name) => {
    if (!confirm(`确定要删除项目 ${name} 吗？`)) return;

    try {
      await api.delete(`/api/import/projects/${name}`);
      alert('删除成功！');
      loadProjects();
    } catch (error) {
      alert('删除失败: ' + error.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* 导入表单 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Download className="w-5 h-5 mr-2" />
          导入Git仓库
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              仓库URL *
            </label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              项目名称 *
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="my-project"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              分支（可选）
            </label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleImport}
            disabled={importing}
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {importing ? '导入中...' : '开始导入'}
          </button>
        </div>
      </div>

      {/* 已导入项目列表 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <GitBranch className="w-5 h-5 mr-2" />
          已导入项目 ({projects.length})
        </h2>

        <div className="space-y-3">
          {projects.map((project) => (
            <div
              key={project.name}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
            >
              <div className="flex-1">
                <h3 className="font-medium">{project.name}</h3>
                <p className="text-sm text-gray-500">
                  大小: {project.size_mb} MB
                </p>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => handleAnalyze(project.name)}
                  disabled={analyzing === project.name}
                  className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
                >
                  {analyzing === project.name ? '分析中...' : '分析'}
                </button>
                <button
                  onClick={() => handleDelete(project.name)}
                  className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {projects.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              暂无导入的项目
            </div>
          )}
        </div>
      </div>

      {/* 分析结果 */}
      {analysisResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Search className="w-5 h-5 mr-2" />
            分析结果
          </h2>

          <div className="space-y-4">
            {/* 语言统计 */}
            <div>
              <h3 className="font-medium mb-2">编程语言</h3>
              <div className="space-y-2">
                {analysisResult.languages.languages.map((lang) => (
                  <div key={lang.language} className="flex items-center">
                    <span className="w-32">{lang.language}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-500 h-4 rounded-full"
                        style={{ width: `${lang.file_percentage}%` }}
                      />
                    </div>
                    <span className="ml-2 text-sm text-gray-600">
                      {lang.file_percentage}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 技术栈 */}
            <div>
              <h3 className="font-medium mb-2">技术栈</h3>
              <div className="flex flex-wrap gap-2">
                {analysisResult.tech_stack.frameworks.map((fw) => (
                  <span
                    key={fw}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                  >
                    {fw}
                  </span>
                ))}
                {analysisResult.tech_stack.tools.map((tool) => (
                  <span
                    key={tool}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* 统计信息 */}
            <div>
              <h3 className="font-medium mb-2">统计信息</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-blue-600">
                    {analysisResult.statistics.total_files}
                  </div>
                  <div className="text-sm text-gray-600">文件数</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-green-600">
                    {analysisResult.statistics.code_files}
                  </div>
                  <div className="text-sm text-gray-600">代码文件</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-purple-600">
                    {analysisResult.statistics.total_size_mb} MB
                  </div>
                  <div className="text-sm text-gray-600">总大小</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectImport;
