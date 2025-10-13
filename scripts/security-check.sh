#!/bin/bash

# セキュリティチェックスクリプト
# 依存関係の脆弱性スキャンを実行

set -e

echo "======================================"
echo "セキュリティチェックを開始します"
echo "======================================"
echo ""

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# バックエンドのセキュリティチェック
echo -e "${YELLOW}[1/2] バックエンドの脆弱性スキャン${NC}"
echo "--------------------------------------"
cd backend

if command -v poetry &> /dev/null; then
    echo "Poetry環境を確認中..."
    
    # safetyがインストールされているか確認
    if poetry run which safety &> /dev/null; then
        echo "safety でスキャン中..."
        if poetry run safety check --json > /tmp/safety-report.json 2>&1; then
            echo -e "${GREEN}✓ 脆弱性は検出されませんでした${NC}"
        else
            echo -e "${RED}✗ 脆弱性が検出されました${NC}"
            cat /tmp/safety-report.json
            echo ""
            echo "詳細: poetry run safety check --full-report"
        fi
    else
        echo -e "${YELLOW}⚠ safety がインストールされていません${NC}"
        echo "インストール: poetry add --group dev safety"
    fi
else
    echo -e "${RED}✗ Poetry がインストールされていません${NC}"
fi

cd ..
echo ""

# フロントエンドのセキュリティチェック
echo -e "${YELLOW}[2/2] フロントエンドの脆弱性スキャン${NC}"
echo "--------------------------------------"
cd frontend

if command -v npm &> /dev/null; then
    echo "npm audit でスキャン中..."
    
    # 本番依存関係のみチェック
    if npm audit --production --json > /tmp/npm-audit-report.json 2>&1; then
        echo -e "${GREEN}✓ 脆弱性は検出されませんでした${NC}"
    else
        AUDIT_EXIT=$?
        if [ $AUDIT_EXIT -eq 1 ]; then
            echo -e "${RED}✗ 脆弱性が検出されました${NC}"
            npm audit --production
            echo ""
            echo "修正: npm audit fix"
            echo "強制修正: npm audit fix --force"
        fi
    fi
else
    echo -e "${RED}✗ npm がインストールされていません${NC}"
fi

cd ..
echo ""

# まとめ
echo "======================================"
echo -e "${GREEN}セキュリティチェック完了${NC}"
echo "======================================"
echo ""
echo "推奨事項:"
echo "  1. 定期的にこのスクリプトを実行してください"
echo "  2. 脆弱性が検出された場合は速やかに対応してください"
echo "  3. GitHub Dependabot を有効化することを推奨します"
echo ""

