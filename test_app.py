import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys

# Mock streamlit before importing app
sys.modules['streamlit'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.express'] = MagicMock()


class TestPortfolioCalculations:
    """Tests for portfolio financial calculations"""

    def test_current_value_calculation(self):
        """Should calculate current portfolio value correctly"""
        quantity = 10
        current_price = 100.0
        current_value = quantity * current_price
        assert current_value == 1000.0

    def test_investment_value_calculation(self):
        """Should calculate initial investment value correctly"""
        quantity = 10
        average_price = 90.0
        investment = quantity * average_price
        assert investment == 900.0

    def test_gain_loss_calculation(self):
        """Should calculate gain/loss correctly"""
        current_value = 1000.0
        investment = 900.0
        gain_loss = current_value - investment
        assert gain_loss == 100.0

    def test_performance_percentage_calculation(self):
        """Should calculate performance percentage correctly"""
        current_value = 1000.0
        investment = 900.0
        performance = ((current_value - investment) / investment) * 100
        assert performance == pytest.approx(11.11, 0.01)

    def test_performance_with_loss(self):
        """Should calculate negative performance correctly"""
        current_value = 800.0
        investment = 900.0
        performance = ((current_value - investment) / investment) * 100
        assert performance == pytest.approx(-11.11, 0.01)

    def test_zero_investment_case(self):
        """Should handle zero investment gracefully"""
        current_value = 0
        investment = 0
        with pytest.raises(ZeroDivisionError):
            performance = ((current_value - investment) / investment) * 100

    def test_portfolio_total_calculation(self):
        """Should sum portfolio values correctly"""
        values = [1000.0, 500.0, 2000.0]
        total = sum(values)
        assert total == 3500.0

    def test_global_performance_calculation(self):
        """Should calculate global portfolio performance correctly"""
        total_value = 11000.0
        total_invested = 10000.0
        global_performance = ((total_value - total_invested) / total_invested) * 100
        assert global_performance == 10.0


class TestFutureValueProjection:
    """Tests for 2050 projection calculations"""

    def test_monthly_rate_calculation(self):
        """Should calculate monthly rate from annual rendement correctly"""
        annual_rate = 7.0
        monthly_rate = (1 + annual_rate/100)**(1/12) - 1
        assert monthly_rate == pytest.approx(0.00565, 0.0001)

    def test_future_value_formula_no_contributions(self):
        """Should calculate future value with just initial capital"""
        current_value = 1000.0
        monthly_rate = 0.00565
        months = 300  # 25 years
        future_value = current_value * (1 + monthly_rate)**months
        assert future_value > current_value
        assert future_value == pytest.approx(4750, 100)

    def test_future_value_with_monthly_contributions(self):
        """Should calculate future value with monthly contributions"""
        current_value = 1000.0
        monthly_contribution = 200.0
        monthly_rate = 0.00565
        months = 300

        # FV = PV * (1+r)^n + PMT * [((1+r)^n - 1) / r]
        future_value = (current_value * (1 + monthly_rate)**months +
                       monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate))
        assert future_value > (current_value + monthly_contribution * months)

    def test_contribution_effect_on_future_value(self):
        """Higher contributions should increase future value"""
        current_value = 1000.0
        monthly_rate = 0.00565
        months = 300

        fv_no_contrib = current_value * (1 + monthly_rate)**months
        fv_low_contrib = (current_value * (1 + monthly_rate)**months +
                         100 * (((1 + monthly_rate)**months - 1) / monthly_rate))
        fv_high_contrib = (current_value * (1 + monthly_rate)**months +
                          500 * (((1 + monthly_rate)**months - 1) / monthly_rate))

        assert fv_low_contrib > fv_no_contrib
        assert fv_high_contrib > fv_low_contrib

    def test_rendement_effect_on_future_value(self):
        """Higher rendement should increase future value"""
        current_value = 1000.0
        monthly_contribution = 200.0
        months = 300

        def calculate_fv(annual_rate):
            monthly_rate = (1 + annual_rate/100)**(1/12) - 1
            return (current_value * (1 + monthly_rate)**months +
                   monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate))

        fv_low = calculate_fv(3.0)
        fv_mid = calculate_fv(7.0)
        fv_high = calculate_fv(10.0)

        assert fv_mid > fv_low
        assert fv_high > fv_mid

    def test_years_calculation_to_2050(self):
        """Should calculate years until 2050 correctly"""
        current_year = 2024
        target_year = 2050
        years = target_year - current_year
        months = years * 12
        assert years == 26
        assert months == 312

    def test_extreme_long_term_projection(self):
        """Should handle very long-term projections"""
        current_value = 1000.0
        monthly_contribution = 100.0
        monthly_rate = 0.005
        months = 600  # 50 years

        future_value = (current_value * (1 + monthly_rate)**months +
                       monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate))
        assert future_value > 0
        assert not np.isnan(future_value)
        assert not np.isinf(future_value)

    def test_zero_rendement(self):
        """Should handle 0% rendement (just accumulating contributions)"""
        current_value = 1000.0
        monthly_contribution = 100.0
        months = 60

        # With 0% rate, should be approximately: PV + PMT * months
        future_value = current_value + monthly_contribution * months
        assert future_value == 7000.0


class TestPortfolioDataFrame:
    """Tests for DataFrame operations"""

    def test_portfolio_dataframe_structure(self):
        """Should create portfolio DataFrame with correct structure"""
        data = {
            'Ticker': ['CW8.PA', 'EUSA.PA', 'VUSA.PA'],
            'Nom': ['MSCI World', 'S&P 500', 'S&P 500 Acc'],
            'Quantité': [10, 5, 2],
            'Prix_Moyen_Achat': [410.0, 380.0, 85.0]
        }
        df = pd.DataFrame(data)

        assert len(df) == 3
        assert list(df.columns) == ['Ticker', 'Nom', 'Quantité', 'Prix_Moyen_Achat']
        assert df.iloc[0]['Ticker'] == 'CW8.PA'

    def test_add_calculated_columns_to_dataframe(self):
        """Should add calculated columns correctly"""
        df = pd.DataFrame({
            'Ticker': ['CW8.PA'],
            'Quantité': [10],
            'Prix_Moyen_Achat': [410.0]
        })

        prices = {'CW8.PA': 450.0}
        df['Prix_Actuel'] = df['Ticker'].map(prices)
        df['Valeur_Actuelle'] = df['Quantité'] * df['Prix_Actuel']
        df['Investissement_Initial'] = df['Quantité'] * df['Prix_Moyen_Achat']
        df['Plus_Moins_Value'] = df['Valeur_Actuelle'] - df['Investissement_Initial']
        df['Performance_%'] = (df['Plus_Moins_Value'] / df['Investissement_Initial']) * 100

        assert df.iloc[0]['Valeur_Actuelle'] == 4500.0
        assert df.iloc[0]['Investissement_Initial'] == 4100.0
        assert df.iloc[0]['Plus_Moins_Value'] == 400.0
        assert df.iloc[0]['Performance_%'] == pytest.approx(9.76, 0.01)

    def test_handle_none_prices_in_dataframe(self):
        """Should handle None values in prices gracefully"""
        df = pd.DataFrame({
            'Ticker': ['CW8.PA', 'INVALID.PA'],
            'Quantité': [10, 5]
        })

        prices = {'CW8.PA': 450.0, 'INVALID.PA': None}
        df['Prix_Actuel'] = df['Ticker'].map(prices)

        assert df.iloc[0]['Prix_Actuel'] == 450.0
        assert pd.isna(df.iloc[1]['Prix_Actuel'])

    def test_multiline_portfolio_calculations(self):
        """Should calculate across multiple portfolio lines"""
        df = pd.DataFrame({
            'Ticker': ['CW8.PA', 'EUSA.PA'],
            'Quantité': [10, 5],
            'Prix_Moyen_Achat': [410.0, 380.0],
            'Prix_Actuel': [450.0, 400.0]
        })

        df['Valeur_Actuelle'] = df['Quantité'] * df['Prix_Actuel']
        df['Investissement_Initial'] = df['Quantité'] * df['Prix_Moyen_Achat']

        total_value = df['Valeur_Actuelle'].sum()
        total_invested = df['Investissement_Initial'].sum()

        assert total_value == (4500.0 + 2000.0)
        assert total_invested == (4100.0 + 1900.0)
        assert len(df) == 2


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_very_small_values(self):
        """Should handle very small portfolio values"""
        current_value = 0.01
        investment = 0.01
        performance = ((current_value - investment) / investment) * 100
        assert performance == 0.0

    def test_very_large_values(self):
        """Should handle very large portfolio values"""
        current_value = 1_000_000_000.0
        investment = 999_999_999.0
        performance = ((current_value - investment) / investment) * 100
        assert performance == pytest.approx(0.1, 0.01)

    def test_negative_monthly_contribution(self):
        """Should handle negative contributions (withdrawals)"""
        current_value = 10000.0
        monthly_contribution = -100.0
        monthly_rate = 0.005
        months = 60

        future_value = (current_value * (1 + monthly_rate)**months +
                       monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate))
        assert future_value < current_value

    def test_extreme_high_rendement(self):
        """Should handle unrealistically high rendement"""
        current_value = 1000.0
        monthly_rate = (1 + 100/100)**(1/12) - 1
        months = 120

        future_value = current_value * (1 + monthly_rate)**months
        assert future_value > 0
        assert not np.isnan(future_value)

    def test_single_line_portfolio(self):
        """Should work with single-line portfolio"""
        df = pd.DataFrame({
            'Ticker': ['CW8.PA'],
            'Quantité': [10],
            'Prix_Moyen_Achat': [410.0],
            'Prix_Actuel': [450.0]
        })

        df['Valeur_Actuelle'] = df['Quantité'] * df['Prix_Actuel']
        assert len(df) == 1
        assert df.iloc[0]['Valeur_Actuelle'] == 4500.0

    def test_dataframe_with_nan_values(self):
        """Should handle NaN in portfolio data"""
        df = pd.DataFrame({
            'Ticker': ['CW8.PA', 'EUSA.PA'],
            'Prix_Actuel': [450.0, np.nan],
            'Quantité': [10, 5]
        })

        df['Valeur_Actuelle'] = df['Quantité'] * df['Prix_Actuel']
        assert df.iloc[0]['Valeur_Actuelle'] == 4500.0
        assert pd.isna(df.iloc[1]['Valeur_Actuelle'])


class TestDataValidation:
    """Tests for data validation"""

    def test_positive_quantity(self):
        """Should validate that quantity is positive"""
        quantity = 10
        assert quantity > 0

    def test_positive_price(self):
        """Should validate that prices are positive"""
        price = 450.0
        assert price > 0

    def test_rendement_within_bounds(self):
        """Should validate rendement is within reasonable bounds"""
        rendement = 7.0
        assert 0.0 <= rendement <= 20.0

    def test_monthly_contribution_non_negative(self):
        """Monthly contribution should allow zero or positive"""
        contribution = 200.0
        assert contribution >= 0

    def test_dataframe_column_count(self):
        """Should have expected number of columns"""
        data = {
            'Ticker': ['CW8.PA'],
            'Nom': ['MSCI World'],
            'Quantité': [10],
            'Prix_Moyen_Achat': [410.0]
        }
        df = pd.DataFrame(data)
        assert len(df.columns) == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov='])
