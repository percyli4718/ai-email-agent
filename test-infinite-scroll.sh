#!/bin/bash
# 测试无限滚动加载功能

echo "========================================"
echo "测试邮件列表无限滚动加载功能"
echo "========================================"
echo ""

API_URL="http://localhost:8080/api/emails"

# 获取总邮件数
TOTAL=$(curl -s "$API_URL?limit=1&offset=0" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
echo "数据库中总邮件数：$TOTAL"
echo ""

# 计算应该有多少页
PAGES=$(( (TOTAL + 19) / 20 ))
echo "预计页数：$PAGES 页（每页 20 封）"
echo ""

# 测试每一页
echo "逐页测试..."
for i in $(seq 1 $PAGES); do
    OFFSET=$(( ($i - 1) * 20 ))
    RESULT=$(curl -s "$API_URL?limit=20&offset=$OFFSET" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'页{i}: {len(d[\"emails\"])}封，total={d[\"total\"]}')")
    echo "  $RESULT"
done

echo ""
echo "========================================"
echo "前端测试说明:"
echo "1. 打开浏览器访问 http://localhost:3000"
echo "2. 查看左侧邮件列表是否显示 '20 封邮件'"
echo "3. 滚动到底部或点击 '加载更多...' 按钮"
echo "4. 应该能看到邮件数量增加到 40、60..."
echo "5. 最终可以加载全部 $TOTAL 封邮件"
echo "========================================"
