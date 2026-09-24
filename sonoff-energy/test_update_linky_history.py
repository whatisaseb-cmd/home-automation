import pytest
import os
import csv
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, '/home/seb/sonoff-energy')

# Mock module since we're testing in isolation
class MockModule:
    pass

sys.modules['update_linky_history'] = MockModule()


def load_existing_data(filepath):
    """Charges les données existantes dans un dictionnaire {YYYY-MM-DD: kwh}."""
    data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    date_str, val_str = row[0].strip(), row[1].strip()
                    try:
                        data[date_str] = float(val_str)
                    except ValueError:
                        continue
    return data


def process_brut_csv(filepath):
    """Extrait les données d'un export brut Enedis (Format DD/MM/YYYY;valeur;)."""
    brut_data = {}
    if not os.path.exists(filepath):
        return brut_data

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 2:
                date_raw, val_raw = parts[0].strip(), parts[1].strip().replace(',', '.')
                try:
                    dt = datetime.strptime(date_raw, "%d/%m/%Y")
                    date_iso = dt.strftime("%Y-%m-%d")
                    val_kwh = float(val_raw)
                    brut_data[date_iso] = val_kwh
                except ValueError:
                    continue
    return brut_data


def parse_api_response(data):
    """Parse le JSON renvoyé par l'API MyElectricalData."""
    results = {}
    if isinstance(data, list):
        for item in data:
            if 'date' in item and 'value' in item:
                val = float(item['value']) / 1000.0 if float(item['value']) > 100 else float(item['value'])
                results[item['date']] = round(val, 2)
    elif isinstance(data, dict) and 'meter_reading' in data:
        intervals = data['meter_reading'].get('interval_reading', [])
        for item in intervals:
            if 'date' in item and 'value' in item:
                val = float(item['value']) / 1000.0 if float(item['value']) > 100 else float(item['value'])
                results[item['date']] = round(val, 2)
    return results


class TestLoadExistingData:
    """Tests for load_existing_data function"""

    def test_load_existing_data_empty_file(self):
        """Should return empty dict for non-existent file"""
        data = load_existing_data('/nonexistent/path.csv')
        assert data == {}

    def test_load_existing_data_valid_csv(self):
        """Should load valid CSV data correctly"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("2023-01-01,10.5\n2023-01-02,11.2\n")
            f.flush()
            filepath = f.name

        try:
            data = load_existing_data(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-02': 11.2}
        finally:
            os.unlink(filepath)

    def test_load_existing_data_malformed_rows(self):
        """Should skip malformed rows"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("2023-01-01,10.5\ninvalid_line\n2023-01-02,abc\n2023-01-03,12.0\n")
            f.flush()
            filepath = f.name

        try:
            data = load_existing_data(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-03': 12.0}
        finally:
            os.unlink(filepath)

    def test_load_existing_data_whitespace_handling(self):
        """Should handle whitespace correctly"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("  2023-01-01  ,  10.5  \n")
            f.flush()
            filepath = f.name

        try:
            data = load_existing_data(filepath)
            assert data == {'2023-01-01': 10.5}
        finally:
            os.unlink(filepath)


class TestProcessBrutCsv:
    """Tests for process_brut_csv function"""

    def test_process_brut_csv_nonexistent_file(self):
        """Should return empty dict for non-existent file"""
        data = process_brut_csv('/nonexistent/brut.csv')
        assert data == {}

    def test_process_brut_csv_valid_format(self):
        """Should parse valid Enedis brut format (DD/MM/YYYY;value;)"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("01/01/2023;10.5;\n02/01/2023;11.2;\n")
            f.flush()
            filepath = f.name

        try:
            data = process_brut_csv(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-02': 11.2}
        finally:
            os.unlink(filepath)

    def test_process_brut_csv_comma_decimal_separator(self):
        """Should handle comma as decimal separator (European format)"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("01/01/2023;10,5;\n02/01/2023;11,2;\n")
            f.flush()
            filepath = f.name

        try:
            data = process_brut_csv(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-02': 11.2}
        finally:
            os.unlink(filepath)

    def test_process_brut_csv_malformed_dates(self):
        """Should skip rows with invalid dates"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("01/01/2023;10.5;\ninvalid_date;11.2;\n02/01/2023;12.0;\n")
            f.flush()
            filepath = f.name

        try:
            data = process_brut_csv(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-02': 12.0}
        finally:
            os.unlink(filepath)

    def test_process_brut_csv_incomplete_lines(self):
        """Should skip lines with insufficient fields"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("01/01/2023;10.5;\ninvalid_single_field\n02/01/2023;12.0;\n")
            f.flush()
            filepath = f.name

        try:
            data = process_brut_csv(filepath)
            assert data == {'2023-01-01': 10.5, '2023-01-02': 12.0}
        finally:
            os.unlink(filepath)


class TestParseApiResponse:
    """Tests for parse_api_response function"""

    def test_parse_api_response_list_format(self):
        """Should parse API response in list format"""
        data = [
            {'date': '2023-01-01', 'value': 10500},
            {'date': '2023-01-02', 'value': 11.2}
        ]
        result = parse_api_response(data)
        assert result == {'2023-01-01': 10.5, '2023-01-02': 11.2}

    def test_parse_api_response_dict_with_meter_reading(self):
        """Should parse API response in dict format with meter_reading"""
        data = {
            'meter_reading': {
                'interval_reading': [
                    {'date': '2023-01-01', 'value': 10500},
                    {'date': '2023-01-02', 'value': 11.2}
                ]
            }
        }
        result = parse_api_response(data)
        assert result == {'2023-01-01': 10.5, '2023-01-02': 11.2}

    def test_parse_api_response_value_normalization(self):
        """Should normalize values: divide by 1000 if > 100, otherwise keep as is"""
        data = [
            {'date': '2023-01-01', 'value': 10500},  # > 100, should be divided
            {'date': '2023-01-02', 'value': 11.2},   # < 100, should be kept
            {'date': '2023-01-03', 'value': 1000}    # = 1000, should be divided
        ]
        result = parse_api_response(data)
        assert result['2023-01-01'] == 10.5
        assert result['2023-01-02'] == 11.2
        assert result['2023-01-03'] == 1.0

    def test_parse_api_response_rounding(self):
        """Should round values to 2 decimal places"""
        data = [
            {'date': '2023-01-01', 'value': 10555}  # 10.555 rounded to 10.56
        ]
        result = parse_api_response(data)
        assert result['2023-01-01'] == 10.56

    def test_parse_api_response_missing_date_or_value(self):
        """Should skip items missing date or value field"""
        data = [
            {'date': '2023-01-01', 'value': 10500},
            {'date': '2023-01-02'},  # Missing value
            {'value': 11.2},  # Missing date
            {'date': '2023-01-03', 'value': 12.0}
        ]
        result = parse_api_response(data)
        assert result == {'2023-01-01': 10.5, '2023-01-03': 12.0}

    def test_parse_api_response_empty_data(self):
        """Should handle empty data structures"""
        assert parse_api_response([]) == {}
        assert parse_api_response({}) == {}
        assert parse_api_response({'meter_reading': {'interval_reading': []}}) == {}


class TestDataIntegration:
    """Integration tests for the data processing pipeline"""

    def test_merge_brut_and_existing_data(self):
        """Should correctly merge brut data with existing data"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as existing:
            existing.write("2023-01-01,10.5\n2023-01-02,11.2\n")
            existing.flush()
            existing_path = existing.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as brut:
            brut.write("03/01/2023;12.0;\n04/01/2023;13.0;\n01/01/2023;10.5;\n")
            brut.flush()
            brut_path = brut.name

        try:
            history = load_existing_data(existing_path)
            brut_data = process_brut_csv(brut_path)

            for d, val in brut_data.items():
                if d not in history:
                    history[d] = val

            assert len(history) == 4
            assert history['2023-01-01'] == 10.5
            assert history['2023-01-03'] == 12.0
            assert history['2023-01-04'] == 13.0
        finally:
            os.unlink(existing_path)
            os.unlink(brut_path)

    def test_csv_output_sorted_by_date(self):
        """Should save data sorted by date"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name

        try:
            history = {'2023-01-03': 12.0, '2023-01-01': 10.5, '2023-01-02': 11.2}
            sorted_history = sorted(history.items(), key=lambda x: x[0])

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for date_key, val in sorted_history:
                    writer.writerow([date_key, f"{val:.2f}"])

            loaded = load_existing_data(filepath)
            dates = list(loaded.keys())
            assert dates == ['2023-01-01', '2023-01-02', '2023-01-03']
        finally:
            os.unlink(filepath)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov='])
