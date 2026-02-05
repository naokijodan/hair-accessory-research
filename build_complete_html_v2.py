#!/usr/bin/env python3
"""髪飾り市場分析HTML完全版生成スクリプト - 時計分析HTMLと完全に同等の構造"""

import pandas as pd
import json
from collections import defaultdict
import re
from datetime import datetime
import numpy as np

# 設定
SHIPPING_JPY = 3000
EXCHANGE_RATE = 155
FEE_RATE = 0.20

# CSVファイル読み込み
df = pd.read_csv('/Users/naokijodan/Desktop/髪飾り市場データ_sheet8_2026-02-05.csv')

print(f"=== データ読み込み完了 ===")
print(f"総件数: {len(df)}")

# 販売数を数値に変換
df['販売数'] = pd.to_numeric(df['販売数'], errors='coerce').fillna(1).astype(int)

# 売上計算
df['売上'] = df['価格'] * df['販売数']

# 総販売数・総売上
total_sales = int(df['販売数'].sum())
total_revenue = float(df['売上'].sum())

# 期間
period_start = df['販売日'].min()
period_end = df['販売日'].max()

# アイテムタイプ分類
def extract_item_type(title):
    title_upper = str(title).upper()
    if 'TIARA' in title_upper:
        return 'Tiara'
    if 'HEADBAND' in title_upper or 'HAIR BAND' in title_upper or 'HAIRBAND' in title_upper:
        return 'Headband'
    if 'BARRETTE' in title_upper or 'VALLETTA' in title_upper:
        return 'Barrette'
    if 'CLIP' in title_upper or 'HAIRPIN' in title_upper or 'HAIR PIN' in title_upper or 'PIN' in title_upper:
        return 'Hair Clip'
    if 'SCRUNCHIE' in title_upper or 'シュシュ' in title_upper:
        return 'Scrunchie'
    if 'KANZASHI' in title_upper or 'KUSHI' in title_upper or '簪' in title_upper:
        return 'Kanzashi'
    if 'COMB' in title_upper:
        return 'Comb'
    if 'RIBBON' in title_upper:
        return 'Ribbon'
    return 'Other'

df['アイテムタイプ'] = df['タイトル'].apply(extract_item_type)

# ブランドカテゴリ分類
HIGH_BRANDS = ['CHANEL', 'DIOR', 'LOUIS VUITTON', 'GUCCI', 'HERMES', 'PRADA', 'FENDI', 'CELINE']
DESIGNER_BRANDS = ['Vivienne Westwood', 'Salvatore Ferragamo', 'Miu Miu', 'DOLCE & GABBANA',
                   'BALENCIAGA', 'BOTTEGA VENETA', 'LOEWE', 'Anya Hindmarch', 'LORO PIANA',
                   'Alexandre de Paris', 'colette malouf', 'adidas', 'H&M', 'BURBERRY']
CHARACTER_BRANDS = ['SANRIO', 'Disney', 'Pokemon', 'miffy']

def categorize_brand(brand):
    if pd.isna(brand) or brand == '(不明)':
        return 'ノーブランド'
    brand_upper = str(brand).upper()
    for hb in HIGH_BRANDS:
        if hb.upper() in brand_upper:
            return 'ハイブランド'
    for db in DESIGNER_BRANDS:
        if db.upper() in brand_upper:
            return 'デザイナー'
    for cb in CHARACTER_BRANDS:
        if cb.upper() in brand_upper:
            return 'キャラクター'
    return 'その他'

df['ブランドカテゴリ'] = df['ブランド'].apply(categorize_brand)

# まとめ売り判定
def is_bulk(title):
    bulk_keywords = ['LOT', 'BULK', 'SET OF', 'BUNDLE', 'X2', 'X3', '2PCS', '3PCS', '4PCS', '5PCS', '6PCS',
                     'PAIR', 'COLLECTION', '複数', 'まとめ', 'セット', 'SET', 'PCS', 'PACK']
    title_upper = str(title).upper()
    for kw in bulk_keywords:
        if kw in title_upper:
            return True
    if re.search(r'\d+\s*(PCS|PIECES|PACK|点|個|本)', title_upper):
        return True
    return False

df['まとめ売り'] = df['タイトル'].apply(is_bulk)

# ノベルティ判定
def is_novelty(title):
    novelty_keywords = ['NOVELTY', 'GWP', 'LIMITED', 'NOT FOR SALE', '非売品', 'RARE', 'VIP']
    title_upper = str(title).upper()
    for kw in novelty_keywords:
        if kw in title_upper:
            return True
    return False

df['ノベルティ'] = df['タイトル'].apply(is_novelty)

# CITES規制リスク判定
def is_cites_risk(title):
    risk_keywords = ['TORTOISE', 'BEKKO', 'IVORY', 'べっ甲', '象牙', '鼈甲']
    safe_keywords = ['RESIN', 'PLASTIC', 'FAUX', 'CELLULOID', '樹脂']
    title_upper = str(title).upper()
    for kw in safe_keywords:
        if kw in title_upper:
            return False
    for kw in risk_keywords:
        if kw in title_upper:
            return True
    return False

df['CITES_RISK'] = df['タイトル'].apply(is_cites_risk)

# 箱あり判定
def has_box(title):
    title_upper = str(title).upper()
    return 'W/BOX' in title_upper or 'WITH BOX' in title_upper or 'BOX' in title_upper

df['箱あり'] = df['タイトル'].apply(has_box)

# 仕入れ上限計算
df['仕入れ上限'] = df['価格'] * EXCHANGE_RATE * (1 - FEE_RATE) - SHIPPING_JPY

# ブランド別統計
def get_brand_stats(brand_df):
    if len(brand_df) == 0:
        return {}
    sales = int(brand_df['販売数'].sum())
    prices = brand_df['価格']
    return {
        'count': len(brand_df),
        'sales': sales,
        'revenue': float(brand_df['売上'].sum()),
        'avg_price': float(prices.mean()),
        'median_price': float(prices.median()),
        'min_price': float(prices.min()),
        'max_price': float(prices.max()),
        'cv': float(prices.std() / prices.mean()) if prices.mean() > 0 else 0,
        'purchase_limit': float(brand_df['仕入れ上限'].median())
    }

# トップブランドリスト（販売数順）
brand_sales = df.groupby('ブランド')['販売数'].sum().sort_values(ascending=False)
top_brands = [b for b in brand_sales.head(10).index if b != '(不明)']

print(f"\n=== トップ10ブランド ===")
for b in top_brands:
    print(f"  - {b}")

# ノベルティプレミアム計算（JDMプレミアムに相当）
def calc_novelty_premium(brand_df):
    novelty = brand_df[brand_df['ノベルティ'] == True]
    regular = brand_df[brand_df['ノベルティ'] == False]
    if len(novelty) < 2 or len(regular) < 2:
        return 0.0
    novelty_median = novelty['価格'].median()
    regular_median = regular['価格'].median()
    if regular_median > 0:
        return float((novelty_median - regular_median) / regular_median * 100)
    return 0.0

# 箱ありプレミアム計算
def calc_box_premium(brand_df):
    with_box = brand_df[brand_df['箱あり'] == True]
    without_box = brand_df[brand_df['箱あり'] == False]
    if len(with_box) < 2 or len(without_box) < 2:
        return 0.0
    box_median = with_box['価格'].median()
    no_box_median = without_box['価格'].median()
    if no_box_median > 0:
        return float((box_median - no_box_median) / no_box_median * 100)
    return 0.0

# 安定度評価
def get_stability(cv):
    if cv <= 0.3:
        return '★★★'
    elif cv <= 0.5:
        return '★★☆'
    elif cv <= 0.7:
        return '★☆☆'
    else:
        return '☆☆☆'

# 価格帯分布（50ドル刻み）
def get_price_distribution_50(prices):
    bins = list(range(0, 1001, 50)) + [float('inf')]
    labels = [f'${i}-{i+49}' for i in range(0, 1000, 50)] + ['$1000+']
    distribution = pd.cut(prices, bins=bins, labels=labels).value_counts().sort_index()
    return {str(k): int(v) for k, v in distribution.items()}

# HTML生成開始
html_parts = []

# CSSスタイル
css = '''
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-card: #ffffff;
    --text-primary: #333333;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --accent: #e91e63;
    --positive: #4CAF50;
    --negative: #f44336;
}
[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-card: #0f3460;
    --text-primary: #eee;
    --text-secondary: #aaa;
    --border-color: #3a3a5c;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}
.header {
    background: linear-gradient(135deg, #e91e63 0%, #9c27b0 100%);
    color: white;
    padding: 30px 20px;
    text-align: center;
    position: relative;
}
.header h1 { font-size: 2em; margin-bottom: 10px; }
.header p { opacity: 0.9; font-size: 0.9em; }
.theme-toggle {
    position: absolute;
    top: 20px;
    right: 20px;
}
.theme-toggle button {
    padding: 10px 20px;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    border-radius: 20px;
    cursor: pointer;
}
.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    padding: 15px 20px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    align-items: center;
}
.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}
.control-group label { font-size: 0.85em; color: var(--text-secondary); }
.control-group input {
    width: 80px;
    padding: 6px 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-card);
    color: var(--text-primary);
}
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85em;
    transition: all 0.2s;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { opacity: 0.9; }
.tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    padding: 10px 20px;
    background: var(--bg-secondary);
    border-bottom: 2px solid var(--border-color);
    overflow-x: auto;
}
.tab {
    padding: 10px 16px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 4px;
    font-size: 0.85em;
    transition: all 0.2s;
    white-space: nowrap;
}
.tab:hover { background: var(--bg-card); }
.tab.active { background: var(--accent); color: white; }
.tab-content {
    display: none;
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
}
.tab-content.active { display: block; }
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border-left: 4px solid var(--accent);
}
.stat-card .icon { font-size: 1.5em; margin-bottom: 5px; }
.stat-card .value {
    font-size: 2em;
    font-weight: bold;
    color: var(--accent);
    margin: 10px 0;
}
.stat-card .label { font-size: 0.85em; color: var(--text-secondary); }
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}
.table-container {
    overflow-x: auto;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin-bottom: 20px;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
}
th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
th {
    background: var(--bg-secondary);
    font-weight: 600;
    position: sticky;
    top: 0;
}
tr:hover { background: rgba(233, 30, 99, 0.05); }
.link-btn {
    display: inline-block;
    padding: 4px 8px;
    margin: 2px;
    font-size: 0.75em;
    border-radius: 3px;
    text-decoration: none;
    color: white;
}
.link-ebay { background: #0064d2; }
.link-mercari { background: #ff0211; }
.highlight { color: var(--positive); font-weight: bold; }
.section-title {
    font-size: 1.5em;
    color: var(--accent);
    margin: 30px 0 15px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border-color);
}
.risk-low { background: #4CAF50; color: white; padding: 4px 8px; border-radius: 3px; font-size: 0.8em; }
.risk-mid { background: #FF9800; color: white; padding: 4px 8px; border-radius: 3px; font-size: 0.8em; }
.risk-high { background: #f44336; color: white; padding: 4px 8px; border-radius: 3px; font-size: 0.8em; }
.mode-selector {
    margin-bottom: 20px;
    padding: 15px;
    background: var(--bg-secondary);
    border-radius: 8px;
}
.mode-selector label {
    margin-right: 20px;
    cursor: pointer;
}
.insight-box {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
    border-left: 4px solid var(--positive);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.insight-box h3 { color: var(--positive); margin-bottom: 10px; }
.insight-box ul { list-style: none; padding: 0; }
.insight-box li { padding: 8px 0; border-bottom: 1px dashed var(--border-color); }
.cites-warning {
    background: linear-gradient(135deg, #fff3e0, #ffe0b2);
    border-left: 5px solid #ff9800;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.cites-warning h3 { color: #e65100; margin-bottom: 10px; }
.brand-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin: 20px 0;
}
.brand-chart-container {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.brand-chart-container h4 {
    margin-bottom: 10px;
    font-size: 16px;
}
@media (max-width: 768px) {
    .chart-grid { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .brand-grid { grid-template-columns: 1fr; }
}

/* CHANEL固有のスタイル */
#CHANEL .stat-card {
    background: linear-gradient(135deg, #00000015 0%, #00000005 100%);
    border-top: 3px solid #000000;
}
.chanel-accent { color: #000000; font-weight: bold; }

/* LOUIS VUITTON固有のスタイル */
#LOUIS_VUITTON .stat-card {
    background: linear-gradient(135deg, #8B451315 0%, #8B451305 100%);
    border-top: 3px solid #8B4513;
}
.lv-accent { color: #8B4513; font-weight: bold; }

/* DIOR固有のスタイル */
#DIOR .stat-card {
    background: linear-gradient(135deg, #00000015 0%, #00000005 100%);
    border-top: 3px solid #000000;
}
.dior-accent { color: #6c757d; font-weight: bold; }

/* Vivienne Westwood固有のスタイル */
#Vivienne_Westwood .stat-card {
    background: linear-gradient(135deg, #6B0B5A15 0%, #6B0B5A05 100%);
    border-top: 3px solid #6B0B5A;
}
.vw-accent { color: #6B0B5A; font-weight: bold; }

/* GUCCI固有のスタイル */
#GUCCI .stat-card {
    background: linear-gradient(135deg, #00634115 0%, #00634105 100%);
    border-top: 3px solid #006341;
}
.gucci-accent { color: #006341; font-weight: bold; }

/* Salvatore Ferragamo固有のスタイル */
#Salvatore_Ferragamo .stat-card {
    background: linear-gradient(135deg, #96020015 0%, #96020005 100%);
    border-top: 3px solid #960200;
}
.ferragamo-accent { color: #960200; font-weight: bold; }
'''

# HTML開始
html_parts.append(f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>髪飾り市場分析（完全版）</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
{css}
    </style>
</head>
<body>
    <div class="header">
        <div class="theme-toggle">
            <button onclick="toggleTheme()" id="themeBtn">🌙 ダークモード</button>
        </div>
        <h1>🎀 髪飾り市場分析（完全版）</h1>
        <p>データ期間: {period_start} ~ {period_end} | 生成: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 総件数: {len(df)}件</p>
    </div>

    <div class="controls">
        <div class="control-group">
            <label>💱 為替:</label>
            <input type="number" id="exchangeRate" value="{EXCHANGE_RATE}" step="0.1">
            <button class="btn btn-secondary" onclick="updateExchangeRate()" style="margin-left: 10px;">🔄 最新レート取得</button>
        </div>
        <div class="control-group">
            <label>📦 送料(円):</label>
            <input type="number" id="shippingCost" value="{SHIPPING_JPY}" step="100">
        </div>
        <div class="control-group">
            <label>💰 手数料:</label>
            <input type="number" id="feeRate" value="{int(FEE_RATE * 100)}" step="1">%
        </div>
        <button class="btn btn-primary" onclick="recalculate()">🔄 再計算</button>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">📊 全体分析</button>
        <button class="tab" onclick="showTab('brands')">🏷️ ブランド一覧</button>
        <button class="tab" onclick="showTab('headband')">👑 Headband</button>
        <button class="tab" onclick="showTab('barrette')">✨ Barrette</button>
        <button class="tab" onclick="showTab('hairclip')">📎 Hair Clip</button>
        <button class="tab" onclick="showTab('tiara')">👸 Tiara</button>
        <button class="tab" onclick="showTab('scrunchie')">🎀 Scrunchie</button>
        <button class="tab" onclick="showTab('kanzashi')">🌸 簪</button>
        <button class="tab" onclick="showTab('novelty')">🎁 ノベルティ</button>
        <button class="tab" onclick="showTab('bundle')">📦 まとめ売り</button>
        <button class="tab" onclick="showTab('recommend')">⭐ おすすめ出品順序</button>
        <button class="tab" onclick="showTab('CHANEL')">CHANEL</button>
        <button class="tab" onclick="showTab('LOUIS_VUITTON')">LOUIS VUITTON</button>
        <button class="tab" onclick="showTab('DIOR')">DIOR</button>
        <button class="tab" onclick="showTab('Salvatore_Ferragamo')">Salvatore Ferragamo</button>
        <button class="tab" onclick="showTab('Vivienne_Westwood')">Vivienne Westwood</button>
        <button class="tab" onclick="showTab('GUCCI')">GUCCI</button>
    </div>
''')

# 全体分析タブ
overall_stats = get_brand_stats(df)
cites_count = int(df['CITES_RISK'].sum())

# アイテムタイプ別統計
item_type_stats = {}
for item_type in df['アイテムタイプ'].unique():
    type_df = df[df['アイテムタイプ'] == item_type]
    item_type_stats[item_type] = {
        'sales': int(type_df['販売数'].sum()),
        'revenue': float(type_df['売上'].sum()),
        'median': float(type_df['価格'].median())
    }

# ブランドカテゴリ別統計
brand_cat_stats = {}
for cat in df['ブランドカテゴリ'].unique():
    cat_df = df[df['ブランドカテゴリ'] == cat]
    brand_cat_stats[cat] = {
        'sales': int(cat_df['販売数'].sum()),
        'revenue': float(cat_df['売上'].sum())
    }

html_parts.append(f'''
    <!-- 全体分析タブ -->
    <div id="overview" class="tab-content active">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">総販売数</div>
                <div class="value">{total_sales:,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">総売上</div>
                <div class="value">${total_revenue:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">平均価格</div>
                <div class="value">${overall_stats["avg_price"]:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${overall_stats["median_price"]:.2f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>💡 市場インサイト</h3>
            <ul>
                <li>🔝 最大カテゴリ: ハイブランド ({brand_cat_stats.get("ハイブランド", {}).get("sales", 0):,}件) とノーブランド ({brand_cat_stats.get("ノーブランド", {}).get("sales", 0):,}件) で市場の大半を占める</li>
                <li>💎 高価格帯: Vivienne Westwood Tiara ($211中央値) が市場を牽引</li>
                <li>⚡ 回転率重視: Headband・Hair Clipは低価格で回転が早い（エントリー層向け）</li>
                <li>🎁 ノベルティ市場: {int(df['ノベルティ'].sum())}件の取引あり（CHANELが最多）</li>
            </ul>
        </div>
''')

# CITESリスク警告
if cites_count > 0:
    html_parts.append(f'''
        <div class="cites-warning">
            <h3>⚠️ CITES規制リスク品検出（{cites_count}件）</h3>
            <p>べっ甲・象牙などのワシントン条約規制対象の可能性がある商品が検出されました。輸出入には許可証が必要です。</p>
        </div>
''')

# 全体分析グラフ用データ
item_type_labels = list(item_type_stats.keys())
item_type_sales = [item_type_stats[k]['sales'] for k in item_type_labels]

brand_cat_labels = list(brand_cat_stats.keys())
brand_cat_sales = [brand_cat_stats[k]['sales'] for k in brand_cat_labels]

# ブランド別Top20
brand_stats_list = []
for brand in df['ブランド'].unique():
    brand_df = df[df['ブランド'] == brand]
    stats = get_brand_stats(brand_df)
    stats['brand'] = brand
    brand_stats_list.append(stats)
brand_stats_list.sort(key=lambda x: x['sales'], reverse=True)
top20_brands = brand_stats_list[:20]

html_parts.append(f'''
        <h2 class="section-title">📊 カテゴリ別分析</h2>
        <div class="chart-grid">
            <div class="chart-container"><div id="itemTypeBarChart"></div></div>
            <div class="chart-container"><div id="brandCatPieChart"></div></div>
        </div>

        <h2 class="section-title">🏷️ ブランド別分析（Top20）</h2>
        <div class="chart-grid">
            <div class="chart-container"><div id="brandBarChart"></div></div>
            <div class="chart-container"><div id="brandPieChart"></div></div>
        </div>

        <h2 class="section-title">💰 価格帯分布（50ドル刻み）</h2>
        <div class="chart-container"><div id="priceDistChart"></div></div>

        <h2 class="section-title">🏷️ ブランド別詳細（Top20）</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>最低価格</th>
                        <th>最高価格</th>
                        <th>中央値($)</th>
                        <th>中央値(¥)</th>
                        <th>仕入上限(¥)</th>
                        <th>CV値</th>
                        <th>安定度</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for stats in top20_brands:
    brand = stats['brand']
    brand_display = '不明' if brand == '(不明)' else brand
    median_jpy = int(stats['median_price'] * EXCHANGE_RATE)
    purchase_limit = int(stats['purchase_limit'])
    stability = get_stability(stats['cv'])
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand.replace(' ', '+')}+Hair+Accessory&LH_Sold=1"
    mercari_url = f"https://jp.mercari.com/search?keyword={brand}%20髪飾り&status=on_sale"

    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand_display}</strong></td>
                        <td>{stats["sales"]}</td>
                        <td>${stats["min_price"]:.2f}</td>
                        <td>${stats["max_price"]:.2f}</td>
                        <td>${stats["median_price"]:.2f}</td>
                        <td>¥{median_jpy:,}</td>
                        <td class="highlight">¥{purchase_limit:,}</td>
                        <td>{stats["cv"]:.3f}</td>
                        <td>{stability}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ブランド一覧タブ
html_parts.append('''
    <!-- ブランド一覧タブ -->
    <div id="brands" class="tab-content">
        <h2 class="section-title">🏷️ ブランド一覧</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>カテゴリ</th>
                        <th>販売数</th>
                        <th>売上</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV値</th>
                        <th>安定度</th>
                    </tr>
                </thead>
                <tbody>
''')

for stats in brand_stats_list[:50]:
    brand = stats['brand']
    brand_display = '不明' if brand == '(不明)' else brand
    brand_df = df[df['ブランド'] == brand]
    category = brand_df['ブランドカテゴリ'].iloc[0] if len(brand_df) > 0 else '不明'
    stability = get_stability(stats['cv'])

    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand_display}</strong></td>
                        <td>{category}</td>
                        <td>{stats["sales"]}</td>
                        <td>${stats["revenue"]:,.2f}</td>
                        <td>${stats["median_price"]:.2f}</td>
                        <td>¥{int(stats["purchase_limit"]):,}</td>
                        <td>{stats["cv"]:.3f}</td>
                        <td>{stability}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# 個別ブランドタブ生成関数
def generate_brand_tab(brand_name, tab_id, accent_class):
    brand_df = df[df['ブランド'] == brand_name]
    if len(brand_df) == 0:
        return ''

    stats = get_brand_stats(brand_df)
    novelty_premium = calc_novelty_premium(brand_df)
    box_premium = calc_box_premium(brand_df)
    novelty_count = int(brand_df['ノベルティ'].sum())
    bulk_count = int(brand_df['まとめ売り'].sum())

    # アイテムタイプ別統計
    item_stats = []
    for item_type in brand_df['アイテムタイプ'].unique():
        type_df = brand_df[brand_df['アイテムタイプ'] == item_type]
        if len(type_df) > 0:
            type_stats = get_brand_stats(type_df)
            type_stats['type'] = item_type
            item_stats.append(type_stats)
    item_stats.sort(key=lambda x: x['sales'], reverse=True)

    # 人気商品Top15
    popular_items = brand_df.nlargest(15, '販売数')[['タイトル', '価格', '販売数', '仕入れ上限']].to_dict('records')

    tab_html = f'''
    <!-- {brand_name}タブ -->
    <div id="{tab_id}" class="tab-content">
        <h2 class="section-title {accent_class}">📊 {brand_name} 詳細分析</h2>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">総販売数</div>
                <div class="value">{stats["sales"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">中央値</div>
                <div class="value">${stats["median_price"]:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">CV（変動係数）</div>
                <div class="value">{stats["cv"]:.3f}</div>
            </div>
            <div class="stat-card">
                <div class="label">ノベルティプレミアム</div>
                <div class="value {accent_class}">{novelty_premium:+.1f}%</div>
            </div>
        </div>

        <div class="insight-box" style="border-left: 5px solid #ff6b35;">
            <h3 class="{accent_class}">🎯 仕入れ戦略（実践ガイド）</h3>
            <div style="display: grid; gap: 15px;">
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #1976d2;">
                    <h4 style="color: #1976d2; margin-bottom: 10px;">✅ 狙い目条件</h4>
                    <ul style="margin-left: 20px;">
                        <li><strong class="{accent_class}">箱・保証書付き</strong>（<span class="{accent_class}">{box_premium:+.1f}%</span>プレミアム）</li>
                        <li>型番・モデル名が<strong>明確に記載</strong>されている商品</li>
                        <li><strong class="{accent_class}">ノベルティ・限定品</strong>（<span class="{accent_class}">{novelty_premium:+.1f}%</span>プレミアム）</li>
                        <li>人気アイテムタイプ：<strong>{", ".join([s["type"] for s in item_stats[:3]])}</strong></li>
                    </ul>
                </div>
                <div style="background: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff6b35;">
                    <h4 style="color: #ff6b35; margin-bottom: 10px;">⚠️ 避けるべき条件</h4>
                    <ul style="margin-left: 20px;">
                        <li>まとめ売り・セット品（単価が不明確）</li>
                        <li>状態不明・説明が曖昧な商品</li>
                        <li>偽物リスクの高い格安品</li>
                    </ul>
                </div>
                <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; border-left: 4px solid #7b1fa2;">
                    <h4 style="color: #7b1fa2; margin-bottom: 10px;">💰 仕入れ価格目安</h4>
                    <p style="margin: 0;"><strong>通常商品:</strong> ¥{int(stats["purchase_limit"]):,}以下</p>
                    <p style="margin: 5px 0 0 0;"><strong class="{accent_class}">箱付き・美品:</strong> ${stats["median_price"]:.0f}前後が上限（中央値基準）</p>
                </div>
            </div>
        </div>

        <h3 class="section-title {accent_class}">📊 市場分析グラフ</h3>
        <div class="brand-grid">
            <div class="brand-chart-container">
                <h4 class="{accent_class}">価格帯別分析（50ドル刻み）</h4>
                <div id="{tab_id}_price_chart" style="height: 350px;"></div>
            </div>
            <div class="brand-chart-container">
                <h4 class="{accent_class}">アイテムタイプ別分布</h4>
                <div id="{tab_id}_item_chart" style="height: 350px;"></div>
            </div>
        </div>

        <h3 class="section-title {accent_class}">🎀 アイテムタイプ別詳細分析</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>アイテムタイプ</th>
                        <th>販売数</th>
                        <th class="{accent_class}">比率</th>
                        <th>中央値</th>
                        <th class="{accent_class}">仕入上限(¥)</th>
                        <th>CV値</th>
                        <th>安定度</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
'''

    total_brand_sales = stats['sales']
    for type_stats in item_stats:
        ratio = type_stats['sales'] / total_brand_sales * 100 if total_brand_sales > 0 else 0
        stability = get_stability(type_stats['cv'])
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand_name.replace(' ', '+')}+{type_stats['type'].replace(' ', '+')}+Hair+Accessory&LH_Sold=1"
        mercari_url = f"https://jp.mercari.com/search?keyword={brand_name}%20{type_stats['type']}%20髪飾り&status=on_sale"

        tab_html += f'''
                    <tr>
                        <td><strong>{type_stats["type"]}</strong></td>
                        <td>{type_stats["sales"]}</td>
                        <td class="{accent_class}">{ratio:.1f}%</td>
                        <td>${type_stats["median_price"]:.2f}</td>
                        <td class="highlight {accent_class}">¥{int(type_stats["purchase_limit"]):,}</td>
                        <td>{type_stats["cv"]:.3f}</td>
                        <td>{stability}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
'''

    tab_html += f'''
                </tbody>
            </table>
        </div>

        <h3 class="section-title {accent_class}">💡 {brand_name}の特徴</h3>
        <div class="stats-grid" style="margin-bottom: 20px;">
            <div class="stat-card">
                <div class="label">🎁 ノベルティ品</div>
                <div class="value {accent_class}">{novelty_count}件</div>
            </div>
            <div class="stat-card">
                <div class="label">📦 まとめ売り</div>
                <div class="value">{bulk_count}件</div>
            </div>
            <div class="stat-card">
                <div class="label">💰 総売上</div>
                <div class="value">${stats["revenue"]:,.2f}</div>
            </div>
        </div>

        <h3 class="section-title {accent_class}">📌 人気商品（実データより）Top15</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>商品タイトル</th>
                        <th>販売数</th>
                        <th>価格</th>
                        <th class="{accent_class}">仕入上限(¥)</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
'''

    for i, item in enumerate(popular_items, 1):
        title = str(item['タイトル'])[:80] + '...' if len(str(item['タイトル'])) > 80 else str(item['タイトル'])
        search_term = str(item['タイトル'])[:50].replace(' ', '+')
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&LH_Sold=1"
        mercari_url = f"https://jp.mercari.com/search?keyword={str(item['タイトル'])[:30]}&status=on_sale"

        tab_html += f'''
                    <tr>
                        <td><strong class="{accent_class}">{i}</strong></td>
                        <td class="model-sample">{title}</td>
                        <td>{item["販売数"]}</td>
                        <td>${item["価格"]:.2f}</td>
                        <td class="highlight {accent_class}">¥{int(item["仕入れ上限"]):,}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
'''

    tab_html += '''
                </tbody>
            </table>
        </div>
    </div>
'''
    return tab_html

# 各ブランドタブを生成
brand_tabs = [
    ('CHANEL', 'CHANEL', 'chanel-accent'),
    ('LOUIS VUITTON', 'LOUIS_VUITTON', 'lv-accent'),
    ('DIOR', 'DIOR', 'dior-accent'),
    ('Salvatore Ferragamo', 'Salvatore_Ferragamo', 'ferragamo-accent'),
    ('Vivienne Westwood', 'Vivienne_Westwood', 'vw-accent'),
    ('GUCCI', 'GUCCI', 'gucci-accent'),
]

for brand_name, tab_id, accent_class in brand_tabs:
    html_parts.append(generate_brand_tab(brand_name, tab_id, accent_class))

# アイテムタイプ別タブ生成関数
def generate_item_type_tab(item_type, tab_id):
    type_df = df[df['アイテムタイプ'] == item_type]
    if len(type_df) == 0:
        return ''

    stats = get_brand_stats(type_df)

    # ブランド別統計
    brand_stats_in_type = []
    for brand in type_df['ブランド'].unique():
        brand_df = type_df[type_df['ブランド'] == brand]
        if len(brand_df) > 0:
            b_stats = get_brand_stats(brand_df)
            b_stats['brand'] = brand
            brand_stats_in_type.append(b_stats)
    brand_stats_in_type.sort(key=lambda x: x['sales'], reverse=True)

    tab_html = f'''
    <!-- {item_type}タブ -->
    <div id="{tab_id}" class="tab-content">
        <h2 class="section-title">📊 {item_type} 市場分析</h2>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">総販売数</div>
                <div class="value">{stats["sales"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">中央値</div>
                <div class="value">${stats["median_price"]:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">CV（変動係数）</div>
                <div class="value">{stats["cv"]:.3f}</div>
            </div>
            <div class="stat-card">
                <div class="label">仕入上限</div>
                <div class="value">¥{int(stats["purchase_limit"]):,}</div>
            </div>
        </div>

        <h3 class="section-title">🏷️ ブランド別詳細分析（Top20）</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>比率</th>
                        <th>中央値</th>
                        <th>仕入上限(¥)</th>
                        <th>CV値</th>
                        <th>安定度</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
'''

    total_type_sales = stats['sales']
    for b_stats in brand_stats_in_type[:20]:
        brand = b_stats['brand']
        brand_display = '不明' if brand == '(不明)' else brand
        ratio = b_stats['sales'] / total_type_sales * 100 if total_type_sales > 0 else 0
        stability = get_stability(b_stats['cv'])
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand.replace(' ', '+')}+{item_type.replace(' ', '+')}+Hair+Accessory&LH_Sold=1"
        mercari_url = f"https://jp.mercari.com/search?keyword={brand}%20{item_type}%20髪飾り&status=on_sale"

        tab_html += f'''
                    <tr>
                        <td><strong>{brand_display}</strong></td>
                        <td>{b_stats["sales"]}</td>
                        <td>{ratio:.1f}%</td>
                        <td>${b_stats["median_price"]:.2f}</td>
                        <td class="highlight">¥{int(b_stats["purchase_limit"]):,}</td>
                        <td>{b_stats["cv"]:.3f}</td>
                        <td>{stability}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
'''

    tab_html += '''
                </tbody>
            </table>
        </div>
    </div>
'''
    return tab_html

# アイテムタイプ別タブを生成
item_type_tabs = [
    ('Headband', 'headband'),
    ('Barrette', 'barrette'),
    ('Hair Clip', 'hairclip'),
    ('Tiara', 'tiara'),
    ('Scrunchie', 'scrunchie'),
    ('Kanzashi', 'kanzashi'),
]

for item_type, tab_id in item_type_tabs:
    html_parts.append(generate_item_type_tab(item_type, tab_id))

# ノベルティタブ
novelty_df = df[df['ノベルティ'] == True]
novelty_stats = get_brand_stats(novelty_df) if len(novelty_df) > 0 else {}

html_parts.append(f'''
    <!-- ノベルティタブ -->
    <div id="novelty" class="tab-content">
        <h2 class="section-title">🎁 ノベルティ品分析</h2>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">総販売数</div>
                <div class="value">{novelty_stats.get("sales", 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="label">中央値</div>
                <div class="value">${novelty_stats.get("median_price", 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">総売上</div>
                <div class="value">${novelty_stats.get("revenue", 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">仕入上限</div>
                <div class="value">¥{int(novelty_stats.get("purchase_limit", 0)):,}</div>
            </div>
        </div>

        <h3 class="section-title">🏷️ ブランド別ノベルティ分析</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限(¥)</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

# ノベルティのブランド別統計
novelty_brand_stats = []
for brand in novelty_df['ブランド'].unique():
    brand_df = novelty_df[novelty_df['ブランド'] == brand]
    if len(brand_df) > 0:
        b_stats = get_brand_stats(brand_df)
        b_stats['brand'] = brand
        novelty_brand_stats.append(b_stats)
novelty_brand_stats.sort(key=lambda x: x['sales'], reverse=True)

for b_stats in novelty_brand_stats[:20]:
    brand = b_stats['brand']
    brand_display = '不明' if brand == '(不明)' else brand
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand.replace(' ', '+')}+novelty+Hair+Accessory&LH_Sold=1"
    mercari_url = f"https://jp.mercari.com/search?keyword={brand}%20ノベルティ%20髪飾り&status=on_sale"

    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand_display}</strong></td>
                        <td>{b_stats["sales"]}</td>
                        <td>${b_stats["median_price"]:.2f}</td>
                        <td class="highlight">¥{int(b_stats["purchase_limit"]):,}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# まとめ売りタブ
bulk_df = df[df['まとめ売り'] == True]
bulk_stats = get_brand_stats(bulk_df) if len(bulk_df) > 0 else {}

html_parts.append(f'''
    <!-- まとめ売りタブ -->
    <div id="bundle" class="tab-content">
        <h2 class="section-title">📦 まとめ売り分析</h2>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">総販売数</div>
                <div class="value">{bulk_stats.get("sales", 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="label">中央値</div>
                <div class="value">${bulk_stats.get("median_price", 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">総売上</div>
                <div class="value">${bulk_stats.get("revenue", 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">仕入上限</div>
                <div class="value">¥{int(bulk_stats.get("purchase_limit", 0)):,}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>⚠️ まとめ売りの注意点</h3>
            <ul>
                <li>単品あたりの価格が不明確になりがち</li>
                <li>状態のバラつきがある可能性</li>
                <li>再販時は単品出品が基本</li>
            </ul>
        </div>
    </div>
''')

# おすすめ順序タブ
# 単品のみ（まとめ売り・CITESリスク品を除外）
safe_df = df[(df['まとめ売り'] == False) & (df['CITES_RISK'] == False)]

# ブランド×アイテムタイプ別集計
recommend_data = []
for (brand, item_type), group_df in safe_df.groupby(['ブランド', 'アイテムタイプ']):
    if len(group_df) >= 2:
        stats = get_brand_stats(group_df)
        stats['brand'] = brand
        stats['item_type'] = item_type
        recommend_data.append(stats)

# 回転重視スコア（CV <= 0.5、仕入上限 <= 30000、販売数 >= 3）
rotation_data = [d for d in recommend_data if d['cv'] <= 0.5 and d['purchase_limit'] <= 30000 and d['sales'] >= 3]
rotation_data.sort(key=lambda x: x['purchase_limit'] * x['sales'], reverse=True)

# 利益重視スコア（全商品）
profit_data = sorted(recommend_data, key=lambda x: x['purchase_limit'] * x['sales'], reverse=True)

html_parts.append(f'''
    <!-- おすすめ出品順序タブ -->
    <div id="recommend" class="tab-content">
        <h2 class="section-title">⭐ おすすめ出品順序</h2>

        <div class="mode-selector">
            <label>
                <input type="radio" name="recommend-mode" value="rotation" checked onchange="showRecommendMode('rotation')">
                🔄 回転重視（初心者向け）
            </label>
            <label>
                <input type="radio" name="recommend-mode" value="profit" onchange="showRecommendMode('profit')">
                💰 利益重視（経験者向け）
            </label>
        </div>

        <div id="rotation-mode">
            <div class="insight-box">
                <h3>🔄 回転重視モードの条件</h3>
                <ul>
                    <li>変動係数（CV）≤ 0.5（価格が安定）</li>
                    <li>仕入上限 ≤ ¥30,000（低資金でも仕入可能）</li>
                    <li>販売数 ≥ 3件（一定の需要）</li>
                </ul>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>ブランド</th>
                            <th>アイテムタイプ</th>
                            <th>販売数</th>
                            <th>中央値($)</th>
                            <th>仕入上限</th>
                            <th>安定度</th>
                            <th>スコア</th>
                        </tr>
                    </thead>
                    <tbody>
''')

for i, data in enumerate(rotation_data[:30], 1):
    stability = get_stability(data['cv'])
    score = int(data['purchase_limit'] * data['sales'])
    risk = '低' if data['cv'] <= 0.3 else ('中' if data['cv'] <= 0.5 else '高')

    html_parts.append(f'''
                        <tr>
                            <td><strong>{i}</strong></td>
                            <td>{data["brand"]}</td>
                            <td>{data["item_type"]}</td>
                            <td>{data["sales"]}</td>
                            <td>${data["median_price"]:.2f}</td>
                            <td>¥{int(data["purchase_limit"]):,}</td>
                            <td>{stability}</td>
                            <td>{score:,}</td>
                        </tr>
''')

html_parts.append('''
                    </tbody>
                </table>
            </div>
        </div>

        <div id="profit-mode" style="display: none;">
            <div class="insight-box">
                <h3>💰 利益重視モードの特徴</h3>
                <ul>
                    <li>スコア = 仕入上限 × 販売数</li>
                    <li>全商品が対象（フィルタなし）</li>
                    <li>高単価・高需要商品を優先</li>
                </ul>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>ブランド</th>
                            <th>アイテムタイプ</th>
                            <th>販売数</th>
                            <th>中央値($)</th>
                            <th>仕入上限</th>
                            <th>リスク</th>
                            <th>スコア</th>
                        </tr>
                    </thead>
                    <tbody>
''')

for i, data in enumerate(profit_data[:30], 1):
    score = int(data['purchase_limit'] * data['sales'])
    risk = '低' if data['cv'] <= 0.3 else ('中' if data['cv'] <= 0.5 else '高')

    html_parts.append(f'''
                        <tr>
                            <td><strong>{i}</strong></td>
                            <td>{data["brand"]}</td>
                            <td>{data["item_type"]}</td>
                            <td>{data["sales"]}</td>
                            <td>${data["median_price"]:.2f}</td>
                            <td>¥{int(data["purchase_limit"]):,}</td>
                            <td>{risk}</td>
                            <td>{score:,}</td>
                        </tr>
''')

html_parts.append('''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
''')

# JavaScript
# グラフデータの準備
price_dist = get_price_distribution_50(df['価格'])
price_dist_labels = list(price_dist.keys())
price_dist_values = list(price_dist.values())

brand_top10_labels = [b['brand'] for b in top20_brands[:10]]
brand_top10_sales = [b['sales'] for b in top20_brands[:10]]

# 各ブランドの価格分布データ
brand_price_dist = {}
brand_item_type_dist = {}
for brand_name, tab_id, _ in brand_tabs:
    brand_df = df[df['ブランド'] == brand_name]
    if len(brand_df) > 0:
        brand_price_dist[tab_id] = get_price_distribution_50(brand_df['価格'])
        item_dist = brand_df.groupby('アイテムタイプ')['販売数'].sum().to_dict()
        brand_item_type_dist[tab_id] = {str(k): int(v) for k, v in item_dist.items()}

html_parts.append(f'''
    <script>
    // Plotly設定
    const plotlyLayout = {{
        margin: {{ t: 40, b: 40, l: 60, r: 20 }},
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: {{ color: '#333' }}
    }};
    const plotlyConfig = {{ responsive: true, displayModeBar: false }};

    // タブ切り替え
    function showTab(tabId) {{
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        document.querySelector(`[onclick="showTab('${{tabId}}')"]`).classList.add('active');
    }}

    // おすすめモード切り替え
    function showRecommendMode(mode) {{
        document.getElementById('rotation-mode').style.display = mode === 'rotation' ? 'block' : 'none';
        document.getElementById('profit-mode').style.display = mode === 'profit' ? 'block' : 'none';
    }}

    // ダークモード切り替え
    function toggleTheme() {{
        const body = document.body;
        const btn = document.getElementById('themeBtn');
        if (body.getAttribute('data-theme') === 'dark') {{
            body.removeAttribute('data-theme');
            btn.textContent = '🌙 ダークモード';
        }} else {{
            body.setAttribute('data-theme', 'dark');
            btn.textContent = '☀️ ライトモード';
        }}
    }}

    // 為替レート取得
    async function updateExchangeRate() {{
        try {{
            const res = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            const data = await res.json();
            document.getElementById('exchangeRate').value = data.rates.JPY.toFixed(2);
        }} catch (e) {{
            alert('為替レート取得に失敗しました');
        }}
    }}

    // 再計算
    function recalculate() {{
        alert('再計算機能は準備中です');
    }}

    // グラフ描画
    document.addEventListener('DOMContentLoaded', function() {{
        // アイテムタイプ別棒グラフ
        Plotly.newPlot('itemTypeBarChart', [{{
            y: {json.dumps(item_type_labels)},
            x: {json.dumps(item_type_sales)},
            type: 'bar',
            orientation: 'h',
            marker: {{ color: '#e91e63' }}
        }}], {{...plotlyLayout, title: 'アイテムタイプ別販売数', xaxis: {{ title: '販売数' }}}}, plotlyConfig);

        // ブランドカテゴリ別円グラフ
        Plotly.newPlot('brandCatPieChart', [{{
            labels: {json.dumps(brand_cat_labels)},
            values: {json.dumps(brand_cat_sales)},
            type: 'pie',
            hole: 0.4
        }}], {{...plotlyLayout, title: 'ブランドカテゴリ別シェア'}}, plotlyConfig);

        // ブランド別棒グラフ
        Plotly.newPlot('brandBarChart', [{{
            y: {json.dumps(brand_top10_labels)},
            x: {json.dumps(brand_top10_sales)},
            type: 'bar',
            orientation: 'h',
            marker: {{ color: '#9c27b0' }}
        }}], {{...plotlyLayout, title: 'ブランド別販売数（Top10）', xaxis: {{ title: '販売数' }}, height: 400}}, plotlyConfig);

        // ブランド別円グラフ
        Plotly.newPlot('brandPieChart', [{{
            labels: {json.dumps(brand_top10_labels)},
            values: {json.dumps(brand_top10_sales)},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'ブランド別シェア（Top10）'}}, plotlyConfig);

        // 価格帯分布
        Plotly.newPlot('priceDistChart', [{{
            x: {json.dumps(price_dist_labels)},
            y: {json.dumps(price_dist_values)},
            type: 'bar',
            marker: {{ color: '#e91e63' }}
        }}], {{...plotlyLayout, title: '価格帯分布（50ドル刻み）', xaxis: {{ title: '価格帯' }}, yaxis: {{ title: '件数' }}}}, plotlyConfig);
''')

# 各ブランドタブのグラフ
for brand_name, tab_id, _ in brand_tabs:
    if tab_id in brand_price_dist:
        price_labels = list(brand_price_dist[tab_id].keys())
        price_values = list(brand_price_dist[tab_id].values())
        item_labels = list(brand_item_type_dist[tab_id].keys())
        item_values = list(brand_item_type_dist[tab_id].values())

        html_parts.append(f'''
        // {brand_name}の価格帯分布
        Plotly.newPlot('{tab_id}_price_chart', [{{
            x: {json.dumps(price_labels)},
            y: {json.dumps(price_values)},
            type: 'bar',
            marker: {{ color: '#e91e63' }}
        }}], {{...plotlyLayout, xaxis: {{ title: '価格帯' }}, yaxis: {{ title: '件数' }}}}, plotlyConfig);

        // {brand_name}のアイテムタイプ別分布
        Plotly.newPlot('{tab_id}_item_chart', [{{
            labels: {json.dumps(item_labels)},
            values: {json.dumps(item_values)},
            type: 'pie',
            hole: 0.4
        }}], {{...plotlyLayout}}, plotlyConfig);
''')

html_parts.append('''
    });
    </script>
</body>
</html>
''')

# HTMLファイル出力
output_path = '/Users/naokijodan/Desktop/hair-accessory-research/index.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(''.join(html_parts))

print(f"\n=== HTML生成完了 ===")
print(f"出力先: {output_path}")
print(f"ファイルサイズ: {len(''.join(html_parts)):,} bytes")
