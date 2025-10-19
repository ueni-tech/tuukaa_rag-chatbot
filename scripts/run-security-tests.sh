#!/bin/bash

# セキュリティ機能のテストを実行するスクリプト

set -e

echo "======================================"
echo "セキュリティ機能のテストを開始します"
echo "======================================"
echo ""

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# バックエンドのテスト
echo -e "${BLUE}[1/3] バックエンドのユニットテストを実行${NC}"
echo "--------------------------------------"
cd backend

if command -v poetry &> /dev/null; then
    echo "Poetry環境でテストを実行中..."
    
    # セキュリティ機能のテストのみを実行
    if poetry run pytest tests/test_security_features.py -v; then
        echo -e "${GREEN}✓ バックエンドのテストが成功しました${NC}"
    else
        echo -e "${RED}✗ バックエンドのテストが失敗しました${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Poetry がインストールされていません${NC}"
    exit 1
fi

cd ..
echo ""

# ログマスキングの確認
echo -e "${BLUE}[2/3] ログマスキングの確認${NC}"
echo "--------------------------------------"
echo "バックエンドのログを確認してください："
echo ""
echo -e "${YELLOW}コマンド:${NC}"
echo "  docker-compose logs backend | tail -n 50"
echo ""
echo "確認項目："
echo "  ✓ ip_hash: IPアドレスがハッシュ化されている"
echo "  ✓ key_hash: APIキーがハッシュ化されている"
echo "  ✓ question_hash: 質問がハッシュ化されている"
echo "  ✓ timestamp: タイムスタンプが含まれている"
echo "  ✗ 質問の実テキストが含まれていない"
echo "  ✗ 生のIPアドレスが含まれていない"
echo ""

# ブラウザテストの案内
echo -e "${BLUE}[3/3] ブラウザテスト${NC}"
echo "--------------------------------------"
echo "ブラウザでテストページにアクセスしてください："
echo ""
echo -e "${GREEN}URL: http://localhost:3000/security-test${NC}"
echo ""
echo "テスト項目："
echo "  1. 制御文字のサニタイゼーション"
echo "  2. 最大長制限（2000文字）"
echo "  3. モデル名インジェクション防止"
echo "  4. ID類のバリデーション"
echo "  5. 通常のリクエスト"
echo ""

# まとめ
echo "======================================"
echo -e "${GREEN}テスト実行完了${NC}"
echo "======================================"
echo ""
echo "次のステップ："
echo "  1. ブラウザテストページで手動テストを実行"
echo "  2. バックエンドのログを確認してマスキングを検証"
echo "  3. すべてのテストが成功したことを確認"
echo ""

