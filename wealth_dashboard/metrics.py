from typing import Dict, List

class MetricsCalculator:
    def __init__(self, assets: List[Dict], liabilities: List[Dict], 
                 income_streams: List[Dict], expenses: List[Dict]):
        self.assets = assets
        self.liabilities = liabilities
        self.income_streams = income_streams
        self.expenses = expenses
    
    def calculate_net_worth(self) -> float:
        """Calculate total net worth"""
        total_assets = sum(a['current_value'] for a in self.assets)
        total_liabilities = sum(l['remaining_balance'] for l in self.liabilities)
        return total_assets - total_liabilities
    
    def calculate_asset_allocation(self) -> Dict:
        """Calculate allocation by asset type"""
        allocation = {
            'foundation': 0.0,
            'growth': 0.0,
            'high_risk': 0.0
        }
        
        for asset in self.assets:
            allocation[asset['asset_type']] += asset['current_value']
        
        return allocation
    
    def calculate_category_breakdown(self) -> Dict:
        """Calculate breakdown by category"""
        breakdown = {}
        for asset in self.assets:
            category = asset['category']
            breakdown[category] = breakdown.get(category, 0) + asset['current_value']
        return breakdown
    
    def calculate_monthly_cashflow(self) -> float:
        """Calculate monthly net cashflow"""
        total_income = sum(i['monthly_amount'] for i in self.income_streams)
        total_expenses = sum(e['monthly_amount'] for e in self.expenses)
        return total_income - total_expenses
    
    def calculate_risk_score(self) -> Dict:
        """Calculate risk metrics"""
        allocation = self.calculate_asset_allocation()
        total = sum(allocation.values())
        
        if total == 0:
            return {'score': 0, 'level': 'No Data'}
        
        high_risk_pct = (allocation['high_risk'] / total) * 100
        foundation_pct = (allocation['foundation'] / total) * 100
        
        # Simple risk scoring
        if high_risk_pct > 50:
            score = 8
            level = "Very High Risk"
        elif high_risk_pct > 30:
            score = 6
            level = "High Risk"
        elif foundation_pct > 60:
            score = 2
            level = "Conservative"
        elif foundation_pct > 40:
            score = 4
            level = "Moderate"
        else:
            score = 5
            level = "Balanced"
        
        return {
            'score': score,
            'level': level,
            'high_risk_percentage': high_risk_pct,
            'foundation_percentage': foundation_pct
        }
    
    def get_top_assets(self, n: int = 5) -> List[Dict]:
        """Get top N assets by value"""
        sorted_assets = sorted(self.assets, key=lambda x: x['current_value'], reverse=True)
        return sorted_assets[:n]
    
    def get_all_metrics(self) -> Dict:
        """Get all metrics in one dict"""
        allocation = self.calculate_asset_allocation()
        risk = self.calculate_risk_score()
        
        return {
            'net_worth': self.calculate_net_worth(),
            'asset_allocation': allocation,
            'category_breakdown': self.calculate_category_breakdown(),
            'monthly_cashflow': self.calculate_monthly_cashflow(),
            'risk': risk,
            'top_assets': self.get_top_assets(),
            'total_income': sum(i['monthly_amount'] for i in self.income_streams),
            'total_expenses': sum(e['monthly_amount'] for e in self.expenses),
            'total_liabilities': sum(l['remaining_balance'] for l in self.liabilities)
        }