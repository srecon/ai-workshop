import re
from typing import Dict, Tuple

# Russian to English column mapping
COLUMN_MAPPING = {
    'объект': 'name',
    'название': 'name',
    'монета': 'name',
    'тикер': 'name',
    'металл': 'name',
    'банк': 'name',
    'источник': 'source',
    'категория': 'category',
    'стоимость покупки': 'purchase_price',
    'цена покупки': 'purchase_price',
    'вложено': 'purchase_price',
    'текущая стоимость': 'current_value',
    'стоимость сейчас': 'current_value',
    'текущая цена': 'current_value',
    'количество': 'quantity',
    'вес': 'quantity',
    'ипотека': 'mortgage_amount',
    'сумма': 'amount',
    'остаток': 'remaining_balance',
    'ставка': 'interest_rate',
    'сумма в месяц': 'monthly_amount',
    'дата открытия': 'opening_date'
}

# Sheet name to asset category detection
SHEET_PATTERNS = {
    'real_estate': ['real estate', 'недвижимость', 'property'],
    'business': ['business', 'бизнес', 'company'],
    'deposits': ['deposit', 'депозит', 'вклад', 'savings'],
    'crypto': ['crypto', 'крипто', 'bitcoin', 'ethereum'],
    'stocks': ['stock', 'акци', 'share', 'equity'],
    'precious_metals': ['metal', 'металл', 'gold', 'silver', 'золото', 'серебро'],
    'loans': ['loan', 'займ', 'credit', 'кредит'],
    'income': ['income', 'доход', 'salary', 'зарплата'],
    'expenses': ['expense', 'расход', 'spending']
}

ASSET_TYPE_MAPPING = {
    'real_estate': 'foundation',
    'deposits': 'foundation',
    'precious_metals': 'foundation',
    'business': 'growth',
    'stocks': 'growth',
    'crypto': 'high_risk',
    'loans': 'liability',
    'income': 'income',
    'expenses': 'expense'
}

def detect_sheet_type(sheet_name: str, df_columns: list) -> Tuple[str, str]:
    """Auto-detect sheet type and asset category"""
    sheet_name_lower = sheet_name.lower()
    
    # First check sheet name patterns
    for asset_category, patterns in SHEET_PATTERNS.items():
        for pattern in patterns:
            if pattern in sheet_name_lower:
                asset_type = ASSET_TYPE_MAPPING.get(asset_category, 'growth')
                return asset_category, asset_type
    
    # If sheet name doesn't match, check column patterns
    columns_lower = [str(c).lower() for c in df_columns]
    
    if any('цена' in col or 'стоимость' in col for col in columns_lower):
        if any('крипто' in col or 'crypto' in col for col in columns_lower):
            return 'crypto', 'high_risk'
        elif any('акци' in col or 'stock' in col for col in columns_lower):
            return 'stocks', 'growth'
        elif any('недвижимость' in col or 'real estate' in col for col in columns_lower):
            return 'real_estate', 'foundation'
    
    if any('сумма' in col or 'amount' in col for col in columns_lower):
        if any('доход' in col or 'income' in col for col in columns_lower):
            return 'income', 'income'
        elif any('расход' in col or 'expense' in col for col in columns_lower):
            return 'expenses', 'expense'
    
    # Default fallbacks
    if 'monthly_amount' in columns_lower or 'сумма в месяц' in columns_lower:
        return 'income', 'income'
    
    return 'other', 'growth'

def translate_columns(df_columns: list) -> dict:
    """Map Russian column names to English"""
    mapping = {}
    for col in df_columns:
        col_lower = str(col).lower().strip()
        mapped = COLUMN_MAPPING.get(col_lower, col_lower.replace(' ', '_'))
        mapping[col] = mapped
    return mapping

def classify_asset(row: dict, category: str, asset_type: str) -> dict:
    """Classify individual asset row"""
    asset = {
        'name': row.get('name', 'Unknown'),
        'asset_type': asset_type,
        'category': category,
        'purchase_price': float(row.get('purchase_price', 0)) if row.get('purchase_price') else 0,
        'current_value': float(row.get('current_value', 0)) if row.get('current_value') else 0,
        'quantity': float(row.get('quantity', 1)) if row.get('quantity') else 1,
        'metadata_json': {}
    }
    
    # Handle mortgage for real estate
    if 'mortgage_amount' in row and row['mortgage_amount']:
        asset['metadata_json']['mortgage'] = float(row['mortgage_amount'])
        # Adjust current value to equity
        if asset['current_value'] > 0:
            asset['current_value'] = max(0, asset['current_value'] - float(row['mortgage_amount']))
    
    # If only purchase price exists but no current value, use purchase price
    if asset['current_value'] == 0 and asset['purchase_price'] > 0:
        asset['current_value'] = asset['purchase_price']
    
    return asset