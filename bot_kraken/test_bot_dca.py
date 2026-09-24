"""
Tests unitaires pour bot_dca.py
Teste les fonctions critiques de trading DCA avec mock des APIs externes
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Mock les variables d'env avant l'import
os.environ.setdefault('TELEGRAM_TOKEN', 'test_token')
os.environ.setdefault('TELEGRAM_CHAT_ID', '12345')
os.environ.setdefault('API_KEY', 'test_key')
os.environ.setdefault('API_SECRET', 'test_secret')

# Importer après config env
sys.path.insert(0, '/home/seb/bot_kraken')
from bot_dca import (
    analyser_tendance,
    validate_env_vars,
    envoyer_telegram,
    executer_achat_smart_dca,
    MONTANT_BULL,
    MONTANT_BEAR
)


class TestValidateEnvVars:
    """Tests de validation des variables d'environnement"""

    def test_env_vars_présentes(self):
        """Test que les env vars requises sont présentes"""
        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token123',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key789',
            'API_SECRET': 'secret012'
        }):
            # Ne doit pas lever d'exception
            validate_env_vars()

    def test_env_vars_manquantes(self):
        """Test que le script détecte les env vars manquantes"""
        with patch.dict(os.environ, {'TELEGRAM_TOKEN': ''}, clear=False):
            with pytest.raises(ValueError, match="Missing env vars"):
                validate_env_vars()

    def test_env_vars_partiellement_manquantes(self):
        """Test si une seule env var manque"""
        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '',  # Manquante
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            with pytest.raises(ValueError):
                validate_env_vars()


class TestAnalyseTendance:
    """Tests du calcul de tendance SMA"""

    def create_mock_ohlcv(self, prices):
        """Créer des données OHLCV mock"""
        data = []
        for i, price in enumerate(prices):
            data.append([
                i * 86400000,  # timestamp
                price * 0.99,  # open
                price * 1.01,  # high
                price * 0.98,  # low
                price,         # close
                1000           # volume
            ])
        return data

    def test_sma_200_correct(self):
        """Test que la SMA 200 est calculée correctement"""
        mock_kraken = Mock()

        # Données: 200 prix qui augmentent doucement
        prices = list(range(100, 300))  # 100 à 299
        mock_kraken.fetch_ohlcv.return_value = self.create_mock_ohlcv(prices)

        est_haussier, prix_actuel, sma_200, tendance = analyser_tendance(mock_kraken, 'BTC/EUR')

        # Vérifications
        assert bool(est_haussier) is True, "Tendance devrait être haussière"
        assert prix_actuel == 299, f"Prix actuel devrait être 299, got {prix_actuel}"
        assert 190 < sma_200 < 210, f"SMA 200 devrait être ~200, got {sma_200}"
        assert "HAUSSIÈRE" in tendance
        assert "🚀" in tendance

    def test_tendance_baissiere(self):
        """Test une tendance baissière"""
        mock_kraken = Mock()

        # Données: 200 prix qui diminuent
        prices = list(range(300, 100, -1))  # 300 à 101
        mock_kraken.fetch_ohlcv.return_value = self.create_mock_ohlcv(prices)

        est_haussier, prix_actuel, sma_200, tendance = analyser_tendance(mock_kraken, 'BTC/EUR')

        assert bool(est_haussier) is False, "Tendance devrait être baissière"
        assert prix_actuel == 101
        assert "BAISSIÈRE" in tendance
        assert "📉" in tendance

    def test_sma_prix_egal(self):
        """Test quand le prix == SMA (cas limite)"""
        mock_kraken = Mock()

        # Tous les prix identiques
        prices = [200] * 200
        mock_kraken.fetch_ohlcv.return_value = self.create_mock_ohlcv(prices)

        est_haussier, prix_actuel, sma_200, tendance = analyser_tendance(mock_kraken, 'BTC/EUR')

        assert bool(est_haussier) is False, "Prix == SMA devrait être baissier (not >)"
        assert prix_actuel == sma_200
        assert abs(prix_actuel - 200) < 0.01

    def test_erreur_api_kraken(self):
        """Test gestion d'erreur si l'API Kraken crash"""
        mock_kraken = Mock()
        mock_kraken.fetch_ohlcv.side_effect = Exception("API Error: Rate limit exceeded")

        est_haussier, prix_actuel, sma_200, tendance = analyser_tendance(mock_kraken, 'BTC/EUR')

        assert est_haussier is None, "Devrait retourner None en cas d'erreur"
        assert prix_actuel is None
        assert sma_200 is None
        assert tendance == "ERREUR"

    def test_insufficient_data(self):
        """Test si on a moins de 200 bougies"""
        mock_kraken = Mock()

        # Seulement 50 bougies
        prices = list(range(100, 150))
        mock_kraken.fetch_ohlcv.return_value = self.create_mock_ohlcv(prices)

        est_haussier, prix_actuel, sma_200, tendance = analyser_tendance(mock_kraken, 'BTC/EUR')

        # SMA retourne NaN si pas assez de données
        assert est_haussier is None or pd.isna(sma_200)
        assert tendance == "ERREUR"


class TestEnvoyerTelegram:
    """Tests de l'envoi Telegram"""

    @patch('requests.post')
    def test_telegram_success(self, mock_post):
        """Test que le message est envoyé correctement"""
        mock_post.return_value.status_code = 200

        with patch.dict(os.environ, {'TELEGRAM_TOKEN': 'token123', 'TELEGRAM_CHAT_ID': '456'}):
            envoyer_telegram("Test message")

        # Vérifier que POST a été appelé
        assert mock_post.called
        call_args = mock_post.call_args

        # Vérifier l'URL
        assert 'api.telegram.org' in call_args[0][0]
        assert 'token123' in call_args[0][0]

        # Vérifier le payload
        payload = call_args[1]['json']
        assert payload['chat_id'] == '456'
        assert payload['text'] == "Test message"

    @patch('requests.post')
    def test_telegram_timeout(self, mock_post):
        """Test gestion du timeout Telegram"""
        import requests
        mock_post.side_effect = requests.RequestException("Connection timeout")

        with patch.dict(os.environ, {'TELEGRAM_TOKEN': 'token123', 'TELEGRAM_CHAT_ID': '456'}):
            # Ne doit pas lever d'exception
            envoyer_telegram("Test")

    def test_telegram_config_manquante(self):
        """Test si les credentials Telegram manquent"""
        with patch.dict(os.environ, {'TELEGRAM_TOKEN': '', 'TELEGRAM_CHAT_ID': ''}, clear=False):
            # Ne doit pas crash
            envoyer_telegram("Test")


class TestExecuterAchat:
    """Tests du flow d'achat complet"""

    @patch('bot_dca.envoyer_telegram')
    @patch('bot_dca.analyser_tendance')
    def test_achat_bull(self, mock_analyse, mock_telegram):
        """Test achat en tendance haussière"""
        mock_kraken = Mock()
        mock_kraken.create_market_buy_order.return_value = {'id': '123456'}

        # Tendance haussière
        mock_analyse.return_value = (True, 45000.0, 40000.0, "HAUSSIÈRE 🚀")

        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            with patch('ccxt.kraken', return_value=mock_kraken):
                executer_achat_smart_dca()

        # Vérifier que l'achat a été exécuté
        assert mock_kraken.create_market_buy_order.called
        call_args = mock_kraken.create_market_buy_order.call_args[0]

        # Montant BULL = 12€
        volume_attendu = MONTANT_BULL / 45000.0
        assert abs(call_args[1] - volume_attendu) < 0.0001

    @patch('bot_dca.envoyer_telegram')
    @patch('bot_dca.analyser_tendance')
    def test_achat_bear_pause(self, mock_analyse, mock_telegram):
        """Test pause d'achat en tendance baissière (si MONTANT_BEAR=0)"""
        mock_kraken = Mock()

        # Tendance baissière
        mock_analyse.return_value = (False, 40000.0, 45000.0, "BAISSIÈRE 📉")

        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            with patch('ccxt.kraken', return_value=mock_kraken):
                executer_achat_smart_dca()

        # Vérifier que Telegram a été appelé
        assert mock_telegram.called

        # Si MONTANT_BEAR > 0, achat devrait être exécuté
        if MONTANT_BEAR > 0:
            assert mock_kraken.create_market_buy_order.called
        else:
            assert not mock_kraken.create_market_buy_order.called

    @patch('bot_dca.envoyer_telegram')
    @patch('bot_dca.analyser_tendance')
    def test_insufficient_funds(self, mock_analyse, mock_telegram):
        """Test gestion erreur fonds insuffisants"""
        import ccxt

        mock_kraken = Mock()
        mock_kraken.create_market_buy_order.side_effect = ccxt.InsufficientFunds("Not enough funds")

        mock_analyse.return_value = (True, 45000.0, 40000.0, "HAUSSIÈRE 🚀")

        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            with patch('ccxt.kraken', return_value=mock_kraken):
                executer_achat_smart_dca()

        # Vérifier que l'erreur a été signalée via Telegram
        assert mock_telegram.called
        call_args = mock_telegram.call_args[0][0]
        assert "Fonds insuffisants" in call_args or "⚠️" in call_args

    @patch('bot_dca.envoyer_telegram')
    @patch('bot_dca.analyser_tendance')
    def test_analyse_erreur(self, mock_analyse, mock_telegram):
        """Test si l'analyse échoue"""
        mock_kraken = Mock()

        # L'analyse retourne une erreur
        mock_analyse.return_value = (None, None, None, "ERREUR")

        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            with patch('ccxt.kraken', return_value=mock_kraken):
                executer_achat_smart_dca()

        # Ne doit pas faire d'achat
        assert not mock_kraken.create_market_buy_order.called

        # Doit alerter via Telegram
        assert mock_telegram.called
        call_args = mock_telegram.call_args[0][0]
        assert "Impossible" in call_args or "❌" in call_args


class TestIntegration:
    """Tests d'intégration (flow complet)"""

    @patch('bot_dca.envoyer_telegram')
    @patch('ccxt.kraken')
    def test_flow_complet_achat_reussi(self, mock_kraken_class, mock_telegram):
        """Test le flow complet: analyse + décision + achat"""
        # Setup mock Kraken
        mock_kraken = Mock()
        mock_kraken_class.return_value = mock_kraken

        # Mock des données OHLCV
        prices = list(range(40000, 40200))  # Prix augmente
        ohlcv_data = []
        for i, p in enumerate(prices):
            ohlcv_data.append([i*86400000, p*0.99, p*1.01, p*0.98, p, 1000])

        mock_kraken.fetch_ohlcv.return_value = ohlcv_data
        mock_kraken.create_market_buy_order.return_value = {'id': 'order123'}

        with patch.dict(os.environ, {
            'TELEGRAM_TOKEN': 'token',
            'TELEGRAM_CHAT_ID': '456',
            'API_KEY': 'key',
            'API_SECRET': 'secret'
        }):
            executer_achat_smart_dca()

        # Vérifications
        assert mock_kraken.fetch_ohlcv.called, "Devrait fetcher les données"
        assert mock_kraken.create_market_buy_order.called, "Devrait faire un achat"
        assert mock_telegram.called, "Devrait envoyer un message Telegram"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
