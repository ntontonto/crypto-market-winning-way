
from datetime import datetime

class VideoMetadataGenerator:
    def __init__(self, input_data):
        self.data = input_data
        self.as_of = input_data.get("asOf", "").split("T")[0]

    def get_title(self) -> str:
        """
        Generates a catchy title for the Winning Playboard format.
        Format: BTC + ETH Daily Winning Playboard 🎯 {Date} #shorts
        """
        # We can add dynamic "Mode" if available, e.g. "BTC Breakout? 🚀"
        rr = self.data.get("render_ready", {})
        mode = rr.get("mode", "")
        
        base = f"BTC + ETH Daily Winning Playboard 🎯 {self.as_of}"
        
        # Add slight variation? 
        # "BTC + ETH Daily Playboard: {Mode} Mode ⚡ {Date} #shorts"
        if mode:
            return f"Crypto Market: {mode} MODE ⚡ {self.as_of} #shorts"
            
        return f"{base} #shorts"

    def get_description(self) -> str:
        """
        Generates a description with specific playboard highlights.
        """
        rr = self.data.get("render_ready", {})
        mode = rr.get("mode", "N/A")
        btc = rr.get("btc", {})
        eth = rr.get("eth", {})
        radar = rr.get("on_radar", [])
        
        lines = []
        lines.append(f"Daily Crypto Winning Playboard for {self.as_of} 📊")
        lines.append("")
        lines.append(f"🔥 Today's Market Mode: {mode}")
        lines.append("")
        
        # Volatility Highlight
        b_vol = btc.get("vol_label", "")
        e_vol = eth.get("vol_label", "")
        if b_vol and e_vol:
            lines.append(f"⚡ Volatility Regime: BTC ({b_vol}) / ETH ({e_vol})")
            
        lines.append("")
        lines.append("🎯 On The Radar:")
        if radar:
            for item in radar:
                sym = item.get('symbol', '').upper()
                reason = item.get('reason', '')
                lines.append(f"- {sym}: {reason}")
        else:
            lines.append("No specific radar picks today.")
            
        lines.append("")
        lines.append("Watch daily for your 60-second market edge! ⏱️")
        lines.append("#Crypto #Bitcoin #Ethereum #Trading #Invest #Blockchain #Finance #Altcoins")
        
        # Add dynamic tags
        dynamic_tags = [f"#{item.get('symbol', '').upper()}" for item in radar]
        if dynamic_tags:
            lines.append(" ".join(dynamic_tags))
            
        return "\n".join(lines)

    def get_tags(self) -> list:
        """
        Returns a list of tags.
        """
        tags = [
            "crypto", "bitcoin", "ethereum", "btc", "eth", 
            "crypto trading", "market analysis", "winning playboard", 
            "investing", "finance", "shorts", "crypto news"
        ]
        
        # Add radar coins
        rr = self.data.get("render_ready", {})
        radar = rr.get("on_radar", [])
        for item in radar:
            sym = item.get('symbol', '')
            if sym:
                tags.append(sym)
                tags.append(f"{sym} price")
                tags.append(f"{sym} prediction")
        
        return tags
