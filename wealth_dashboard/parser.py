import pandas as pd
import io
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bilingual column mapping (Russian -> English AND English variations)
COLUMN_MAPPING = {
    # English variations
    'name': 'name',
    'symbol': 'name',
    'asset': 'name',
    'property': 'name',
    'coin': 'name',
    'metal': 'name',
    
    # Russian to English
    'объект': 'name',
    'название': 'name',
    'монета': 'name',
    'тикер': 'name',
    'металл': 'name',
    'банк': 'name',
    'источник': 'source',
    'категория': 'category',
    
    # Price columns
    'purchaseprice': 'purchase_price',
    'purchase price': 'purchase_price',
    'purchase_price': 'purchase_price',
    'cost': 'purchase_price',
    'стоимость покупки': 'purchase_price',
    'цена покупки': 'purchase_price',
    'вложено': 'purchase_price',
    
    'currentprice': 'current_value',
    'current price': 'current_value',
    'current_value': 'current_value',
    'value': 'current_value',
    'текущая стоимость': 'current_value',
    'стоимость сейчас': 'current_value',
    'текущая цена': 'current_value',
    
    # Quantity columns
    'quantity': 'quantity',
    'qty': 'quantity',
    'amount': 'quantity',
    'weight': 'quantity',
    'количество': 'quantity',
    'вес': 'quantity',
    
    # Liability columns
    'mortgage': 'mortgage_amount',
    'ипотека': 'mortgage_amount',
    'loan': 'loan_amount',
    'remaining': 'remaining_balance',
    'balance': 'remaining_balance',
    'остаток': 'remaining_balance',
    
    # Income columns
    'monthly income': 'monthly_amount',
    'monthly_amount': 'monthly_amount',
    'amount': 'monthly_amount',
    'сумма в месяц': 'monthly_amount',
    
    'interest rate': 'interest_rate',
    'rate': 'interest_rate',
    'ставка': 'interest_rate',
    
    'source': 'source',
    'category': 'category',
    'type': 'asset_type'
}

# Sheet name patterns (both English and Russian)
SHEET_CATEGORIES = {
    'real_estate': ['real estate', 'property', 'недвижимость', 'realty'],
    'business': ['business', 'company', 'бизнес', 'enterprise'],
    'deposits': ['deposit', 'bonds', 'fixed income', 'депозит', 'вклад', 'savings', 'bonds and deposits'],
    'crypto': ['crypto', 'cryptocurrency', 'крипто', 'криптовалюта', 'crypto assets'],
    'stocks': ['stock', 'equity', 'shares', 'акци', 'акции'],
    'precious_metals': ['metal', 'precious metal', 'gold', 'silver', 'металл', 'золото', 'серебро', 'metals'],
    'loans': ['loan', 'debt', 'liabilities', 'займ', 'кредит', 'liability'],
    'income': ['income', 'revenue', 'salary', 'доход', 'зарплата', 'income sources'],
    'expenses': ['expense', 'spending', 'расход', 'расходы'],
    'investment': ['investment', 'profit', 'loss', 'p&l']
}

ASSET_TYPE_MAPPING = {
    'real_estate': 'foundation',
    'deposits': 'foundation',
    'bonds': 'foundation',
    'precious_metals': 'foundation',
    'business': 'growth',
    'stocks': 'growth',
    'investment': 'growth',
    'crypto': 'high_risk',
    'loans': 'liability',
    'liabilities': 'liability',
    'income': 'income',
    'expenses': 'expense'
}

class WealthParser:
    def __init__(self):
        self.assets = []
        self.liabilities = []
        self.income_streams = []
        self.expenses = []
    
    def parse_excel(self, file_bytes: bytes) -> Dict:
        """Parse Excel file from bytes"""
        logger.info("Starting to parse Excel file")
        
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = excel_file.sheet_names
        logger.info(f"Found sheets: {sheet_names}")
        
        for sheet_name in sheet_names:
            logger.info(f"Processing sheet: {sheet_name}")
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
            logger.info(f"Sheet '{sheet_name}' has {len(df)} rows and columns: {list(df.columns)}")
            
            if df.empty:
                logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                continue
            
            # Normalize column names (lowercase, remove spaces)
            df.columns = [str(col).strip().replace(' ', '').lower() for col in df.columns]
            logger.info(f"Normalized columns: {list(df.columns)}")
            
            self._parse_sheet(sheet_name, df)
        
        logger.info(f"Parsing complete. Assets: {len(self.assets)}, Liabilities: {len(self.liabilities)}, "
                   f"Income: {len(self.income_streams)}, Expenses: {len(self.expenses)}")
        
        # Log first few assets for debugging
        if self.assets:
            logger.info(f"Sample asset: {self.assets[0]}")
        
        return self._get_summary()
    
    def _detect_sheet_type(self, sheet_name: str, df_columns: list) -> Tuple[str, str]:
        """Auto-detect sheet type and asset category"""
        sheet_name_lower = sheet_name.lower()
        
        # First check sheet name patterns
        for asset_category, patterns in SHEET_CATEGORIES.items():
            for pattern in patterns:
                if pattern in sheet_name_lower:
                    asset_type = ASSET_TYPE_MAPPING.get(asset_category, 'growth')
                    logger.info(f"Detected by sheet name: '{sheet_name}' -> {asset_category}/{asset_type}")
                    return asset_category, asset_type
        
        # Check columns for clues
        columns_str = ' '.join(df_columns)
        
        if 'crypto' in columns_str or 'cryptocurrency' in columns_str:
            return 'crypto', 'high_risk'
        elif 'stock' in columns_str or 'equity' in columns_str:
            return 'stocks', 'growth'
        elif 'realestate' in columns_str or 'property' in columns_str:
            return 'real_estate', 'foundation'
        elif 'deposit' in columns_str or 'bond' in columns_str:
            return 'deposits', 'foundation'
        elif 'metal' in columns_str:
            return 'precious_metals', 'foundation'
        elif 'income' in columns_str or 'revenue' in columns_str:
            return 'income', 'income'
        elif 'liabilities' in columns_str or 'loan' in columns_str or 'debt' in columns_str:
            return 'loans', 'liability'
        
        return 'other', 'growth'
    
    def _parse_sheet(self, sheet_name: str, df: pd.DataFrame):
        """Parse individual sheet"""
        # Auto-detect sheet type
        category, asset_type = self._detect_sheet_type(sheet_name, df.columns)
        logger.info(f"Detected category: {category}, type: {asset_type} for sheet '{sheet_name}'")
        
        # Process based on type
        if asset_type == 'liability':
            self._parse_liabilities(df, category, sheet_name)
        elif asset_type == 'income':
            self._parse_income(df, sheet_name)
        else:
            self._parse_assets(df, category, asset_type, sheet_name)
    
    def _parse_assets(self, df: pd.DataFrame, category: str, asset_type: str, sheet_name: str):
        """Parse asset rows"""
        logger.info(f"Parsing assets from sheet '{sheet_name}'")
        
        for idx, row in df.iterrows():
            # Extract name
            name = None
            for col in ['name', 'symbol', 'asset']:
                if col in df.columns and pd.notna(row[col]):
                    name = str(row[col])
                    break
            
            if not name:
                name = f"{category}_{idx}"
            
            # Extract quantity
            quantity = 1
            for col in ['quantity', 'qty', 'amount']:
                if col in df.columns and pd.notna(row[col]):
                    try:
                        quantity = float(row[col])
                        break
                    except:
                        pass
            
            # Extract purchase price
            purchase_price = 0
            for col in ['purchaseprice', 'purchase_price', 'cost']:
                if col in df.columns and pd.notna(row[col]):
                    try:
                        purchase_price = float(row[col])
                        break
                    except:
                        pass
            
            # Extract current value
            current_value = 0
            for col in ['currentprice', 'current_price', 'currentvalue', 'value']:
                if col in df.columns and pd.notna(row[col]):
                    try:
                        current_value = float(row[col])
                        break
                    except:
                        pass
            
            # If current_value is 0 but we have quantity and purchase price
            if current_value == 0 and purchase_price > 0:
                current_value = purchase_price * quantity
            
            # If still 0, try to calculate from quantity * current price per unit
            if current_value == 0 and 'currentprice' in df.columns:
                try:
                    current_value = quantity * float(row['currentprice'])
                except:
                    pass
            
            if current_value > 0:
                asset = {
                    'name': name,
                    'asset_type': asset_type,
                    'category': category,
                    'purchase_price': float(purchase_price),
                    'current_value': float(current_value),
                    'quantity': float(quantity),
                    'currency': 'RUB',
                    'metadata_json': {}
                }
                
                self.assets.append(asset)
                logger.info(f"Added asset: {name} - {current_value:,.0f} RUB (qty: {quantity}, purchase: {purchase_price})")
    
    def _parse_liabilities(self, df: pd.DataFrame, category: str, sheet_name: str):
        """Parse liability rows"""
        logger.info(f"Parsing liabilities from sheet '{sheet_name}'")
        
        for idx, row in df.iterrows():
            # Extract name
            name = None
            for col in ['name', 'symbol']:
                if col in df.columns and pd.notna(row[col]):
                    name = str(row[col])
                    break
            
            if not name:
                name = f"liability_{idx}"
            
            # Extract amount/balance
            amount = 0
            for col in ['amount', 'balance', 'currentprice', 'value']:
                if col in df.columns and pd.notna(row[col]):
                    try:
                        amount = float(row[col])
                        break
                    except:
                        pass
            
            if amount > 0:
                liability = {
                    'name': name,
                    'liability_type': category,
                    'amount': amount,
                    'remaining_balance': amount,
                    'interest_rate': 0,
                    'metadata_json': {}
                }
                self.liabilities.append(liability)
                logger.info(f"Added liability: {name} - {amount:,.0f} RUB")
    
    def _parse_income(self, df: pd.DataFrame, sheet_name: str):
        """Parse income rows"""
        logger.info(f"Parsing income from sheet '{sheet_name}'")
        
        for idx, row in df.iterrows():
            # Extract name/source
            source = None
            for col in ['name', 'source', 'symbol']:
                if col in df.columns and pd.notna(row[col]):
                    source = str(row[col])
                    break
            
            if not source:
                source = f"income_{idx}"
            
            # Extract monthly amount
            monthly_amount = 0
            for col in ['monthlyincome', 'monthly_income', 'amount']:
                if col in df.columns and pd.notna(row[col]):
                    try:
                        monthly_amount = float(row[col])
                        break
                    except:
                        pass
            
            if monthly_amount > 0:
                income = {
                    'source': source,
                    'monthly_amount': monthly_amount,
                    'is_passive': 0
                }
                self.income_streams.append(income)
                logger.info(f"Added income: {source} - {monthly_amount:,.0f} RUB/month")
    
    def _get_summary(self) -> Dict:
        """Get parsing summary"""
        total_assets_value = sum(a['current_value'] for a in self.assets)
        
        return {
            'assets': self.assets,
            'liabilities': self.liabilities,
            'income_streams': self.income_streams,
            'expenses': self.expenses,
            'stats': {
                'total_assets': len(self.assets),
                'total_assets_value': total_assets_value,
                'total_liabilities': len(self.liabilities),
                'total_income_sources': len(self.income_streams),
                'total_expense_categories': len(self.expenses)
            }
        }