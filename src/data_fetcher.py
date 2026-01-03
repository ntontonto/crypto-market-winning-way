
import requests
import json
import os
import time
from datetime import datetime, timedelta
from src.compute.metrics import CryptoMetricsProcessor

class CryptoDataFetcher:
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = cache_dir
        self.api_url_base = "https://api.coingecko.com/api/v3"
        self.api_key = self._load_api_key()
        
        # Rate limit configuration
        # Public: ~10-15 calls/min (safe) -> 4.0s delay
        # Demo Key: 30 calls/min -> 2.2s delay (safe)
        if self.api_key:
            print("Configured matching CoinGecko Demo API Key. Using optimized rate limits (2.2s delay).")
            self.sleep_duration = 2.2
        else:
            print("No API Key found. Using public rate limits (4.0s delay).")
            self.sleep_duration = 4.0
            
        self.fetch_enabled = True

    def _load_api_key(self):
        """
        Manually parse .env file to find COINGECKO_API_KEY without external dependencies.
        """
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("COINGECKO_API_KEY="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass
        return None

    def _get_headers(self):
        """Returns headers with API key if available."""
        headers = {
            "accept": "application/json"
        }
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        return headers

    def generate_input_json(self):
        """
        Orchestrates the fetching of all necessary data to produce the 'input.json' 
        required by the video generator.
        """
        print("Starting full data fetch sequence...")
        
        # 1. Fetch current Top 30
        current_top = self._fetch_current_top_markets(limit=30)
        
        # 1b. Download Icons
        print("Downloading coin icons...")
        icon_map = {} # coin_id -> local_path
        os.makedirs("./assets/coins", exist_ok=True)
        
        for coin in current_top:
            cid = coin['id']
            img_url = coin.get('image')
            if img_url:
                local_path = self._download_icon(cid, img_url)
                if local_path:
                    icon_map[cid] = os.path.abspath(local_path)
            time.sleep(0.5) # Gentle rate limit
        
        # 2. Fetch Historical 7-day Market Chart
        history_map = {} # { coin_id: { 'market_caps': {date: val}, 'prices': {date: val} } }
        
        print(f"Fetching 7-day history for {len(current_top)} coins...")
        for i, coin in enumerate(current_top):
            coin_id = coin['id']
            print(f"[{i+1}/{len(current_top)}] Fetching history for {coin_id}...")
            history = self._fetch_coin_history_7d(coin_id)
            history_map[coin_id] = history
            time.sleep(self.sleep_duration)

        # 2b. Fetch Long-Term History for BTC & ETH (365 days) and 24h charts
        if self.fetch_enabled:
            print("Fetching 365-day history for BTC & ETH...")
            btc_series = self._fetch_coin_history_long("bitcoin", days=365)
            eth_series = self._fetch_coin_history_long("ethereum", days=365)
            
            print("Fetching 24h charts for BTC & ETH...")
            btc_24h = self._fetch_24h_chart("bitcoin")
            eth_24h = self._fetch_24h_chart("ethereum")
        else:
            # Mock or Empty
            btc_series, eth_series = [], []
            btc_24h, eth_24h = [], []
            
        # Determine 7 dates (today - 6 days through today)
        today = datetime.utcnow().date()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            
        # 5. Build "weekly_top_movers" AND "top30_metrics"
        # We calculate change from first date to last available date
        import statistics

        metrics_list = []
        
        start_date = dates[0]
        end_date = dates[-1]
        
        for coin in current_top:
            c_id = coin['id']
            sym = coin['symbol'].upper()
            img_path = icon_map.get(c_id, "")
            
            prices = history_map.get(c_id, {}).get('prices', {})
            sorted_dates = sorted(prices.keys())
            
            
            # --- 5b. Metrics Calculation ---
            sorted_prices_val = [prices[d] for d in sorted_dates if prices[d] > 0]
            daily_returns = []
            for i in range(1, len(sorted_prices_val)):
                p0 = sorted_prices_val[i-1]
                p1 = sorted_prices_val[i]
                if p0 > 0:
                    ret = ((p1 - p0) / p0) * 100
                    daily_returns.append(ret)
                    
            mean_7d = 0
            std_7d = 0
            if daily_returns:
                mean_7d = statistics.mean(daily_returns)
                if len(daily_returns) > 1:
                    std_7d = statistics.stdev(daily_returns)
            
            
            change_24h = coin.get('price_change_percentage_24h', 0)
            vol_24h = coin.get('total_volume', 0)
            mcap = coin.get('market_cap', 0)
            
            metrics_list.append({
                "id": c_id,
                "symbol": sym,
                "change_24h_pct": change_24h,
                "volume_24h": vol_24h, 
                "market_cap": mcap,
                "image": img_path,
                "stats_7d": {
                    "mean": mean_7d,
                    "std": std_7d,
                    # "daily_returns": daily_returns[-7:] 
                }
            })

        
        # --- 5c. Movers 24h (from current_top) ---
        # existing current_top has price_change_percentage_24h
        
        # Sort by 24h change
        current_top_sorted = sorted(current_top, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
        
        def map_mover(c):
            return {
                "id": c['id'],
                "name": c['name'],
                "symbol": c['symbol'].upper(),
                "price": c.get('current_price', 0),
                "change_24h_pct": c.get('price_change_percentage_24h', 0),
                "image": icon_map.get(c['id'], "")
            }
            
        gainers_24h = [map_mover(c) for c in current_top_sorted[:3]]
        # Losers (worst change)
        losers_24h = [map_mover(c) for c in current_top_sorted[-3:][::-1]]
        
        movers_24h = {
            "gainers": gainers_24h,
            "losers": losers_24h
        }
        
        final_json = {
            "asOf": datetime.utcnow().isoformat() + "Z",
            "currency": "usd",
            "movers_24h": movers_24h,
            "top30_metrics": metrics_list,
            "btc_series": btc_series,
            "eth_series": eth_series,
            "btc_24h": btc_24h,
            "eth_24h": eth_24h
        }
        
        # 6. Compute Render Ready Data
        print("Computing render-ready metrics...")
        
        # We need to assemble a raw_data dict for the processor
        raw_data_for_metrics = {
            "top30_metrics": metrics_list,
            "btc_series": btc_series,
            "eth_series": eth_series,
            "btc_24h": btc_24h,
            "eth_24h": eth_24h
        }
        render_ready = CryptoMetricsProcessor.compute_render_ready_data(raw_data_for_metrics)
        final_json["render_ready"] = render_ready
        
        return final_json

    def _fetch_current_top_markets(self, limit=30):
        url = f"{self.api_url_base}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        print("Fetching current top markets...")
        resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _fetch_coin_history_7d(self, coin_id):
        """
        Returns a dict with 'market_caps' and 'prices' maps: { "YYYY-MM-DD": value }
        """
        url = f"{self.api_url_base}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": "7",
            "interval": "daily" 
        }
        try:
            resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            if resp.status_code == 429:
                print("Rate limit hit. Sleeping 60s...")
                time.sleep(60)
                resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
                
            resp.raise_for_status()
            data = resp.json()
            
            result = {'market_caps': {}, 'prices': {}}
            
            for key in ['market_caps', 'prices']:
                for entry in data.get(key, []):
                    ts = entry[0]
                    val = entry[1]
                    date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                    result[key][date_str] = val
                
            return result
        except Exception as e:
            print(f"Failed to fetch history for {coin_id}: {e}")
            return {'market_caps': {}, 'prices': {}}

    def _fetch_coin_history_long(self, coin_id, days=365):
        """
        Fetches daily OHLC-like data (using prices endpoint for simplicity) for 'days' duration.
        Returns list of {t: 'YYYY-MM-DD', price: float}.
        """
        url = f"{self.api_url_base}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": "daily" 
        }
        try:
            resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            if resp.status_code == 429:
                time.sleep(60)
                resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            
            resp.raise_for_status()
            data = resp.json()
            
            prices = data.get('prices', [])
            day_list = []
            
            for entry in prices:
                ts = entry[0]
                val = entry[1]
                date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                
                # Check if we already added this date (CoinGecko sometimes returns multiple points per day, or midnight)
                if day_list and day_list[-1]['t'] == date_str:
                     # Update with latest price for that day
                     day_list[-1]['price'] = val
                else:
                    day_list.append({"t": date_str, "price": val})
            
            return {"days": day_list}
            
        except Exception as e:
            print(f"Failed to fetch long history for {coin_id}: {e}")
            return {"days": []}


    def _fetch_24h_chart(self, coin_id):
        """
        Fetches intraday data for last 24h.
        Returns list of {t: timestamp_ms, price: float}.
        """
        url = f"{self.api_url_base}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": "1"
        }
        
        try:
            resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            if resp.status_code == 429:
                time.sleep(60)
                resp = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            
            resp.raise_for_status()
            data = resp.json()
            prices = data.get('prices', [])
            
            formatted = []
            for p in prices:
                formatted.append({
                    "t": p[0], # Keep Ms
                    "price": p[1]
                })
            return formatted
        except Exception as e:
            print(f"Error fetching 24h chart for {coin_id}: {e}")
            return []

    def _download_icon(self, coin_id, url):
        """Downloads coin icon to ./assets/coins/{coin_id}.png if not exists."""
        try:
            path = f"./assets/coins/{coin_id}.png"
            if os.path.exists(path):
                return path
                
            print(f"Downloading icon for {coin_id}...")
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(r.content)
                return path
        except Exception as e:
            print(f"Error downloading icon for {coin_id}: {e}")
        return None

if __name__ == "__main__":
    fetcher = CryptoDataFetcher()
    # Test run
    # data = fetcher.generate_input_json()
    # print(json.dumps(data, indent=2))

