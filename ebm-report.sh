#!/bin/bash
# ============================================================
# ebm-report.sh — EBM (Evidence-Based Medicine) 報告產生器
# 用法：bash ebm-report.sh "肺炎的抗生素選擇"
# 輸出：~/ai-twin/workspace/reports/ebm/ebm-YYYY-MM-DD-slug.md
# ============================================================
set -euo pipefail
source ~/ai-twin/common.sh

LOG=~/ai-twin/logs/ebm-report.log

# ---- 參數檢查 ----
QUERY="${1:-}"
if [ -z "$QUERY" ]; then
    echo "用法：bash ebm-report.sh \"臨床問題\""
    echo "範例：bash ebm-report.sh \"肺炎的抗生素選擇\""
    exit 1
fi

log "=== EBM Report 開始：$QUERY ==="

# ---- 設定 ----
REPORT_DIR=~/ai-twin/workspace/reports/ebm
mkdir -p "$REPORT_DIR"
SLUG=$(echo "$QUERY" | sed 's/[^a-zA-Z0-9\u4e00-\u9fff]/-/g' | head -c 60)
REPORT_FILE="$REPORT_DIR/ebm-${TODAY}-${SLUG}.md"
TIMEOUT_SECS=300  # 5 分鐘

# ---- Step 1: PubMed 文獻搜尋 ----
log "Step 1: PubMed 搜尋..."

# 將中文 query URL encode
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")

# 搜尋 PubMed（取前 10 篇）
SEARCH_URL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${ENCODED_QUERY}&retmax=10&retmode=json&sort=relevance"
SEARCH_RESULT=$(curl -s --max-time 30 "$SEARCH_URL" 2>/dev/null || echo '{"esearchresult":{"idlist":[]}}')

# 提取 PMID 清單
PMIDS=$(echo "$SEARCH_RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    ids = data.get('esearchresult', {}).get('idlist', [])
    print(','.join(ids))
except:
    print('')
" 2>/dev/null)

if [ -z "$PMIDS" ]; then
    log "PubMed 搜尋無結果，嘗試英文翻譯查詢..."
    # 用 claude 快速翻譯 query 為英文 MeSH terms
    ENGLISH_QUERY=$(run_with_timeout 30 claude -p "Translate the following clinical question to English PubMed search terms (MeSH preferred). Output ONLY the search terms, nothing else: $QUERY" 2>/dev/null || echo "$QUERY")
    ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$ENGLISH_QUERY'''))")
    SEARCH_URL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${ENCODED_QUERY}&retmax=10&retmode=json&sort=relevance"
    SEARCH_RESULT=$(curl -s --max-time 30 "$SEARCH_URL" 2>/dev/null || echo '{"esearchresult":{"idlist":[]}}')
    PMIDS=$(echo "$SEARCH_RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    ids = data.get('esearchresult', {}).get('idlist', [])
    print(','.join(ids))
except:
    print('')
" 2>/dev/null)
fi

PMID_COUNT=$(echo "$PMIDS" | tr ',' '\n' | grep -c '[0-9]' || true)
log "找到 $PMID_COUNT 篇文獻：$PMIDS"

# ---- Step 2: 取得文獻摘要 ----
ABSTRACTS=""
if [ -n "$PMIDS" ] && [ "$PMID_COUNT" -gt 0 ]; then
    log "Step 2: 取得文獻摘要..."
    FETCH_URL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${PMIDS}&retmode=xml"
    RAW_XML=$(curl -s --max-time 60 "$FETCH_URL" 2>/dev/null || echo "")

    if [ -n "$RAW_XML" ]; then
        # 用 python 解析 XML 提取標題+摘要
        ABSTRACTS=$(echo "$RAW_XML" | python3 -c "
import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse(sys.stdin)
    root = tree.getroot()
    articles = root.findall('.//PubmedArticle')
    for i, art in enumerate(articles[:10], 1):
        # PMID
        pmid_el = art.find('.//PMID')
        pmid = pmid_el.text if pmid_el is not None else 'N/A'
        # Title
        title_el = art.find('.//ArticleTitle')
        title = title_el.text if title_el is not None else 'N/A'
        # Abstract
        abs_parts = art.findall('.//AbstractText')
        abstract = ' '.join(a.text or '' for a in abs_parts) if abs_parts else 'No abstract available'
        # Year
        year_el = art.find('.//PubDate/Year')
        year = year_el.text if year_el is not None else ''
        # Journal
        journal_el = art.find('.//Journal/Title')
        journal = journal_el.text if journal_el is not None else ''

        print(f'[{i}] PMID: {pmid} ({year})')
        print(f'    Title: {title}')
        print(f'    Journal: {journal}')
        print(f'    Abstract: {abstract[:500]}')
        print()
except Exception as e:
    print(f'XML parsing error: {e}', file=sys.stderr)
" 2>/dev/null)
    fi
fi

log "摘要解析完成（$(echo "$ABSTRACTS" | wc -l | tr -d ' ') 行）"

# ---- Step 3: Claude 分析 → EBM 報告 ----
log "Step 3: Claude 生成 EBM 報告..."

PROMPT=$(cat <<PROMPT_EOF
你是一位實證醫學（EBM）專家。請根據以下臨床問題和 PubMed 文獻，產出一份結構化的 EBM 報告。

## 臨床問題
$QUERY

## PubMed 文獻摘要
$ABSTRACTS

## 輸出要求
請用繁體中文撰寫，格式如下：

# EBM 報告：$QUERY
> 產生日期：$TODAY | 文獻數：$PMID_COUNT 篇

## 1. PICO 框架
- **P (Patient/Problem)**：目標族群與臨床情境
- **I (Intervention)**：建議的介入/治療方式
- **C (Comparison)**：對照組/替代方案
- **O (Outcome)**：預期結果與評估指標

## 2. 證據摘要
逐篇列出關鍵文獻發現（標注 PMID、年份、研究類型、主要結論）

## 3. 證據等級評估
- 使用 Oxford CEBM 分級（Level 1-5）
- 說明整體證據品質

## 4. 臨床建議
- 基於證據的具體建議
- 適用情境與限制
- 需注意的風險/副作用

## 5. 實務應用（給 PGY 醫師）
- 在台灣醫療環境的實務考量
- 常見 pitfall
- 何時需要會診專科

## 6. 參考文獻
列出所有引用文獻（APA 格式，附 PMID 連結）

注意：
- 如果文獻不足以回答問題，明確指出證據缺口
- 區分強推薦與弱推薦
- 標注是否有台灣本土指引（如衛福部/醫學會 guideline）
PROMPT_EOF
)

REPORT_CONTENT=$(run_with_timeout "$TIMEOUT_SECS" claude -p "$PROMPT" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$REPORT_CONTENT" ]; then
    log "ERROR: Claude 生成報告失敗"
    send_telegram "❌ EBM 報告生成失敗：$QUERY"
    exit 1
fi

# ---- Step 4: 存檔 ----
echo "$REPORT_CONTENT" > "$REPORT_FILE"
log "報告已存檔：$REPORT_FILE"

# ---- Step 5: Telegram 通知 ----
PREVIEW=$(echo "$REPORT_CONTENT" | head -5)
send_telegram "📋 EBM 報告完成
題目：$QUERY
文獻：$PMID_COUNT 篇
檔案：ebm-${TODAY}-${SLUG}.md

$PREVIEW"

log "=== EBM Report 完成 ==="
echo "✅ EBM 報告已存檔：$REPORT_FILE"
