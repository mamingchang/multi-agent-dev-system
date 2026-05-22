#!/bin/bash
# 快速功能测试脚本

set -e  # 遇到错误立即退出

echo "========================================="
echo "Multi-Agent Dev System - 快速功能测试"
echo "========================================="

CLI="./cli/main.py"
TEST_USER="test_user_$(date +%s)"
TEST_PROJECT="test_project_$(date +%s)"

echo ""
echo "1. 测试用户管理..."
echo "-------------------"
$CLI user init --username $TEST_USER
$CLI user whoami
$CLI user list

echo ""
echo "2. 测试项目模板导入..."
echo "-------------------"
$CLI import templates
$CLI import template --template web-app --name $TEST_PROJECT --user $TEST_USER

echo ""
echo "3. 测试进度管理..."
echo "-------------------"
$CLI progress show $TEST_PROJECT --user $TEST_USER

echo ""
echo "4. 测试阶段管理..."
echo "-------------------"
$CLI progress phase-start $TEST_PROJECT requirement_analysis --user $TEST_USER
$CLI progress phase $TEST_PROJECT requirement_analysis --user $TEST_USER

echo ""
echo "5. 测试任务管理..."
echo "-------------------"
$CLI progress task-create $TEST_PROJECT \
  --title "测试任务1" \
  --phase requirement_analysis \
  --priority high \
  --agent Requester \
  --user $TEST_USER

$CLI progress tasks $TEST_PROJECT --user $TEST_USER

$CLI progress task-update $TEST_PROJECT task-001 \
  --status in_progress \
  --progress 50 \
  --user $TEST_USER

$CLI progress tasks $TEST_PROJECT --user $TEST_USER

echo ""
echo "6. 测试项目导出..."
echo "-------------------"
OUTPUT_FILE="/tmp/${TEST_PROJECT}.mas"
$CLI export package $TEST_PROJECT --output $OUTPUT_FILE --user $TEST_USER

if [ -f "$OUTPUT_FILE" ]; then
  echo "✅ 项目包已创建: $OUTPUT_FILE"
  ls -lh $OUTPUT_FILE
else
  echo "❌ 项目包创建失败"
  exit 1
fi

echo ""
echo "7. 测试进度报告导出..."
echo "-------------------"
REPORT_FILE="/tmp/${TEST_PROJECT}_report.md"
$CLI export report $TEST_PROJECT --format markdown --output $REPORT_FILE --user $TEST_USER

if [ -f "$REPORT_FILE" ]; then
  echo "✅ 进度报告已创建: $REPORT_FILE"
  echo ""
  echo "报告内容预览:"
  head -n 20 $REPORT_FILE
else
  echo "❌ 进度报告创建失败"
  exit 1
fi

echo ""
echo "8. 测试项目包导入..."
echo "-------------------"
RESTORED_PROJECT="${TEST_PROJECT}_restored"
$CLI import package --file $OUTPUT_FILE --name $RESTORED_PROJECT --user $TEST_USER

$CLI progress show $RESTORED_PROJECT --user $TEST_USER

echo ""
echo "========================================="
echo "✅ 所有测试通过！"
echo "========================================="
echo ""
echo "测试用户: $TEST_USER"
echo "测试项目: $TEST_PROJECT"
echo "项目包: $OUTPUT_FILE"
echo "进度报告: $REPORT_FILE"
echo "恢复项目: $RESTORED_PROJECT"
echo ""
echo "清理测试数据:"
echo "  rm -rf users/$TEST_USER"
echo "  rm $OUTPUT_FILE $REPORT_FILE"
