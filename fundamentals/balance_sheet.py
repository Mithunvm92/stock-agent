import yfinance as yf
import pandas as pd
from datetime import datetime
from config.settings import FUNDAMENTAL_FILTERS


class FundamentalAnalyzer:
    """
    Balance Sheet & Financial Statement Analysis
    
    Filters stocks based on:
    1. Debt levels (Debt/Equity)
    2. Liquidity (Current Ratio)
    3. Profitability (ROE, ROA, Margins)
    4. Growth (Revenue, EPS)
    5. Cash Flow
    6. Ownership (Promoter, Institutional)
    """

    def __init__(self, ticker):
        self.ticker = ticker
        self.stock = None
        self.info = {}
        self.financials = {}
        self.balance_sheet = {}
        self.cash_flow = {}
        self.score = 0
        self.max_score = 10
        self.passed_checks = []
        self.failed_checks = []

    def fetch_data(self):
        """Fetch all fundamental data from Yahoo Finance"""
        print(f"📊 Fetching fundamentals for {self.ticker}...")

        try:
            self.stock = yf.Ticker(self.ticker)

            # Basic info
            self.info = self.stock.info or {}

            # Financial statements
            try:
                self.financials = self.stock.financials
            except Exception:
                self.financials = pd.DataFrame()

            try:
                self.balance_sheet = self.stock.balance_sheet
            except Exception:
                self.balance_sheet = pd.DataFrame()

            try:
                self.cash_flow = self.stock.cashflow
            except Exception:
                self.cash_flow = pd.DataFrame()

            return True

        except Exception as e:
            print(f"❌ Error fetching fundamentals: {e}")
            return False

    def analyze(self):
        """Run full fundamental analysis"""
        if not self.stock:
            self.fetch_data()

        self.score = 0
        self.passed_checks = []
        self.failed_checks = []

        # Run all checks
        self._check_debt_equity()
        self._check_current_ratio()
        self._check_roe()
        self._check_roa()
        self._check_profit_margin()
        self._check_revenue_growth()
        self._check_eps_growth()
        self._check_free_cash_flow()
        self._check_promoter_holding()
        self._check_institutional_holding()

        return self._generate_report()

    def _check_debt_equity(self):
        """Check Debt to Equity ratio"""
        try:
            de_ratio = self.info.get('debtToEquity', None)
            
            if de_ratio is None:
                # Try calculating from balance sheet
                if not self.balance_sheet.empty:
                    total_debt = self._get_value(self.balance_sheet, 
                        ['Total Debt', 'Long Term Debt', 'Total Liab'])
                    total_equity = self._get_value(self.balance_sheet,
                        ['Total Stockholder Equity', 'Stockholders Equity', 'Total Equity'])
                    if total_equity and total_equity > 0:
                        de_ratio = (total_debt or 0) / total_equity * 100

            if de_ratio is not None:
                # Yahoo returns as percentage (e.g., 50 means 0.5)
                de_ratio_normalized = de_ratio / 100 if de_ratio > 10 else de_ratio
                
                if de_ratio_normalized <= FUNDAMENTAL_FILTERS['max_debt_equity']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Debt/Equity: {de_ratio_normalized:.2f} (< {FUNDAMENTAL_FILTERS['max_debt_equity']})")
                else:
                    self.failed_checks.append(f"❌ Debt/Equity: {de_ratio_normalized:.2f} (> {FUNDAMENTAL_FILTERS['max_debt_equity']})")
            else:
                self.failed_checks.append("⚠️ Debt/Equity: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Debt/Equity: Error - {e}")

    def _check_current_ratio(self):
        """Check Current Ratio (liquidity)"""
        try:
            current_ratio = self.info.get('currentRatio', None)

            if current_ratio is None and not self.balance_sheet.empty:
                current_assets = self._get_value(self.balance_sheet,
                    ['Total Current Assets', 'Current Assets'])
                current_liab = self._get_value(self.balance_sheet,
                    ['Total Current Liabilities', 'Current Liabilities'])
                if current_liab and current_liab > 0:
                    current_ratio = current_assets / current_liab

            if current_ratio is not None:
                if current_ratio >= FUNDAMENTAL_FILTERS['min_current_ratio']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Current Ratio: {current_ratio:.2f} (> {FUNDAMENTAL_FILTERS['min_current_ratio']})")
                else:
                    self.failed_checks.append(f"❌ Current Ratio: {current_ratio:.2f} (< {FUNDAMENTAL_FILTERS['min_current_ratio']})")
            else:
                self.failed_checks.append("⚠️ Current Ratio: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Current Ratio: Error - {e}")

    def _check_roe(self):
        """Check Return on Equity"""
        try:
            roe = self.info.get('returnOnEquity', None)

            if roe is not None:
                roe_pct = roe * 100 if roe < 1 else roe

                if roe_pct >= FUNDAMENTAL_FILTERS['min_roe']:
                    self.score += 1
                    self.passed_checks.append(f"✅ ROE: {roe_pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_roe']}%)")
                else:
                    self.failed_checks.append(f"❌ ROE: {roe_pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_roe']}%)")
            else:
                self.failed_checks.append("⚠️ ROE: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ ROE: Error - {e}")

    def _check_roa(self):
        """Check Return on Assets"""
        try:
            roa = self.info.get('returnOnAssets', None)

            if roa is not None:
                roa_pct = roa * 100 if roa < 1 else roa

                if roa_pct >= FUNDAMENTAL_FILTERS['min_roa']:
                    self.score += 1
                    self.passed_checks.append(f"✅ ROA: {roa_pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_roa']}%)")
                else:
                    self.failed_checks.append(f"❌ ROA: {roa_pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_roa']}%)")
            else:
                self.failed_checks.append("⚠️ ROA: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ ROA: Error - {e}")

    def _check_profit_margin(self):
        """Check Profit Margin"""
        try:
            margin = self.info.get('profitMargins', None)

            if margin is not None:
                margin_pct = margin * 100 if margin < 1 else margin

                if margin_pct >= FUNDAMENTAL_FILTERS['min_profit_margin']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Profit Margin: {margin_pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_profit_margin']}%)")
                else:
                    self.failed_checks.append(f"❌ Profit Margin: {margin_pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_profit_margin']}%)")
            else:
                self.failed_checks.append("⚠️ Profit Margin: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Profit Margin: Error - {e}")

    def _check_revenue_growth(self):
        """Check Revenue Growth"""
        try:
            revenue_growth = self.info.get('revenueGrowth', None)

            if revenue_growth is not None:
                growth_pct = revenue_growth * 100 if abs(revenue_growth) < 1 else revenue_growth

                if growth_pct >= FUNDAMENTAL_FILTERS['min_revenue_growth']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Revenue Growth: {growth_pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_revenue_growth']}%)")
                else:
                    self.failed_checks.append(f"❌ Revenue Growth: {growth_pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_revenue_growth']}%)")
            else:
                self.failed_checks.append("⚠️ Revenue Growth: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Revenue Growth: Error - {e}")

    def _check_eps_growth(self):
        """Check EPS Growth"""
        try:
            eps_growth = self.info.get('earningsGrowth', None)

            if eps_growth is not None:
                growth_pct = eps_growth * 100 if abs(eps_growth) < 1 else eps_growth

                if growth_pct >= FUNDAMENTAL_FILTERS['min_eps_growth']:
                    self.score += 1
                    self.passed_checks.append(f"✅ EPS Growth: {growth_pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_eps_growth']}%)")
                else:
                    self.failed_checks.append(f"❌ EPS Growth: {growth_pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_eps_growth']}%)")
            else:
                self.failed_checks.append("⚠️ EPS Growth: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ EPS Growth: Error - {e}")

    def _check_free_cash_flow(self):
        """Check Free Cash Flow"""
        try:
            fcf = self.info.get('freeCashflow', None)

            if fcf is not None:
                if fcf > 0:
                    self.score += 1
                    self.passed_checks.append(f"✅ Free Cash Flow: ₹{fcf/10000000:.0f} Cr (Positive)")
                else:
                    self.failed_checks.append(f"❌ Free Cash Flow: ₹{fcf/10000000:.0f} Cr (Negative)")
            else:
                # Try from cash flow statement
                if not self.cash_flow.empty:
                    operating_cf = self._get_value(self.cash_flow,
                        ['Operating Cash Flow', 'Total Cash From Operating Activities'])
                    capex = self._get_value(self.cash_flow,
                        ['Capital Expenditures', 'Capital Expenditure'])
                    if operating_cf is not None:
                        fcf = operating_cf - abs(capex or 0)
                        if fcf > 0:
                            self.score += 1
                            self.passed_checks.append(f"✅ Free Cash Flow: Positive")
                        else:
                            self.failed_checks.append(f"❌ Free Cash Flow: Negative")
                    else:
                        self.failed_checks.append("⚠️ Free Cash Flow: Data not available")
                else:
                    self.failed_checks.append("⚠️ Free Cash Flow: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Free Cash Flow: Error - {e}")

    def _check_promoter_holding(self):
        """Check Promoter Holding percentage"""
        try:
            # Yahoo doesn't have this directly, use heldPercentInsiders as proxy
            insider_pct = self.info.get('heldPercentInsiders', None)

            if insider_pct is not None:
                pct = insider_pct * 100 if insider_pct < 1 else insider_pct

                if pct >= FUNDAMENTAL_FILTERS['min_promoter_holding']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Insider Holding: {pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_promoter_holding']}%)")
                else:
                    self.failed_checks.append(f"❌ Insider Holding: {pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_promoter_holding']}%)")
            else:
                self.failed_checks.append("⚠️ Insider Holding: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Insider Holding: Error - {e}")

    def _check_institutional_holding(self):
        """Check Institutional Holding percentage"""
        try:
            inst_pct = self.info.get('heldPercentInstitutions', None)

            if inst_pct is not None:
                pct = inst_pct * 100 if inst_pct < 1 else inst_pct

                if pct >= FUNDAMENTAL_FILTERS['min_institutional_holding']:
                    self.score += 1
                    self.passed_checks.append(f"✅ Institutional Holding: {pct:.1f}% (> {FUNDAMENTAL_FILTERS['min_institutional_holding']}%)")
                else:
                    self.failed_checks.append(f"❌ Institutional Holding: {pct:.1f}% (< {FUNDAMENTAL_FILTERS['min_institutional_holding']}%)")
            else:
                self.failed_checks.append("⚠️ Institutional Holding: Data not available")

        except Exception as e:
            self.failed_checks.append(f"⚠️ Institutional Holding: Error - {e}")

    def _get_value(self, df, possible_names):
        """Get value from DataFrame trying multiple possible column/row names"""
        if df is None or df.empty:
            return None

        for name in possible_names:
            try:
                if name in df.index:
                    val = df.loc[name].iloc[0]  # Most recent
                    if pd.notna(val):
                        return float(val)
            except Exception:
                continue
        return None

    def _generate_report(self):
        """Generate analysis report"""
        pass_rate = (self.score / self.max_score) * 100
        
        # Determine grade
        if pass_rate >= 80:
            grade = "A"
            recommendation = "EXCELLENT — Strong fundamentals"
        elif pass_rate >= 60:
            grade = "B"
            recommendation = "GOOD — Acceptable for trading"
        elif pass_rate >= 40:
            grade = "C"
            recommendation = "AVERAGE — Trade with caution"
        else:
            grade = "D"
            recommendation = "POOR — Avoid trading"

        is_tradeable = pass_rate >= FUNDAMENTAL_FILTERS['min_score_to_trade']

        report = {
            'ticker': self.ticker,
            'score': self.score,
            'max_score': self.max_score,
            'pass_rate': pass_rate,
            'grade': grade,
            'recommendation': recommendation,
            'is_tradeable': is_tradeable,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'company_name': self.info.get('shortName', self.ticker),
            'sector': self.info.get('sector', 'Unknown'),
            'industry': self.info.get('industry', 'Unknown'),
            'market_cap': self.info.get('marketCap', 0),
            'pe_ratio': self.info.get('trailingPE', 0),
            'pb_ratio': self.info.get('priceToBook', 0),
            'dividend_yield': self.info.get('dividendYield', 0),
            'timestamp': datetime.now().isoformat()
        }

        return report

    def print_report(self):
        """Print formatted report"""
        report = self.analyze()

        print(f"\n{'='*60}")
        print(f"📊 FUNDAMENTAL ANALYSIS — {report['ticker']}")
        print(f"   {report['company_name']}")
        print(f"   Sector: {report['sector']} | Industry: {report['industry']}")
        print(f"{'='*60}")

        print(f"\n   SCORE: {report['score']}/{report['max_score']} ({report['pass_rate']:.0f}%)")
        print(f"   GRADE: {report['grade']}")
        print(f"   {report['recommendation']}")

        if report['is_tradeable']:
            print(f"   ✅ TRADEABLE")
        else:
            print(f"   ❌ NOT TRADEABLE")

        print(f"\n   KEY METRICS:")
        print(f"     Market Cap:    ₹{report['market_cap']/10000000:,.0f} Cr")
        print(f"     P/E Ratio:     {report['pe_ratio']:.2f}" if report['pe_ratio'] else "     P/E Ratio:     N/A")
        print(f"     P/B Ratio:     {report['pb_ratio']:.2f}" if report['pb_ratio'] else "     P/B Ratio:     N/A")
        if report['dividend_yield']:
            print(f"     Dividend:      {report['dividend_yield']*100:.2f}%")

        print(f"\n   PASSED CHECKS ({len(report['passed_checks'])}):")
        for check in report['passed_checks']:
            print(f"     {check}")

        print(f"\n   FAILED CHECKS ({len(report['failed_checks'])}):")
        for check in report['failed_checks']:
            print(f"     {check}")

        print(f"{'='*60}\n")

        return report


def scan_fundamentals(tickers=None):
    """Scan multiple stocks for fundamental strength"""
    from config.settings import TICKERS
    
    if tickers is None:
        tickers = TICKERS

    print(f"\n📊 FUNDAMENTAL SCAN — {len(tickers)} stocks\n")

    results = []

    for ticker in tickers:
        try:
            analyzer = FundamentalAnalyzer(ticker)
            report = analyzer.analyze()
            results.append(report)

            emoji = "✅" if report['is_tradeable'] else "❌"
            print(f"{emoji} {ticker:15s} | Grade: {report['grade']} | "
                  f"Score: {report['score']}/{report['max_score']} | "
                  f"{report['recommendation'][:30]}")

        except Exception as e:
            print(f"❌ {ticker:15s} | Error: {e}")

    # Summary
    tradeable = [r for r in results if r['is_tradeable']]
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY: {len(tradeable)}/{len(results)} stocks are tradeable")
    print(f"{'='*60}")

    if tradeable:
        print(f"\n🏆 TRADEABLE STOCKS (Strong Fundamentals):")
        for r in sorted(tradeable, key=lambda x: x['score'], reverse=True):
            print(f"   {r['ticker']:15s} | Grade {r['grade']} | {r['company_name'][:25]}")

    return results
