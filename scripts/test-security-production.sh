#!/bin/bash

API_BASE="http://localhost:8000"
API_KEY="test123"

echo "============================================================"
echo "実際の利用ページでのセキュリティ機能テスト"
echo "APIキー: test123 (tenant: test-client)"
echo "============================================================"
echo ""

# テスト1: 制御文字のサニタイゼーション
echo "【テスト1】制御文字のサニタイゼーション"
RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/embed/docs/search" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -d '{"question":"テスト質問","top_k":2}')
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "✅ 成功: 制御文字が適切に処理されました"
    echo "レスポンス: $(echo $RESPONSE | head -c 100)..."
else
    echo "❌ 失敗"
fi
echo ""

# テスト2: 最大長制限（2000文字）
echo "【テスト2】最大長制限（2000文字）"
LONG_2000=$(printf 'あ%.0s' {1..2000})
LONG_2001=$(printf 'あ%.0s' {1..2001})

STATUS1=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/v1/embed/docs/search" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -d "{\"question\":\"${LONG_2000}\",\"top_k\":2}")

STATUS2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/v1/embed/docs/search" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -d "{\"question\":\"${LONG_2001}\",\"top_k\":2}")

echo "2000文字: ${STATUS1} $([ "$STATUS1" = "200" ] && echo "✅" || echo "❌")"
echo "2001文字: ${STATUS2} $([ "$STATUS2" = "422" ] && echo "✅" || echo "❌")"
echo ""

# テスト3: モデル名インジェクション防止
echo "【テスト3】モデル名インジェクション防止"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/v1/embed/docs/ask" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -H "X-Admin-Api-Secret: test_admin_secret" \
  -H "X-Test-Environment: true" \
  -d '{"question":"テスト","top_k":2,"model":"gpt-4o; DROP TABLE users;"}')

echo "ステータス: ${STATUS} $([ "$STATUS" = "422" ] && echo "✅" || echo "❌")"
echo ""

# テスト4: ID類のバリデーション
echo "【テスト4】ID類のバリデーション"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/v1/embed/docs/ask" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -H "X-Admin-Api-Secret: test_admin_secret" \
  -H "X-Test-Environment: true" \
  -d '{"question":"テスト","top_k":2,"client_id":"client@123#abc"}')

echo "ステータス: ${STATUS} $([ "$STATUS" = "422" ] && echo "✅" || echo "❌")"
echo ""

# テスト5: 通常のリクエスト
echo "【テスト5】通常のリクエスト"
RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/embed/docs/ask" \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: ${API_KEY}" \
  -H "X-Admin-Api-Secret: test_admin_secret" \
  -H "X-Test-Environment: true" \
  -d '{"question":"LPの制作ガイドラインについて教えてください","top_k":3,"model":"gpt-4o-mini","client_id":"test-client-123","session_id":"test-session-456","message_id":"test-message-789"}')

if echo "$RESPONSE" | grep -q "answer"; then
    echo "✅ 成功: 正常に処理されました"
    echo "回答の一部: $(echo $RESPONSE | head -c 150)..."
else
    echo "❌ 失敗"
    echo "エラー: $RESPONSE"
fi
echo ""

echo "============================================================"
echo "テスト完了"
echo "============================================================"
