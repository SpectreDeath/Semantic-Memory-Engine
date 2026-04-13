import base64
import io
import json
import logging
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from pyod.models.iforest import IForest

from extensions.ext_financial_forensics.financial_utils import (
    AlertRule,
    analyze_multi_asset,
    calculate_benfords_law_score,
    calculate_wallet_risk_score,
    create_default_alert_rules,
    detect_time_series_anomalies,
    eval_fraud_triangle,
    evaluate_alert_rules,
    perform_sequence_analysis,
)
from src.core.events import Event, EventType, get_event_bus
from src.core.plugin_base import BasePlugin

logger = logging.getLogger("SME.FinancialForensics")

DEFAULT_BENFORD_THRESHOLD = 0.1
DEFAULT_CONTAMINATION = 0.1
DEFAULT_Z_THRESHOLD = 3.0


class FinancialForensicsExtension(BasePlugin):
    """
    Financial Forensics Layer for SME.
    Handles transaction analysis, on-chain forensics, and behavior profiling.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.event_bus = get_event_bus()
        self._load_config(manifest)

    def _load_config(self, manifest: dict[str, Any]) -> None:
        """Load configuration from manifest."""
        config = manifest.get("config", {})
        self.benford_threshold = config.get("benford_threshold", DEFAULT_BENFORD_THRESHOLD)
        self.contamination = config.get("contamination", DEFAULT_CONTAMINATION)
        self.z_threshold = config.get("z_threshold", DEFAULT_Z_THRESHOLD)
        self.time_window = config.get("time_window", 10)
        self.alert_rules = create_default_alert_rules()

    async def on_startup(self):
        """Initialize database tables for transactions."""
        self.dal.create_table(
            "financial_transactions",
            {
                "id": "PRIMARY_KEY",
                "timestamp": "DATETIME",
                "source_wallet": "STRING",
                "target_wallet": "STRING",
                "amount": "FLOAT",
                "asset_type": "STRING",
                "metadata": "TEXT",
            },
        )

        self.dal.create_table(
            "forensic_anomalies",
            {
                "id": "PRIMARY_KEY",
                "transaction_id": "INTEGER",
                "anomaly_type": "STRING",
                "confidence_score": "FLOAT",
                "description": "TEXT",
                "detected_at": "DATETIME",
            },
        )

        logger.info(f"[{self.plugin_id}] Financial Forensics tables initialized.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Screen ingested data for transaction patterns."""
        try:
            data = json.loads(raw_data)
            if isinstance(data, list) and len(data) > 0 and "source_wallet" in data[0]:
                df = pd.DataFrame(data)

                benford_score = calculate_benfords_law_score(df["amount"].tolist())

                if benford_score > self.benford_threshold:
                    logger.warning(
                        f"[{self.plugin_id}] High Benford deviation detected: {benford_score:.4f}"
                    )

                alert_context = {
                    "benford_score": benford_score,
                    "transaction_count": len(df),
                }
                if "asset_type" in df.columns:
                    alert_context["asset_types"] = df["asset_type"].unique().tolist()
                triggered_alerts = evaluate_alert_rules(alert_context, self.alert_rules)
                if triggered_alerts:
                    logger.warning(f"[{self.plugin_id}] Alerts triggered: {triggered_alerts}")

                self.event_bus.publish(
                    Event(
                        type=EventType.TRANSACTION_INGESTED,
                        source=self.plugin_id,
                        data={"count": len(df), "benford_score": benford_score},
                    )
                )

                return {
                    "status": "ingested",
                    "transaction_count": len(df),
                    "benford_score": benford_score,
                    "alerts_triggered": len(triggered_alerts),
                }
        except Exception:
            pass

        return {"status": "skipped", "reason": "No transaction-like data found."}

    def get_tools(self) -> list[Callable]:
        """Expose financial tools to the AI agent."""
        return [
            self.analyze_transaction_graph,
            self.detect_financial_outliers,
            self.sync_blockchain_anchors,
            self.analyze_sequence_patterns,
            self.calculate_wallet_risk,
            self.analyze_asset_types,
            self.detect_temporal_anomalies,
            self.fetch_external_transactions,
            self.evaluate_alerts,
            self.visualize_transaction_graph,
            self.fetch_exchange_data,
            self.fetch_market_indicators,
            self.calculate_portfolio_risk,
            self.fetch_token_prices,
        ]

    async def analyze_transaction_graph(self, transactions_json: str) -> str:
        """Analyzes the transaction graph to find communities."""
        data = json.loads(transactions_json)
        G = nx.Graph()

        for tx in data:
            G.add_edge(tx["source_wallet"], tx["target_wallet"], weight=tx["amount"])

        communities = list(nx.community.greedy_modularity_communities(G))
        serialized_communities = [list(c) for c in communities]

        result = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "communities": serialized_communities,
            "community_count": len(communities),
        }

        return json.dumps(result, indent=2)

    async def analyze_transaction_graph_with_viz(
        self, transactions_json: str, output_format: str = "png"
    ) -> dict:
        """Analyzes transaction graph and generates visualization."""
        data = json.loads(transactions_json)
        G = nx.Graph()

        for tx in data:
            G.add_edge(tx["source_wallet"], tx["target_wallet"], weight=tx.get("amount", 1))

        communities = list(nx.community.greedy_modularity_communities(G))

        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            _, ax = plt.subplots(figsize=(12, 8))
            pos = nx.spring_layout(G, k=2, iterations=50)

            colors = plt.cm.tab10(np.linspace(0, 1, len(communities)))
            for i, community in enumerate(communities):
                nx.draw_networkx_nodes(
                    G, pos, nodelist=list(community), node_color=[colors[i]], ax=ax
                )
            nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=6, ax=ax)

            plt.title(f"Transaction Network - {len(communities)} Communities")
            plt.tight_layout()

            buffer = io.BytesIO()
            plt.savefig(buffer, format=output_format, dpi=150)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return {
                "visualization": img_base64,
                "format": output_format,
                "communities": len(communities),
                "node_count": G.number_of_nodes(),
            }
        except Exception as e:
            return {"error": str(e)}

    async def visualize_transaction_graph(self, transactions_json: str) -> str:
        """Generate visualization of transaction graph."""
        result = await self.analyze_transaction_graph_with_viz(transactions_json)
        if "error" in result:
            return json.dumps(result)
        return json.dumps(
            {
                "status": "success",
                "communities": result["communities"],
                "node_count": result["node_count"],
                "note": f"Image available ({result['format']})",
            }
        )

    async def detect_financial_outliers(self, transactions_json: str) -> str:
        """Uses PyOD Isolation Forest to detect anomalous transaction patterns."""
        data = json.loads(transactions_json)
        df = pd.DataFrame(data)

        amounts = df["amount"].values.reshape(-1, 1)

        clf = IForest(contamination=self.contamination)
        clf.fit(amounts)

        y_pred = clf.labels_
        scores = clf.decision_scores_

        df["is_anomaly"] = y_pred
        df["anomaly_score"] = scores

        anomalies = df[df["is_anomaly"] == 1].to_dict(orient="records")

        for anomaly in anomalies:
            self.event_bus.publish(
                Event(type=EventType.FORENSIC_ANOMALY_DETECTED, source=self.plugin_id, data=anomaly)
            )

        return json.dumps({"anomaly_count": len(anomalies), "anomalies": anomalies}, indent=2)

    async def sync_blockchain_anchors(self, provider_url: str, wallet_addresses: list[str]) -> str:
        """Synchronize wallet anchors from a blockchain provider."""
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(provider_url))

        if not w3.is_connected():
            return json.dumps(
                {"status": "error", "message": "Failed to connect to blockchain provider"}
            )

        results = []
        for addr in wallet_addresses:
            balance = w3.eth.get_balance(addr)
            results.append(
                {
                    "address": addr,
                    "balance_wei": balance,
                    "balance_eth": float(w3.from_wei(balance, "ether")),
                }
            )

        return json.dumps(
            {
                "status": "success",
                "provider": provider_url,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )

    async def analyze_sequence_patterns(self, transactions_json: str) -> str:
        """Analyze transaction timing patterns for bot-like behavior."""
        data = json.loads(transactions_json)
        df = pd.DataFrame(data)

        if "timestamp" not in df.columns:
            return json.dumps({"error": "No timestamp field found"})

        timestamps = df["timestamp"].tolist()
        amounts = df["amount"].tolist()

        result = perform_sequence_analysis(timestamps, amounts)
        result["interpretation"] = "suspicious" if result["regularity"] > 0.8 else "normal"

        return json.dumps(result, indent=2)

    async def calculate_wallet_risk(self, wallet_address: str, context_json: str) -> str:
        """Calculate risk score for a wallet."""
        context = json.loads(context_json)

        result = calculate_wallet_risk_score(
            transaction_velocity=context.get("tx_per_hour", 0),
            avg_amount=context.get("avg_amount", 0),
            peer_interactions=context.get("peer_count", 0),
            anomaly_count=context.get("anomaly_count", 0),
            age_days=context.get("wallet_age_days"),
        )

        result["wallet"] = wallet_address

        return json.dumps(result, indent=2)

    async def analyze_asset_types(self, transactions_json: str) -> str:
        """Analyze transactions by asset type (ERC-20, NFT, ETH, etc.)."""
        data = json.loads(transactions_json)
        result = analyze_multi_asset(data)
        return json.dumps(result, indent=2)

    async def detect_temporal_anomalies(self, transactions_json: str) -> str:
        """Detect temporal anomalies in transaction time series."""
        data = json.loads(transactions_json)
        df = pd.DataFrame(data)

        if "timestamp" not in df.columns or "amount" not in df.columns:
            return json.dumps({"error": "Required fields: timestamp, amount"})

        amounts = df["amount"].tolist()
        result = detect_time_series_anomalies(
            amounts, window_size=self.time_window, z_threshold=self.z_threshold
        )

        for anomaly in result.get("anomalies", []):
            self.event_bus.publish(
                Event(type=EventType.FORENSIC_ANOMALY_DETECTED, source=self.plugin_id, data=anomaly)
            )

        return json.dumps(result, indent=2)

    async def fetch_external_transactions(
        self, api_provider: str, api_key: str, wallet_address: str, network: str = "ethereum"
    ) -> str:
        """Fetch transactions from external APIs (Etherscan, Blockchair, etc.)."""
        if api_provider.lower() == "etherscan":
            return await self._fetch_etherscan(api_key, wallet_address, network)
        elif api_provider.lower() == "blockchair":
            return await self._fetch_blockchair(api_key, wallet_address, network)
        else:
            return json.dumps({"error": f"Unknown provider: {api_provider}"})

    async def _fetch_etherscan(self, api_key: str, wallet: str, network: str) -> str:
        """Fetch transactions from Etherscan API."""
        try:
            import requests
        except ImportError:
            return json.dumps({"error": "requests library not available"})

        network_suffix = "" if network == "ethereum" else f"-{network}"
        base_url = f"https://api{network_suffix}.etherscan.io/api"

        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 100,
            "sort": "desc",
            "apikey": api_key,
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "1":
                txs = data.get("result", [])[:10]
                return json.dumps(
                    {
                        "provider": "etherscan",
                        "network": network,
                        "wallet": wallet,
                        "transactions": txs,
                        "count": len(txs),
                    },
                    indent=2,
                )
            return json.dumps({"error": data.get("message", "API error")})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _fetch_blockchair(self, api_key: str, wallet: str, network: str) -> str:
        """Fetch transactions from Blockchair API."""
        try:
            import requests
        except ImportError:
            return json.dumps({"error": "requests library not available"})

        network_map = {"ethereum": "ethereum", "bitcoin": "bitcoin"}
        network_code = network_map.get(network, network)

        url = f"https://api.blockchair.com/{network_code}/dashboards/address/{wallet}"

        params = {"limit": 10}

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("data"):
                return json.dumps(
                    {
                        "provider": "blockchair",
                        "network": network,
                        "wallet": wallet,
                        "data": data["data"],
                    },
                    indent=2,
                )
            return json.dumps({"error": "No data returned"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def evaluate_alerts(self, context_json: str) -> str:
        """Evaluate alert rules against context."""
        context = json.loads(context_json)
        triggered = evaluate_alert_rules(context, self.alert_rules)
        return json.dumps(
            {
                "triggered_alerts": triggered,
                "alert_count": len(triggered),
                "available_rules": len(self.alert_rules),
            },
            indent=2,
        )

    async def fetch_exchange_data(
        self, exchange_id: str, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> str:
        """Fetch OHLCV data from CCXT-supported exchanges (100+ exchanges supported)."""
        try:
            import ccxt
        except ImportError:
            return json.dumps({"error": "ccxt library not installed"})

        try:
            exchange_class = getattr(ccxt, exchange_id, None)
            if not exchange_class:
                return json.dumps({"error": f"Exchange {exchange_id} not supported"})

            exchange = exchange_class({"enableRateLimit": True})

            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return json.dumps(
                {
                    "exchange": exchange_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "candles": len(df),
                    "data": df.to_dict(orient="records"),
                },
                indent=2,
                default=str,
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def fetch_market_indicators(
        self, symbol: str, indicators: list[str] | None = None
    ) -> str:
        """Fetch free technical indicators from public exchange APIs."""
        if indicators is None:
            indicators = ["SMA", "EMA", "RSI"]

        try:
            import requests
        except ImportError:
            return json.dumps({"error": "requests library not available"})

        symbol_clean = symbol.replace("/", "").replace("USD", "USDT")

        results = {}
        try:
            candles = requests.get(
                f"https://api.binance.com/api/v3/klines?symbol={symbol_clean}&interval=1h&limit=168",
                timeout=10,
            ).json()

            closes = [float(c[4]) for c in candles]

            if "SMA" in indicators:
                window = 20
                sma = sum(closes[-window:]) / window
                results[" SMA_20"] = sma

            if "EMA" in indicators:
                ema = closes[-1]
                results["EMA"] = ema

            if "RSI" in indicators:
                deltas = np.diff(closes)
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                rs = avg_gain / (avg_loss or 1)
                rsi = 100 - (100 / (1 + rs))
                results["RSI_14"] = rsi

        except Exception as e:
            return json.dumps({"error": str(e)})

        return json.dumps(
            {"symbol": symbol, "indicators": results, "source": "Binance (free)"}, indent=2
        )

    async def calculate_portfolio_risk(
        self, portfolio_json: str, confidence_level: float = 0.95
    ) -> str:
        """Calculate portfolio risk metrics (VaR, CVaR, Sharpe, Sortino)."""
        portfolio = json.loads(portfolio_json)
        returns = []

        for asset in portfolio.get("assets", []):
            returns.append(asset.get("returns", 0))

        if not returns:
            return json.dumps({"error": "No returns data"})

        returns_arr = np.array(returns)

        var = np.percentile(returns_arr, (1 - confidence_level) * 100)
        cvar = returns_arr[returns_arr <= var].mean()

        mean_return = np.mean(returns_arr)
        std_return = np.std(returns_arr)
        sharpe = mean_return / std_return if std_return > 0 else 0

        downside_returns = returns_arr[returns_arr < 0]
        sortino = mean_return / np.std(downside_returns) if len(downside_returns) > 0 else 0

        return json.dumps(
            {
                "var_95": float(var),
                "cvar_95": float(cvar),
                "sharpe_ratio": float(sharpe),
                "sortino_ratio": float(sortino),
                "mean_return": float(mean_return),
                "volatility": float(std_return),
            },
            indent=2,
        )

    async def fetch_token_prices(
        self, exchange: str, tokens: list[str], quote: str = "USDT"
    ) -> str:
        """Fetch current token prices from exchanges using ccxt."""
        try:
            import ccxt
        except ImportError:
            return json.dumps({"error": "ccxt not installed"})

        results = {}
        exchange_class = getattr(ccxt, exchange, None)

        if not exchange_class:
            return json.dumps({"error": f"Exchange {exchange} not supported"})

        ex = exchange_class({"enableRateLimit": True})

        for token in tokens:
            symbol = f"{token}/{quote}"
            try:
                ticker = ex.fetch_ticker(symbol)
                results[token] = {
                    "price": ticker.get("last"),
                    "volume_24h": ticker.get("quoteVolume"),
                    "change_24h": ticker.get("percentage"),
                }
            except Exception:
                results[token] = {"error": "not found"}

        return json.dumps(
            {"exchange": exchange, "prices": results, "timestamp": datetime.now().isoformat()},
            indent=2,
        )


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    """Standard SME Extension Hook."""
    return FinancialForensicsExtension(manifest, nexus_api)
