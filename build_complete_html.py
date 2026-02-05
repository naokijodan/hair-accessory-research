#!/usr/bin/env python3
"""髪飾り市場分析HTML完全版生成スクリプト - 時計分析HTMLと同等の構造"""

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
                   'Alexandre de Paris', 'colette malouf']
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

# CITES規制品判定
def is_cites_risk(title):
    risk_keywords = ['TORTOISE', 'BEKKO', 'IVORY', 'べっ甲', '象牙', 'TORTOISESHELL']
    title_upper = str(title).upper()
    for kw in risk_keywords:
        if kw in title_upper:
            return True
    return False

df['CITES_RISK'] = df['タイトル'].apply(is_cites_risk)

# 仕入れ上限計算
df['仕入れ上限'] = df['価格'] * EXCHANGE_RATE * (1 - FEE_RATE) - SHIPPING_JPY

# CV値（変動係数）計算関数
def calc_cv(prices):
    if len(prices) < 2:
        return 0
    return float(prices.std() / prices.mean()) if prices.mean() > 0 else 0

# 月次データ抽出
df['販売月'] = pd.to_datetime(df['販売日']).dt.to_period('M').astype(str)

# 主要ブランドを特定
brand_sales = df.groupby('ブランド')['販売数'].sum().sort_values(ascending=False)
top_brands = brand_sales[brand_sales.index != '(不明)'].head(10).index.tolist()

print(f"\n=== トップ10ブランド ===")
for b in top_brands:
    print(f"  - {b}")

# アイテムタイプ別統計
item_type_stats = {}
for item_type in df['アイテムタイプ'].unique():
    type_df = df[df['アイテムタイプ'] == item_type]
    if len(type_df) < 3:
        continue
    item_type_stats[item_type] = {
        'count': int(len(type_df)),
        'sales': int(type_df['販売数'].sum()),
        'revenue': float(type_df['売上'].sum()),
        'avg_price': float(type_df['価格'].mean()),
        'median_price': float(type_df['価格'].median()),
        'min_price': float(type_df['価格'].min()),
        'max_price': float(type_df['価格'].max()),
        'cv': float(calc_cv(type_df['価格'])),
        'purchase_limit': float(type_df['仕入れ上限'].median())
    }

# ブランド別統計
brand_stats = {}
for brand in df['ブランド'].unique():
    brand_df = df[df['ブランド'] == brand]
    if len(brand_df) < 2:
        continue
    brand_stats[brand] = {
        'count': int(len(brand_df)),
        'sales': int(brand_df['販売数'].sum()),
        'revenue': float(brand_df['売上'].sum()),
        'avg_price': float(brand_df['価格'].mean()),
        'median_price': float(brand_df['価格'].median()),
        'min_price': float(brand_df['価格'].min()),
        'max_price': float(brand_df['価格'].max()),
        'cv': float(calc_cv(brand_df['価格'])),
        'purchase_limit': float(brand_df['仕入れ上限'].median())
    }

# 月次売上
monthly_sales = df.groupby('販売月').agg({
    '販売数': 'sum',
    '売上': 'sum'
}).reset_index()
monthly_sales = monthly_sales.sort_values('販売月')

# ブランドカテゴリ別統計
brand_cat_stats = {}
for cat in df['ブランドカテゴリ'].unique():
    cat_df = df[df['ブランドカテゴリ'] == cat]
    brand_cat_stats[cat] = {
        'count': int(len(cat_df)),
        'sales': int(cat_df['販売数'].sum()),
        'revenue': float(cat_df['売上'].sum()),
        'avg_price': float(cat_df['価格'].mean()),
        'median_price': float(cat_df['価格'].median())
    }

# まとめ売り統計
bulk_df = df[df['まとめ売り'] == True]
bulk_stats = {
    'count': int(len(bulk_df)),
    'sales': int(bulk_df['販売数'].sum()),
    'avg_price': float(bulk_df['価格'].mean()) if len(bulk_df) > 0 else 0,
    'median_price': float(bulk_df['価格'].median()) if len(bulk_df) > 0 else 0
}

# 価格帯分布
def get_price_distribution(prices):
    bins = [0, 25, 50, 75, 100, 150, 200, 300, 500, 1000, float('inf')]
    labels = ['$0-24', '$25-49', '$50-74', '$75-99', '$100-149', '$150-199', '$200-299', '$300-499', '$500-999', '$1000+']
    distribution = pd.cut(prices, bins=bins, labels=labels).value_counts().sort_index()
    return {k: int(v) for k, v in distribution.items()}

price_dist = get_price_distribution(df['価格'])

# おすすめ商品（回転重視）
safe_df = df[(df['まとめ売り'] == False) & (df['CITES_RISK'] == False)]
recommend_rotation = []
recommend_profit = []

grouped = safe_df.groupby(['ブランド', 'アイテムタイプ']).agg({
    '価格': ['count', 'mean', 'median', 'min', 'max', 'std'],
    '販売数': 'sum',
    '売上': 'sum',
    '仕入れ上限': 'median'
}).round(2)
grouped.columns = ['取引件数', '平均価格', '中央値', '最低価格', '最高価格', '標準偏差', '販売数', '売上', '仕入れ上限']
grouped['CV'] = grouped['標準偏差'] / grouped['平均価格']
grouped['CV'] = grouped['CV'].fillna(0)

# 回転重視
rotation_df = grouped[(grouped['CV'] <= 0.5) & (grouped['仕入れ上限'] <= 30000) & (grouped['販売数'] >= 3)]
rotation_df = rotation_df.copy()
rotation_df['スコア'] = rotation_df['仕入れ上限'] * rotation_df['販売数']
rotation_df = rotation_df.sort_values('スコア', ascending=False)

for idx, row in rotation_df.head(20).iterrows():
    brand, item_type = idx
    recommend_rotation.append({
        'brand': brand,
        'item_type': item_type,
        'sales': int(row['販売数']),
        'median_price': float(row['中央値']),
        'purchase_limit': float(row['仕入れ上限']),
        'cv': float(row['CV']),
        'score': float(row['スコア'])
    })

# 利益重視
profit_df = grouped.copy()
profit_df['スコア'] = profit_df['仕入れ上限'] * profit_df['販売数']
profit_df = profit_df.sort_values('スコア', ascending=False)

for idx, row in profit_df.head(30).iterrows():
    brand, item_type = idx
    recommend_profit.append({
        'brand': brand,
        'item_type': item_type,
        'sales': int(row['販売数']),
        'revenue': float(row['売上']),
        'median_price': float(row['中央値']),
        'purchase_limit': float(row['仕入れ上限']),
        'cv': float(row['CV']),
        'score': float(row['スコア'])
    })

# 主要アイテムタイプ
main_item_types = ['Barrette', 'Headband', 'Hair Clip', 'Tiara', 'Scrunchie', 'Kanzashi']

# ブランド別詳細データ
def get_brand_detail(brand_name):
    brand_df = df[df['ブランド'] == brand_name]
    if len(brand_df) < 3:
        return None

    type_stats = []
    for item_type in brand_df['アイテムタイプ'].unique():
        type_df = brand_df[brand_df['アイテムタイプ'] == item_type]
        if len(type_df) >= 1:
            type_stats.append({
                'item_type': item_type,
                'count': int(len(type_df)),
                'sales': int(type_df['販売数'].sum()),
                'avg_price': float(type_df['価格'].mean()),
                'median_price': float(type_df['価格'].median()),
                'min_price': float(type_df['価格'].min()),
                'max_price': float(type_df['価格'].max()),
                'purchase_limit': float(type_df['仕入れ上限'].median())
            })

    return {
        'total_count': int(len(brand_df)),
        'total_sales': int(brand_df['販売数'].sum()),
        'total_revenue': float(brand_df['売上'].sum()),
        'avg_price': float(brand_df['価格'].mean()),
        'median_price': float(brand_df['価格'].median()),
        'min_price': float(brand_df['価格'].min()),
        'max_price': float(brand_df['価格'].max()),
        'cv': float(calc_cv(brand_df['価格'])),
        'purchase_limit': float(brand_df['仕入れ上限'].median()),
        'type_stats': sorted(type_stats, key=lambda x: x['sales'], reverse=True),
        'novelty_count': int(len(brand_df[brand_df['ノベルティ'] == True])),
        'bulk_count': int(len(brand_df[brand_df['まとめ売り'] == True]))
    }

brand_details = {}
for brand in top_brands:
    detail = get_brand_detail(brand)
    if detail:
        brand_details[brand] = detail

# グラフ描画コードを収集
chart_scripts = []

# 月次売上データ
monthly_labels = monthly_sales['販売月'].tolist()
monthly_values = [float(v) for v in monthly_sales['売上'].tolist()]

# ブランド別シェア用データ
brand_pie_labels = list(brand_stats.keys())[:10]
brand_pie_values = [brand_stats[b]['sales'] for b in brand_pie_labels]

# アイテムタイプ別データ
item_pie_labels = list(item_type_stats.keys())
item_pie_values = [item_type_stats[t]['sales'] for t in item_pie_labels]

# 価格帯分布データ
price_dist_labels = list(price_dist.keys())
price_dist_values = list(price_dist.values())

# ブランドカテゴリ別データ
cat_pie_labels = list(brand_cat_stats.keys())
cat_pie_values = [brand_cat_stats[c]['sales'] for c in cat_pie_labels]

# ========== HTML生成 ==========

def generate_stats_grid(stats):
    """統計カードグリッドを生成"""
    return f'''
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">取引件数</div>
                <div class="value">{stats.get('count', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">総販売数</div>
                <div class="value">{stats.get('sales', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💵</div>
                <div class="label">平均価格</div>
                <div class="value">${stats.get('avg_price', 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${stats.get('median_price', 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">⬇️</div>
                <div class="label">最低価格</div>
                <div class="value">${stats.get('min_price', 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">⬆️</div>
                <div class="label">最高価格</div>
                <div class="value">${stats.get('max_price', 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📉</div>
                <div class="label">CV値</div>
                <div class="value">{stats.get('cv', 0):.3f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💴</div>
                <div class="label">仕入上限</div>
                <div class="value highlight">¥{stats.get('purchase_limit', 0):,.0f}</div>
            </div>
        </div>
    '''

def generate_brand_table(data, tab_id):
    """ブランド別テーブルを生成"""
    rows = []
    for brand, stats in sorted(data.items(), key=lambda x: x[1]['sales'], reverse=True)[:20]:
        if brand == '(不明)':
            display_name = '不明'
        else:
            display_name = brand

        keyword = brand.replace(' ', '+')
        rows.append(f'''
                    <tr>
                        <td><strong>{display_name}</strong></td>
                        <td>{stats['sales']:,}</td>
                        <td>${stats['min_price']:.2f}</td>
                        <td>${stats['max_price']:.2f}</td>
                        <td>${stats['median_price']:.2f}</td>
                        <td>¥{stats['median_price'] * EXCHANGE_RATE:,.0f}</td>
                        <td class="highlight">¥{stats['purchase_limit']:,.0f}</td>
                        <td>{stats['cv']:.3f}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={keyword}+Hair+Accessory&LH_Sold=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={keyword}%20髪飾り&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
        ''')

    return f'''
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
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    '''

# 主要アイテムタイプ用のタブ内容生成
def generate_item_type_tab(item_type):
    """アイテムタイプ別タブの内容を生成（スクリプトなし）"""
    type_df = df[df['アイテムタイプ'] == item_type]
    if len(type_df) < 3:
        return f'''
        <div id="type_{item_type.lower().replace(' ', '_')}" class="tab-content">
            <h2 class="section-title">{item_type} 市場分析</h2>
            <p>データが不足しています（{len(type_df)}件）</p>
        </div>
        ''', None

    stats = {
        'count': int(len(type_df)),
        'sales': int(type_df['販売数'].sum()),
        'revenue': float(type_df['売上'].sum()),
        'avg_price': float(type_df['価格'].mean()),
        'median_price': float(type_df['価格'].median()),
        'min_price': float(type_df['価格'].min()),
        'max_price': float(type_df['価格'].max()),
        'cv': float(calc_cv(type_df['価格'])),
        'purchase_limit': float(type_df['仕入れ上限'].median())
    }

    type_brand_stats = {}
    for brand in type_df['ブランド'].unique():
        brand_df = type_df[type_df['ブランド'] == brand]
        if len(brand_df) >= 1:
            type_brand_stats[brand] = {
                'count': int(len(brand_df)),
                'sales': int(brand_df['販売数'].sum()),
                'avg_price': float(brand_df['価格'].mean()),
                'median_price': float(brand_df['価格'].median()),
                'min_price': float(brand_df['価格'].min()),
                'max_price': float(brand_df['価格'].max()),
                'cv': float(calc_cv(brand_df['価格'])) if len(brand_df) >= 2 else 0,
                'purchase_limit': float(brand_df['仕入れ上限'].median())
            }

    top_brands_in_type = sorted(type_brand_stats.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
    chart_labels = [b[0] for b in top_brands_in_type]
    chart_values = [b[1]['sales'] for b in top_brands_in_type]

    tab_id = item_type.lower().replace(' ', '_')

    html = f'''
    <div id="type_{tab_id}" class="tab-content">
        <h2 class="section-title">{item_type} 市場分析</h2>
        {generate_stats_grid(stats)}
        <h3 class="section-title">📊 市場分析グラフ</h3>
        <div class="chart-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="chart-container"><div id="{tab_id}_brand_bar"></div></div>
            <div class="chart-container"><div id="{tab_id}_brand_pie"></div></div>
        </div>
        <h3 class="section-title">🏷️ ブランド別集計（Top20）</h3>
        {generate_brand_table(type_brand_stats, tab_id)}
    </div>
    '''

    script = f'''
        Plotly.newPlot('{tab_id}_brand_bar', [{{
            x: {chart_values},
            y: {json.dumps(chart_labels, ensure_ascii=False)},
            type: 'bar',
            orientation: 'h',
            marker: {{color: '#E91E63'}}
        }}], {{...plotlyLayout, title: 'ブランド別販売数（Top10）'}}, plotlyConfig);
        Plotly.newPlot('{tab_id}_brand_pie', [{{
            labels: {json.dumps(chart_labels, ensure_ascii=False)},
            values: {chart_values},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'ブランド別シェア'}}, plotlyConfig);
    '''

    return html, script

# 主要ブランド用のタブ内容生成
def generate_brand_tab(brand_name):
    """ブランド別タブの内容を生成（スクリプトなし）"""
    if brand_name not in brand_details:
        return '', None

    detail = brand_details[brand_name]
    tab_id = brand_name.lower().replace(' ', '_').replace('.', '').replace('&', '')

    type_rows = []
    for ts in detail['type_stats'][:15]:
        keyword = f"{brand_name.replace(' ', '+')}+{ts['item_type'].replace(' ', '+')}"
        type_rows.append(f'''
                    <tr>
                        <td><strong>{ts['item_type']}</strong></td>
                        <td>{ts['sales']:,}</td>
                        <td>${ts['min_price']:.2f}</td>
                        <td>${ts['max_price']:.2f}</td>
                        <td>${ts['median_price']:.2f}</td>
                        <td class="highlight">¥{ts['purchase_limit']:,.0f}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={keyword}&LH_Sold=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={brand_name}%20{ts['item_type']}&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
        ''')

    chart_labels = [ts['item_type'] for ts in detail['type_stats'][:8]]
    chart_values = [ts['sales'] for ts in detail['type_stats'][:8]]

    stats = {
        'count': detail['total_count'],
        'sales': detail['total_sales'],
        'avg_price': detail['avg_price'],
        'median_price': detail['median_price'],
        'min_price': detail['min_price'],
        'max_price': detail['max_price'],
        'cv': detail['cv'],
        'purchase_limit': detail['purchase_limit']
    }

    html = f'''
    <div id="brand_{tab_id}" class="tab-content">
        <h2 class="section-title">{brand_name} 詳細分析</h2>
        {generate_stats_grid(stats)}
        <div class="insight-box">
            <h3>💡 {brand_name} の特徴</h3>
            <ul>
                <li>📦 総販売数: {detail['total_sales']:,}個</li>
                <li>💰 総売上: ${detail['total_revenue']:,.2f}</li>
                <li>🎁 ノベルティ品: {detail['novelty_count']}件</li>
                <li>📦 まとめ売り: {detail['bulk_count']}件</li>
            </ul>
        </div>
        <h3 class="section-title">📊 アイテムタイプ別分析</h3>
        <div class="chart-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="chart-container"><div id="{tab_id}_type_bar"></div></div>
            <div class="chart-container"><div id="{tab_id}_type_pie"></div></div>
        </div>
        <h3 class="section-title">🏷️ アイテムタイプ別集計</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>アイテムタイプ</th>
                        <th>販売数</th>
                        <th>最低価格</th>
                        <th>最高価格</th>
                        <th>中央値($)</th>
                        <th>仕入上限(¥)</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(type_rows)}
                </tbody>
            </table>
        </div>
    </div>
    '''

    script = f'''
        Plotly.newPlot('{tab_id}_type_bar', [{{
            x: {chart_values},
            y: {json.dumps(chart_labels, ensure_ascii=False)},
            type: 'bar',
            orientation: 'h',
            marker: {{color: '#9C27B0'}}
        }}], {{...plotlyLayout, title: 'アイテムタイプ別販売数'}}, plotlyConfig);
        Plotly.newPlot('{tab_id}_type_pie', [{{
            labels: {json.dumps(chart_labels, ensure_ascii=False)},
            values: {chart_values},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'アイテムタイプ別シェア'}}, plotlyConfig);
    '''

    return html, script

# タブとスクリプトを収集
item_type_tabs_html = []
item_type_scripts = []
for t in main_item_types:
    if t in item_type_stats:
        html, script = generate_item_type_tab(t)
        item_type_tabs_html.append(html)
        if script:
            item_type_scripts.append(script)

brand_tabs_html = []
brand_scripts = []
for b in top_brands[:6]:
    html, script = generate_brand_tab(b)
    if html:
        brand_tabs_html.append(html)
    if script:
        brand_scripts.append(script)

# アイテムタイプタブボタン
item_type_tab_buttons = ''.join([
    f'<button class="tab" onclick="showTab(\'type_{t.lower().replace(" ", "_")}\')">{t}</button>'
    for t in main_item_types if t in item_type_stats
])

# ブランドタブボタン
brand_tab_buttons = ''.join([
    f'<button class="tab" onclick="showTab(\'brand_{b.lower().replace(" ", "_").replace(".", "").replace("&", "")}\')">{b}</button>'
    for b in top_brands[:6]
])

# おすすめ回転重視テーブル
rotation_rows = []
for i, rec in enumerate(recommend_rotation[:15], 1):
    stability = '★★★' if rec['cv'] <= 0.2 else ('★★☆' if rec['cv'] <= 0.35 else '★☆☆')
    rotation_rows.append(f'''
                        <tr>
                            <td><strong>{i}</strong></td>
                            <td>{rec['brand']}</td>
                            <td>{rec['item_type']}</td>
                            <td>{rec['sales']}</td>
                            <td>${rec['median_price']:.2f}</td>
                            <td class="highlight">¥{rec['purchase_limit']:,.0f}</td>
                            <td>{stability}</td>
                            <td>{rec['score']:,.0f}</td>
                        </tr>
    ''')

# おすすめ利益重視テーブル
profit_rows = []
for i, rec in enumerate(recommend_profit[:20], 1):
    risk = '<span class="risk-low">低</span>' if rec['cv'] <= 0.3 else ('<span class="risk-mid">中</span>' if rec['cv'] <= 0.6 else '<span class="risk-high">高</span>')
    profit_rows.append(f'''
                        <tr>
                            <td><strong>{i}</strong></td>
                            <td>{rec['brand']}</td>
                            <td>{rec['item_type']}</td>
                            <td>{rec['sales']}</td>
                            <td>${rec['median_price']:.2f}</td>
                            <td class="highlight">¥{rec['purchase_limit']:,.0f}</td>
                            <td>{risk}</td>
                            <td>{rec['score']:,.0f}</td>
                        </tr>
    ''')

# CITES警告品
cites_df = df[df['CITES_RISK'] == True]
cites_warning = ''
if len(cites_df) > 0:
    cites_warning = f'''
        <div class="insight-box" style="background: linear-gradient(135deg, #ffebee, #ffcdd2); border-left: 4px solid #f44336;">
            <h3>⚠️ CITES規制リスク品検出（{len(cites_df)}件）</h3>
            <p>べっ甲・象牙などのワシントン条約規制対象の可能性がある商品が検出されました。輸出入には許可証が必要です。</p>
        </div>
    '''

# 全スクリプトを結合
all_chart_scripts = '\n'.join(item_type_scripts + brand_scripts)

# HTML生成
html_content = f'''<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>髪飾り市場分析 - eBay転売リサーチ</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --border-color: #dee2e6;
            --accent-color: #E91E63;
            --accent-light: #FCE4EC;
            --card-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        [data-theme="dark"] {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --border-color: #3a3a5a;
            --accent-light: #3a1a2e;
            --card-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-secondary); color: var(--text-primary); line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #E91E63 0%, #9C27B0 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.1em; }}
        .settings-panel {{ background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; margin: 20px auto; max-width: 800px; display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; align-items: center; }}
        .settings-panel label {{ display: flex; align-items: center; gap: 8px; font-size: 0.9em; }}
        .settings-panel input {{ width: 80px; padding: 5px 10px; border: none; border-radius: 5px; text-align: right; }}
        .settings-panel button {{ background: white; color: #E91E63; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-weight: bold; }}
        .settings-panel button:hover {{ background: #FCE4EC; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .tab-nav {{ display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 20px; background: var(--bg-primary); padding: 10px; border-radius: 10px; box-shadow: var(--card-shadow); }}
        .tab {{ padding: 10px 20px; border: none; background: var(--bg-secondary); color: var(--text-primary); cursor: pointer; border-radius: 5px; transition: all 0.3s; font-size: 0.9em; }}
        .tab:hover {{ background: var(--accent-light); }}
        .tab.active {{ background: var(--accent-color); color: white; }}
        .tab-content {{ display: none; background: var(--bg-primary); padding: 20px; border-radius: 10px; box-shadow: var(--card-shadow); }}
        .tab-content.active {{ display: block; }}
        .section-title {{ font-size: 1.3em; margin: 20px 0 15px; padding-bottom: 10px; border-bottom: 2px solid var(--accent-color); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: var(--bg-secondary); padding: 15px; border-radius: 10px; text-align: center; }}
        .stat-card .icon {{ font-size: 1.5em; margin-bottom: 5px; }}
        .stat-card .label {{ font-size: 0.8em; color: var(--text-secondary); margin-bottom: 5px; }}
        .stat-card .value {{ font-size: 1.4em; font-weight: bold; color: var(--text-primary); }}
        .stat-card .value.highlight {{ color: var(--accent-color); }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .chart-container {{ background: var(--bg-secondary); padding: 15px; border-radius: 10px; min-height: 350px; }}
        .table-container {{ overflow-x: auto; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th, td {{ padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--border-color); }}
        th {{ background: var(--bg-secondary); font-weight: 600; position: sticky; top: 0; }}
        tr:hover {{ background: var(--accent-light); }}
        .highlight {{ color: var(--accent-color); font-weight: bold; }}
        .link-btn {{ display: inline-block; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 0.8em; margin: 2px; }}
        .link-ebay {{ background: #0064D2; color: white; }}
        .link-mercari {{ background: #FF0211; color: white; }}
        .insight-box {{ background: linear-gradient(135deg, var(--accent-light), var(--bg-secondary)); border-left: 4px solid var(--accent-color); padding: 15px 20px; border-radius: 0 10px 10px 0; margin: 20px 0; }}
        .insight-box h3 {{ margin-bottom: 10px; }}
        .insight-box ul {{ margin-left: 20px; }}
        .mode-selector {{ display: flex; gap: 20px; margin-bottom: 20px; padding: 15px; background: var(--bg-secondary); border-radius: 10px; }}
        .mode-selector label {{ display: flex; align-items: center; gap: 8px; cursor: pointer; }}
        .risk-low {{ color: #4CAF50; font-weight: bold; }}
        .risk-mid {{ color: #FF9800; font-weight: bold; }}
        .risk-high {{ color: #f44336; font-weight: bold; }}
        @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>髪飾り市場分析</h1>
        <p class="subtitle">eBay転売リサーチ - {period_start} ~ {period_end}</p>
        <div class="settings-panel">
            <label>💴 為替レート<input type="number" id="exchangeRate" value="{EXCHANGE_RATE}" step="0.1"><button onclick="updateExchangeRate()">最新取得</button></label>
            <label>📦 送料<input type="number" id="shippingCost" value="{SHIPPING_JPY}"></label>
            <label>💳 手数料率<input type="number" id="feeRate" value="{int(FEE_RATE*100)}" step="1">%</label>
            <button onclick="recalculate()">再計算</button>
            <button id="themeBtn" onclick="toggleTheme()">🌙 ダークモード</button>
        </div>
    </div>
    <div class="container">
        <div class="tab-nav">
            <button class="tab active" onclick="showTab('overview')">📊 全体分析</button>
            <button class="tab" onclick="showTab('item_types')">🎀 アイテム別</button>
            <button class="tab" onclick="showTab('brands')">🏷️ ブランド別</button>
            <button class="tab" onclick="showTab('bundle')">📦 まとめ売り</button>
            <button class="tab" onclick="showTab('recommend')">⭐ おすすめ順序</button>
        </div>
        <div id="overview" class="tab-content active">
            <h2 class="section-title">📊 全体市場分析</h2>
            <div class="stats-grid">
                <div class="stat-card"><div class="icon">📊</div><div class="label">取引件数</div><div class="value">{len(df):,}</div></div>
                <div class="stat-card"><div class="icon">📦</div><div class="label">総販売数</div><div class="value">{total_sales:,}</div></div>
                <div class="stat-card"><div class="icon">💵</div><div class="label">総売上</div><div class="value">${total_revenue:,.2f}</div></div>
                <div class="stat-card"><div class="icon">📈</div><div class="label">平均価格</div><div class="value">${float(df['価格'].mean()):,.2f}</div></div>
                <div class="stat-card"><div class="icon">💰</div><div class="label">中央値</div><div class="value">${float(df['価格'].median()):,.2f}</div></div>
                <div class="stat-card"><div class="icon">⬆️</div><div class="label">最高価格</div><div class="value">${float(df['価格'].max()):,.2f}</div></div>
                <div class="stat-card"><div class="icon">📉</div><div class="label">CV値</div><div class="value">{calc_cv(df['価格']):.3f}</div></div>
                <div class="stat-card"><div class="icon">💴</div><div class="label">仕入上限中央値</div><div class="value highlight">¥{float(df['仕入れ上限'].median()):,.0f}</div></div>
            </div>
            {cites_warning}
            <h3 class="section-title">📊 市場分析グラフ</h3>
            <div class="chart-grid">
                <div class="chart-container"><div id="monthly_chart"></div></div>
                <div class="chart-container"><div id="brand_pie_chart"></div></div>
                <div class="chart-container"><div id="item_type_chart"></div></div>
                <div class="chart-container"><div id="price_dist_chart"></div></div>
                <div class="chart-container"><div id="category_pie_chart"></div></div>
            </div>
            <h3 class="section-title">🏷️ ブランド別集計（Top20）</h3>
            {generate_brand_table(brand_stats, 'overview')}
        </div>
        <div id="item_types" class="tab-content">
            <h2 class="section-title">🎀 アイテムタイプ別分析</h2>
            <div class="tab-nav">{item_type_tab_buttons}</div>
        </div>
        {''.join(item_type_tabs_html)}
        <div id="brands" class="tab-content">
            <h2 class="section-title">🏷️ ブランド別詳細分析</h2>
            <div class="tab-nav">{brand_tab_buttons}</div>
        </div>
        {''.join(brand_tabs_html)}
        <div id="bundle" class="tab-content">
            <h2 class="section-title">📦 まとめ売り分析</h2>
            <div class="stats-grid">
                <div class="stat-card"><div class="icon">📦</div><div class="label">まとめ売り件数</div><div class="value">{bulk_stats['count']:,}</div></div>
                <div class="stat-card"><div class="icon">📊</div><div class="label">総販売数</div><div class="value">{bulk_stats['sales']:,}</div></div>
                <div class="stat-card"><div class="icon">💰</div><div class="label">平均価格</div><div class="value">${bulk_stats['avg_price']:,.2f}</div></div>
                <div class="stat-card"><div class="icon">📈</div><div class="label">中央値</div><div class="value">${bulk_stats['median_price']:,.2f}</div></div>
            </div>
            <div class="insight-box">
                <h3>💡 まとめ売りの特徴</h3>
                <ul>
                    <li>🎯 仕入れ戦略: まとめ売りは単価分析には不向きだが、ボリュームディスカウントで仕入れ可能</li>
                    <li>📦 分解転売: まとめ売りを仕入れて個別販売することで利益率向上の可能性</li>
                    <li>⚠️ 注意: 状態確認が困難なため、リスクは高い</li>
                </ul>
            </div>
        </div>
        <div id="recommend" class="tab-content">
            <h2 class="section-title">⭐ おすすめ出品順序</h2>
            <div class="mode-selector">
                <label><input type="radio" name="recMode" value="rotation" checked onchange="switchRecMode()"> 🔄 回転重視（初心者向け）</label>
                <label><input type="radio" name="recMode" value="profit" onchange="switchRecMode()"> 💰 利益重視（経験者向け）</label>
            </div>
            <div id="rotationMode">
                <div class="insight-box">
                    <h3>🔄 回転重視モードの条件</h3>
                    <ul><li>変動係数（CV）≤ 0.5（価格が安定）</li><li>仕入上限 ≤ ¥30,000（低資金でも仕入可能）</li><li>販売数 ≥ 3件（一定の需要）</li></ul>
                </div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>順位</th><th>ブランド</th><th>アイテムタイプ</th><th>販売数</th><th>中央値($)</th><th>仕入上限</th><th>安定度</th><th>スコア</th></tr></thead>
                        <tbody>{''.join(rotation_rows)}</tbody>
                    </table>
                </div>
            </div>
            <div id="profitMode" style="display:none;">
                <div class="insight-box">
                    <h3>💰 利益重視モードの特徴</h3>
                    <ul><li>スコア = 仕入上限 × 販売数</li><li>全商品が対象（フィルタなし）</li><li>高単価・高需要商品を優先</li></ul>
                </div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>順位</th><th>ブランド</th><th>アイテムタイプ</th><th>販売数</th><th>中央値($)</th><th>仕入上限</th><th>リスク</th><th>スコア</th></tr></thead>
                        <tbody>{''.join(profit_rows)}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
    // Plotly共通設定（グローバルスコープで定義）
    const plotlyLayout = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'inherit', color: 'inherit' }},
        margin: {{ l: 50, r: 20, t: 40, b: 40 }}
    }};
    const plotlyConfig = {{ responsive: true, displayModeBar: false }};

    function toggleTheme() {{
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        document.getElementById('themeBtn').textContent = newTheme === 'dark' ? '☀️ ライトモード' : '🌙 ダークモード';
        localStorage.setItem('theme', newTheme);
    }}

    function showTab(tabId) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        event.target.classList.add('active');
    }}

    function switchRecMode() {{
        const mode = document.querySelector('input[name="recMode"]:checked').value;
        document.getElementById('rotationMode').style.display = mode === 'rotation' ? 'block' : 'none';
        document.getElementById('profitMode').style.display = mode === 'profit' ? 'block' : 'none';
    }}

    async function updateExchangeRate() {{
        try {{
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            const data = await response.json();
            const newRate = data.rates.JPY;
            document.getElementById('exchangeRate').value = Math.round(newRate * 10) / 10;
            recalculate();
            alert('為替レート更新完了: $1 = ¥' + newRate.toFixed(2));
        }} catch (error) {{
            alert('為替レート取得失敗');
        }}
    }}

    function recalculate() {{
        const rate = parseFloat(document.getElementById('exchangeRate').value);
        const shipping = parseFloat(document.getElementById('shippingCost').value);
        const feeRate = parseFloat(document.getElementById('feeRate').value) / 100;
        document.querySelectorAll('.highlight').forEach(el => {{
            const row = el.closest('tr');
            if (!row) return;
            const cells = row.querySelectorAll('td');
            for (let cell of cells) {{
                const text = cell.textContent.trim();
                if (/^\\$[\\d,]+(\\.\\d+)?$/.test(text)) {{
                    const price = parseFloat(text.replace(/[^0-9.]/g, ''));
                    const breakeven = price * rate * (1 - feeRate) - shipping;
                    el.textContent = '¥' + Math.max(0, breakeven).toLocaleString('ja-JP', {{maximumFractionDigits: 0}});
                    break;
                }}
            }}
        }});
    }}

    document.addEventListener('DOMContentLoaded', function() {{
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {{
            document.documentElement.setAttribute('data-theme', 'dark');
            document.getElementById('themeBtn').textContent = '☀️ ライトモード';
        }}

        // 全体分析グラフ
        Plotly.newPlot('monthly_chart', [{{
            x: {json.dumps(monthly_labels)},
            y: {json.dumps(monthly_values)},
            type: 'bar',
            marker: {{color: '#E91E63'}}
        }}], {{...plotlyLayout, title: '月次売上推移'}}, plotlyConfig);

        Plotly.newPlot('brand_pie_chart', [{{
            labels: {json.dumps(brand_pie_labels, ensure_ascii=False)},
            values: {json.dumps(brand_pie_values)},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'ブランド別販売シェア（Top10）'}}, plotlyConfig);

        Plotly.newPlot('item_type_chart', [{{
            labels: {json.dumps(item_pie_labels, ensure_ascii=False)},
            values: {json.dumps(item_pie_values)},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'アイテムタイプ別シェア'}}, plotlyConfig);

        Plotly.newPlot('price_dist_chart', [{{
            x: {json.dumps(price_dist_labels)},
            y: {json.dumps(price_dist_values)},
            type: 'bar',
            marker: {{color: '#9C27B0'}}
        }}], {{...plotlyLayout, title: '価格帯分布'}}, plotlyConfig);

        Plotly.newPlot('category_pie_chart', [{{
            labels: {json.dumps(cat_pie_labels, ensure_ascii=False)},
            values: {json.dumps(cat_pie_values)},
            type: 'pie'
        }}], {{...plotlyLayout, title: 'ブランドカテゴリ別シェア'}}, plotlyConfig);

        // アイテムタイプ別・ブランド別グラフ
        {all_chart_scripts}
    }});
    </script>
</body>
</html>
'''

# HTMLファイル出力
output_path = '/Users/naokijodan/Desktop/hair-accessory-research/index.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n=== HTML生成完了 ===")
print(f"出力先: {output_path}")
print(f"ファイルサイズ: {len(html_content):,} bytes")
