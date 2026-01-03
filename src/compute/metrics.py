import statistics
import math

class CryptoMetricsProcessor:
    """
    Computes derived metrics for the 'Daily Winning Playboard'.
    """

    @staticmethod
    def compute_render_ready_data(raw_data):
        """
        Main entry point. Transforms raw JSON input into render-ready metrics.
        """
        
        # 1. Breadth & Mood
        metrics_top30 = raw_data.get("top30_metrics", [])
        breadth_data = CryptoMetricsProcessor._compute_breadth(metrics_top30)
        dispersion = CryptoMetricsProcessor._compute_dispersion(metrics_top30)
        
        # 2. Volatility & Breakout (BTC/ETH)
        btc_series = raw_data.get("btc_series", {}).get("days", [])
        eth_series = raw_data.get("eth_series", {}).get("days", [])
        
        # Note: We need 1Y history for Volatility Percentile, but 30D for charts.
        # Assuming btc_series/eth_series contains enough history (365 days ideally).
        # If not, we fallback gracefully.
        
        btc_24h = raw_data.get("btc_24h", [])
        eth_24h = raw_data.get("eth_24h", [])
        
        btc_metrics = CryptoMetricsProcessor._compute_asset_metrics(btc_series, btc_24h, "btc")
        eth_metrics = CryptoMetricsProcessor._compute_asset_metrics(eth_series, eth_24h, "eth")
        
        # 3. Market Mode
        mode = CryptoMetricsProcessor._classify_mode(breadth_data, btc_metrics, eth_metrics, dispersion)
        
        # 4. On-Radar Picks
        on_radar = CryptoMetricsProcessor._pick_radar_coins(metrics_top30)
        
        # 5. Playbook Text
        playbook = CryptoMetricsProcessor._get_playbook_text(mode)
        
        return {
            "mode": mode,
            "breadth": breadth_data,
            "dispersion": dispersion,
            "btc": btc_metrics,
            "eth": eth_metrics,
            "on_radar": on_radar,
            "playbook_text": playbook
        }

    @staticmethod
    def _compute_breadth(metrics_list):
        if not metrics_list:
            return {"green": 0, "total": 0, "pct": 0}
            
        green_count = sum(1 for m in metrics_list if m.get('change_24h_pct', 0) > 0)
        total = len(metrics_list)
        pct = (green_count / total * 100) if total > 0 else 0
        
        return {
            "green": green_count,
            "total": total,
            "pct": round(pct, 1)
        }
        
    @staticmethod
    def _compute_dispersion(metrics_list):
        if not metrics_list or len(metrics_list) < 2:
            return 0.0
        
        changes = [m.get('change_24h_pct', 0) for m in metrics_list]
        return round(statistics.stdev(changes), 2)

    @staticmethod
    def _compute_asset_metrics(series_days, series_24h_raw, asset_id):
        """
        Computes 30D realised vol percentile and breakout signal.
        Expects series_days to be list of {t: 'YYYY-MM-DD', price: 123.4} sorted by date ASC.
        series_24h_raw: list of {t: ms, price: 123.4}
        """
        if not series_days:
            return {
                "price": 0, "change_24h_pct": 0, 
                "vol_percentile": 50, "vol_label": "MED",
                "breakout_label": "MID", "high_30d": 0, "low_30d": 0,
                "current_vol_val": 0, "vol_history": [],
                "series_24h": []
            }
            
        prices = [d['price'] for d in series_days]
        current_price = prices[-1]
        
        # Change 24h
        change_24h = 0
        if len(prices) >= 2:
            prev = prices[-2]
            if prev > 0:
                change_24h = (current_price - prev) / prev * 100
                
        # --- Volatility Percentile (vs 1Y) ---
        # 1. Calculate daily returns
        returns = []
        for i in range(1, len(prices)):
            p0 = prices[i-1]
            p1 = prices[i]
            if p0 > 0:
                ret = math.log(p1 / p0) # Log returns are better for vol
                returns.append(ret)
                
        # 2. Calculate rolling 30D Volatility (Annualized)
        # We need at least 30 days to compute ONE data point of 30D vol.
        # To compute percentile, we need history of these 30D vols.
        
        rolling_vols = []
        window = 30
        
        if len(returns) >= window:
            for i in range(len(returns) - window + 1):
                window_rets = returns[i : i+window]
                # Annualize: std * sqrt(365)
                vol = statistics.stdev(window_rets) * math.sqrt(365) * 100 # as pct
                rolling_vols.append(vol)
        
        current_vol = rolling_vols[-1] if rolling_vols else 0
        
        # Rank current_vol vs history (last 1Y = approx 365 points of rolling vol if we have data)
        # If we only have 30 days of data, percentile is 50 (or N/A).
        # We assume data fetcher tries to get 365 days.
        
        vol_percentile = 50
        if len(rolling_vols) > 1:
            sorted_vols = sorted(rolling_vols)
            rank = sum(1 for v in sorted_vols if v <= current_vol)
            vol_percentile = int((rank / len(sorted_vols)) * 100)
            
        # Label
        if vol_percentile < 40:
            vol_label = "LOW"
        elif vol_percentile > 75:
            vol_label = "HIGH"
        else:
            vol_label = "MED"
            
        # --- Breakout State (30D) ---
        # Look at last 30 prices
        recent_30 = prices[-30:]
        high_30 = max(recent_30)
        low_30 = min(recent_30)
        
        breakout_label = "MID"
        rnge = high_30 - low_30
        if rnge > 0:
            pos = (current_price - low_30) / rnge
            if pos >= 0.85:
                breakout_label = "NEAR HIGH"
            elif pos <= 0.15: # User said 0.35, but 0.15 is more "Near Low". Sticking to prompt: < 0.35
                breakout_label = "NEAR LOW"
            elif pos <= 0.35: # Explicit prompt check
                breakout_label = "NEAR LOW"
                
        return {
            "price": current_price,
            "change_24h_pct": round(change_24h, 2),
            "vol_percentile": vol_percentile,
            "vol_label": vol_label,
            "breakout_label": breakout_label,
            "high_30d": high_30,
            "low_30d": low_30,
            "current_vol_val": round(current_vol, 1),
            "vol_history": rolling_vols, # List of rolling 30D vol values
            "series_24h": series_24h_raw
        }

    @staticmethod
    def _classify_mode(breadth, btc, eth, dispersion):
        """
        TREND: Breadth >= 65% AND Median Change > 0 (implied by breadth usually) AND Not High Vol
        CHAOS: High Vol OR High Dispersion
        RANGE: Else
        """
        is_high_vol = (btc['vol_label'] == "HIGH") or (eth['vol_label'] == "HIGH")
        # Dispersion threshold? Let's say > 5.0% stddev is chaotic for daily moves
        is_high_dispersion = dispersion > 5.0 
        
        if is_high_vol or is_high_dispersion:
            return "CHAOS"
            
        if breadth['pct'] >= 65:
            return "TREND"
            
        return "RANGE"

    @staticmethod
    def _pick_radar_coins(metrics_list):
        """
        Slot A: MOMENTUM (Rank 24h + Rank 7d)
        Slot B: UNUSUAL (Z-Score)
        Slot C: VOLUME (Volume Spike or Vol/Mcap)
        """
        if not metrics_list:
            return []
            
        # Prepare Data
        # Sort by 24h
        s_24h = sorted(metrics_list, key=lambda x: x.get('change_24h_pct', 0), reverse=True)
        r_24h = {m['id']: i for i, m in enumerate(s_24h)}
        
        # Sort by 7d Mean
        s_7d = sorted(metrics_list, key=lambda x: x.get('stats_7d', {}).get('mean', 0), reverse=True)
        r_7d = {m['id']: i for i, m in enumerate(s_7d)}
        
        candidates = []
        for m in metrics_list:
            cid = m['id']
            sym = m['symbol']
            
            # Momentum Score
            mom_score = r_24h.get(cid, 99) + r_7d.get(cid, 99)
            
            # Z-Score
            stats = m.get('stats_7d', {})
            mean = stats.get('mean', 0)
            std = stats.get('std', 0)
            c24 = m.get('change_24h_pct', 0)
            z = 0
            if std > 0:
                z = abs((c24 - mean) / std)
                
            # Volume Score (Vol / Mcap)
            vol = m.get('volume_24h', 0)
            mcap = m.get('market_cap', 1)
            vol_ratio = vol / mcap if mcap > 0 else 0
            
            candidates.append({
                "id": cid,
                "symbol": sym,
                "mom_score": mom_score,
                "z_score": z,
                "vol_ratio": vol_ratio
            })
            
        # Slot A: Momentum (lowest score)
        cand_mom = sorted(candidates, key=lambda x: x['mom_score'])
        pick_a = cand_mom[0]
        
        # Slot B: Unusual (highest Z)
        # Exclude pick_a
        cand_z = sorted([c for c in candidates if c['id'] != pick_a['id']], key=lambda x: x['z_score'], reverse=True)
        pick_b = cand_z[0] if cand_z else None
        
        # Slot C: Volume
        exclude = {pick_a['id']}
        if pick_b: exclude.add(pick_b['id'])
        cand_v = sorted([c for c in candidates if c['id'] not in exclude], key=lambda x: x['vol_ratio'], reverse=True)
        pick_c = cand_v[0] if cand_v else None
        
        results = []
        if pick_a: results.append({"id": pick_a['id'], "symbol": pick_a['symbol'], "reason": "MOMENTUM"})
        if pick_b: results.append({"id": pick_b['id'], "symbol": pick_b['symbol'], "reason": "UNUSUAL"})
        if pick_c: results.append({"id": pick_c['id'], "symbol": pick_c['symbol'], "reason": "VOLUME"})
            
        return results

    @staticmethod
    def _get_playbook_text(mode):
        if mode == "TREND":
            return "Playbook: Follow strength • avoid chasing spikes"
        elif mode == "CHAOS":
            return "Playbook: Protect capital • no leverage"
        else: # RANGE
            return "Playbook: Wait for breakouts • smaller size"
