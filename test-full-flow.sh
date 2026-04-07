#!/bin/bash
# Layer 1/2/3 全流程测试脚本

echo "========================================"
echo "AI Email Agent 全流程测试"
echo "========================================"
echo ""

API_URL="http://localhost:8080"

# 步骤 1: 获取最新邮件
echo "步骤 1: 获取最新邮件"
echo "----------------------------------------"
LATEST=$(curl -s "$API_URL/api/emails?limit=1&offset=0")
EMAIL_ID=$(echo "$LATEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['emails'][0]['id'] if d['emails'] else '')")
echo "最新邮件 ID: $EMAIL_ID"
echo ""

if [ -z "$EMAIL_ID" ]; then
    echo "错误：没有邮件"
    exit 1
fi

# 步骤 2: 测试 Layer 1 - 分类接口
echo "步骤 2: 测试 Layer 1 - 分类接口"
echo "----------------------------------------"
echo "POST /api/layer1/classify"
LAYER1_RESULT=$(curl -s -X POST "$API_URL/api/layer1/classify" \
  -H "Content-Type: application/json" \
  -d "{\"email_id\": \"$EMAIL_ID\"}")
echo "$LAYER1_RESULT" | python3 -m json.tool 2>/dev/null || echo "$LAYER1_RESULT"
echo ""

# 步骤 3: 测试 Layer 2 - 检索接口
echo "步骤 3: 测试 Layer 2 - 检索接口"
echo "----------------------------------------"
echo "GET /api/emails/{email_id}/retrieval"
LAYER2_RESULT=$(curl -s "$API_URL/api/emails/$EMAIL_ID/retrieval")
echo "$LAYER2_RESULT" | python3 -m json.tool 2>/dev/null || echo "$LAYER2_RESULT"
echo ""

# 步骤 4: 测试 Layer 3 - 报价接口
echo "步骤 4: 测试 Layer 3 - 报价接口"
echo "----------------------------------------"
echo "POST /api/quotes/generate"
LAYER3_RESULT=$(curl -s -X POST "$API_URL/api/quotes/generate" \
  -H "Content-Type: application/json" \
  -d "{\"email_id\": \"$EMAIL_ID\"}")
echo "$LAYER3_RESULT" | python3 -m json.tool 2>/dev/null || echo "$LAYER3_RESULT"
echo ""

# 步骤 5: 测试工作流接口
echo "步骤 5: 测试工作流接口"
echo "----------------------------------------"
echo "GET /api/emails/{email_id}/workflow"
WORKFLOW_RESULT=$(curl -s "$API_URL/api/emails/$EMAIL_ID/workflow")
echo "$WORKFLOW_RESULT" | python3 -m json.tool 2>/dev/null || echo "$WORKFLOW_RESULT"
echo ""

# 步骤 6: 测试分析接口 (Layer 1+2+3 综合结果)
echo "步骤 6: 测试分析接口 (Layer 1+2+3 综合结果)"
echo "----------------------------------------"
echo "GET /api/emails/{email_id}/analysis"
ANALYSIS_RESULT=$(curl -s "$API_URL/api/emails/$EMAIL_ID/analysis")
echo "$ANALYSIS_RESULT" | python3 -m json.tool 2>/dev/null || echo "$ANALYSIS_RESULT"
echo ""

echo "========================================"
echo "测试完成！"
echo "========================================"
echo ""
echo "Layer 1 验证点:"
echo "  - 分类结果包含 type, priority_score, urgency"
echo "  - 识别出产品和区域"
echo ""
echo "Layer 2 验证点:"
echo "  - 返回相似邮件列表"
echo "  - 返回定价政策"
echo "  - 返回合规要求"
echo ""
echo "Layer 3 验证点:"
echo "  - 生成报价单"
echo "  - 包含 quote_id, total_amount, items"
echo ""
