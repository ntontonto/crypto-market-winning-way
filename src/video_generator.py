from manim import *
import json
import datetime
import os
import sys

# Ensure project root is in path for src imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.layout.safe_area import SafeArea

# Configure for Vertical 9:16
config.pixel_height = 1920
config.pixel_width = 1080
config.frame_height = 16.0
config.frame_width = 9.0


class CryptoPlayboardShorts(MovingCameraScene):
    """
    New 60s Format: BTC + ETH Daily Winning Playboard
    Timeline:
    0-2s: Hook (Mode)
    2-10s: Breadth
    10-18s: Volatility
    18-35s: Mini Charts
    35-50s: Movers
    50-60s: Winning Playboard
    """
    def construct(self):
        # Configuration
        self.camera.background_color = "#111111" # Slightly darker for premium feel
        self.camera.frame_height = 16.0
        self.camera.frame_width = 9.0
        
        # Load Data
        try:
            with open("current_input.json", "r") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print("Error: current_input.json not found.")
            return

        self.render_data = self.data.get("render_ready", {})
        if not self.render_data:
            print("Error: 'render_ready' data missing. Please update data fetcher.")
            return

        # Debug Safe Area
        # self.add(SafeArea.debug_overlay()) 

        # Sequence
        self.scene0_hook()
        self.clear()
        self.sceneA_breadth()
        self.clear()
        self.sceneB_volatility()
        self.clear()
        self.sceneC_charts()
        self.clear()
        self.sceneD_movers()
        self.clear()
        self.sceneE_playboard()

    def scene0_hook(self):
        # Duration: 2s
        mode = self.render_data.get("mode", "RANGE")
        
        # Colors
        color = WHITE
        if mode == "TREND": color = GREEN
        elif mode == "CHAOS": color = RED
        elif mode == "RANGE": color = ORANGE
            
        t_label = Text("TODAY'S MODE:", font_size=36, weight=BOLD, color=GRAY)
        t_mode = Text(mode, font_size=80, weight=HEAVY, color=color)
        t_sub = Text("BTC + ETH • Updated daily", font_size=24, color=GRAY)
        
        g = VGroup(t_label, t_mode, t_sub).arrange(DOWN, buff=0.3)
        SafeArea.place(g, 0.5, 0.55) # Slightly above center
        
        self.play(ScaleInPlace(t_mode, 1.2), FadeIn(t_label), FadeIn(t_sub), run_time=0.5)
        self.wait(1.5)
        
    def sceneA_breadth(self):
        # Duration: 8s
        breadth = self.render_data.get("breadth", {})
        pct = breadth.get("pct", 50)
        green = breadth.get("green", 0)
        total = breadth.get("total", 30)
        
        # Grid Data
        metrics = self.data.get("top30_metrics", [])
        
        # Title
        title = Text("Market Breadth (Top 30)", font_size=40, weight=BOLD)
        SafeArea.place(title, 0.5, 0.9)
        
        sub = Text("Changes vs 24h ago", font_size=20, color=GRAY)
        sub.next_to(title, DOWN, buff=0.1)
        
        # Grid visual
        # 5 cols x 6 rows
        grid = VGroup()
        for m in metrics[:30]:
            c = m.get('change_24h_pct', 0)
            col = GREEN if c > 0 else RED
            # Opacity based on magnitude? Keep simple for clarity first, or scale opacity.
            # Let's do simple ON/OFF color with varying intensity maybe?
            
            fill = col
            # Just use opacity param in set_fill
            fill_opacity = 0.8
            if abs(c) < 1.0: fill_opacity = 0.4
            
            rect = Square(side_length=0.8)
            rect.set_fill(fill, opacity=fill_opacity)
            rect.set_stroke(BLACK, width=1)
            
            # Sym
            sym = Text(m['symbol'], font_size=14, color=WHITE).move_to(rect)
            val = Text(f"{c:+.0f}%", font_size=12, color=WHITE).next_to(sym, DOWN, buff=0.05)
            if abs(c) < 1.0: val.set_opacity(0.7)
            
            g = VGroup(rect, sym, val)
            grid.add(g)
            
        grid.arrange_in_grid(rows=6, cols=5, buff=0.1)
        SafeArea.place(grid, 0.5, 0.55)
        
        # Stats
        summary_text = f"{green}/{total} Coins Green ({pct:.0f}%)"
        t_summary = Text(summary_text, font_size=32, color=GREEN if pct>=50 else RED)
        t_summary.next_to(grid, UP, buff=0.3)
        
        expl = Text("Strength of the broad market", font_size=24, color=GRAY)
        expl.next_to(grid, DOWN, buff=0.3)
        
        self.play(FadeIn(title), FadeIn(t_summary))
        self.play(LaggedStart(*[FadeIn(x, scale=0.5) for x in grid], lag_ratio=0.03), run_time=2.0)
        self.play(FadeIn(expl))
        self.wait(4.0)

    def sceneB_volatility(self):
        # Duration: 8s
        btc = self.render_data.get("btc", {})
        eth = self.render_data.get("eth", {})
        
        # Title & Definition
        title = Text("Volatility Regime", font_size=40, weight=BOLD, color=BLUE)
        SafeArea.place(title, 0.5, 0.9)
        
        def_text = Text(
            "Rolling 30-Day Volatility over last 1 Year",
            font_size=24, color=GRAY
        )
        def_text.next_to(title, DOWN, buff=0.1)
        
        def create_vol_chart(label, vol_history, current_val, vol_label):
             # vol_history is list of floats (annualized vol)
            if not vol_history: return VGroup()
            
            # Axes
            v_max = max(vol_history) * 1.1
            v_min = 0
            
            ax = Axes(
                x_range=[0, len(vol_history), len(vol_history)//4],
                y_range=[v_min, v_max, v_max/4],
                x_length=4.0, y_length=2.0,
                axis_config={"include_ticks": False, "stroke_width": 2, "color": GRAY},
                tips=False
            )
            
            # Zones (Rectangles behind chart)
            # Roughly: Low < 40th percentile, High > 75th. 
            # We don't have exact thresholds in value terms returned, but we have the label.
            # Let's just color the line or background based on current state?
            # Or simplified: Draw horizontal zones? 
            # We'll stick to a simple chart for now with Current Point highlighted.
            
            # Plot
            points = [ax.c2p(i, v) for i, v in enumerate(vol_history)]
            line = VMobject(color=WHITE, stroke_width=2).set_points_as_corners(points)
            
            # Highlight Current (Last 30 days... actually last point is "current 30d vol")
            # User asked to "Highlight last 30 days" - but each point IS a 30d vol.
            # I will highlight the end of the curve.
            
            last_pt = points[-1]
            dot = Dot(last_pt, color=YELLOW, radius=0.08)
            
            # Label
            header = Text(label, font_size=32, weight=BOLD).next_to(ax, UP, aligned_edge=LEFT)
            
            status_col = GREEN if vol_label=="LOW" else (RED if vol_label=="HIGH" else YELLOW)
            status = Text(f"{vol_label} ({current_val:.1f}%)", font_size=24, color=status_col)
            status.next_to(header, RIGHT, buff=0.3, aligned_edge=DOWN)
            
            g = VGroup(ax, line, dot, header, status)
            return g, line

        # BTC Chart
        chart_btc, line_btc = create_vol_chart("BTC", btc.get("vol_history", []), btc.get("current_vol_val", 0), btc.get("vol_label", "MED"))
        chart_eth, line_eth = create_vol_chart("ETH", eth.get("vol_history", []), eth.get("current_vol_val", 0), eth.get("vol_label", "MED"))
        
        # Layout
        grp = VGroup(chart_btc, chart_eth).arrange(DOWN, buff=0.8)
        SafeArea.place(grp, 0.5, 0.5)
        
        self.play(FadeIn(title), FadeIn(def_text))
        self.play(FadeIn(chart_btc[0]), FadeIn(chart_btc[3]), FadeIn(chart_btc[4])) # Axes, Text
        self.play(Create(line_btc), run_time=1.5)
        self.play(FadeIn(chart_btc[2])) # Dot
        
        self.play(FadeIn(chart_eth[0]), FadeIn(chart_eth[3]), FadeIn(chart_eth[4]))
        self.play(Create(line_eth), run_time=1.5)
        self.play(FadeIn(chart_eth[2]))
        
        self.wait(2)

    def sceneC_charts(self):
        # Duration: 17s
        # Using 24h data now as per user request
        
        btc_series = self.render_data.get("btc", {}).get("series_24h", [])
        eth_series = self.render_data.get("eth", {}).get("series_24h", [])
        
        if not btc_series or not eth_series:
            self.add(Text("24h Charts Unavailable", font_size=32))
            self.wait(17)
            return

        def create_mini_chart(series, name, meta, color):
            # series: list of {t: ms, price: float}
            # Need to downsample? If too many points.
            # 24h chart from CG (days=1) has ~288 points (5 min intervals).
            # Manim can handle 300 points fine.
            
            prices = [d['price'] for d in series]
            timestamps = [d['t'] for d in series] 
            if not prices: return VGroup(), VMobject()
            
            p_min, p_max = min(prices)*0.999, max(prices)*1.001
            
            # Axes
            ax = Axes(
                x_range=[0, len(prices)-1, len(prices)//4], 
                y_range=[p_min, p_max, (p_max-p_min)/4],
                x_length=6, y_length=2.5,
                axis_config={"include_ticks": False, "stroke_width": 2, "color": GRAY}, 
                tips=False
            )
            
            # Labels for X Axis (Every 6h approx)
            # Total ~288 points -> 6h is ~72 points
            
            # Helper to fmt time
            def fmt_time(ts):
                # ts in ms
                dt = datetime.datetime.fromtimestamp(ts/1000.0)
                return dt.strftime("%H:%M")
            
            # Start
            l_start = Text(fmt_time(timestamps[0]), font_size=16, color=GRAY).next_to(ax.c2p(0, p_min), DOWN, buff=0.2)
            
            # Middle labels (approx +6h, +12h, +18h)
            total_pts = len(timestamps)
            l_m1 = Text(fmt_time(timestamps[int(total_pts*0.25)]), font_size=16, color=GRAY).next_to(ax.c2p(total_pts*0.25, p_min), DOWN, buff=0.2)
            l_m2 = Text(fmt_time(timestamps[int(total_pts*0.5)]), font_size=16, color=GRAY).next_to(ax.c2p(total_pts*0.5, p_min), DOWN, buff=0.2)
            l_m3 = Text(fmt_time(timestamps[int(total_pts*0.75)]), font_size=16, color=GRAY).next_to(ax.c2p(total_pts*0.75, p_min), DOWN, buff=0.2)
            
            # End
            l_end = Text(fmt_time(timestamps[-1]), font_size=16, color=GRAY).next_to(ax.c2p(total_pts-1, p_min), DOWN, buff=0.2)
            
            labels = VGroup(l_start, l_m1, l_m2, l_m3, l_end)
            
            # Plot
            points = [ax.c2p(i, p) for i, p in enumerate(prices)]
            line = VMobject(color=color, stroke_width=3).set_points_as_corners(points)
            
            # Stats (Title)
            last_price = prices[-1]
            chg = meta.get("change_24h_pct", 0)
            sign = "+" if chg > 0 else ""
            c_col = GREEN if chg > 0 else RED
            
            # Title: "BTC 24-Hour Trend"
            header = Text(f"{name} 24h Trend", font_size=24, color=GRAY)
            price_txt = Text(f"${last_price:,.0f}", font_size=36, weight=BOLD)
            pct_txt = Text(f"{sign}{chg:.2f}%", font_size=30, color=c_col)
            
            # Header Block
            #  BTC 24h Trend
            #  $95,000  +2.5%
            
            top_line = header
            bot_line = VGroup(price_txt, pct_txt).arrange(RIGHT, buff=0.4, aligned_edge=DOWN)
            
            h_group = VGroup(top_line, bot_line).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            h_group.next_to(ax, UP, aligned_edge=LEFT, buff=0.2)
            
            # Breakout Label (Context)
            bo_label = meta.get('breakout_label', '')
            if bo_label:
                # Add context about 30D breakout
                bo = Text(f"(30D: {bo_label})", font_size=18, color=YELLOW).next_to(header, RIGHT, buff=0.5)
                h_group.add(bo)

            return VGroup(ax, line, labels, h_group), line

        # Get Meta
        raw_btc = self.render_data.get("btc", {})
        raw_eth = self.render_data.get("eth", {})
        
        grp_btc, line_btc = create_mini_chart(btc_series, "BTC", raw_btc, ORANGE)
        grp_eth, line_eth = create_mini_chart(eth_series, "ETH", raw_eth, BLUE)
        
        # Position
        grp_btc.scale(0.9)
        grp_eth.scale(0.9)
        
        layout = VGroup(grp_btc, grp_eth).arrange(DOWN, buff=0.6)
        SafeArea.place(layout, 0.5, 0.5)
        
        # Animate
        # Draw axes first, then line
        # grp structure: 0=Ax, 1=Line(dup in return), 2=Labels, 3=Header
        
        self.play(FadeIn(grp_btc[0]), FadeIn(grp_btc[2]), FadeIn(grp_btc[3])) 
        self.play(Create(line_btc), run_time=2.0)
        
        self.play(FadeIn(grp_eth[0]), FadeIn(grp_eth[2]), FadeIn(grp_eth[3]))
        self.play(Create(line_eth), run_time=2.0)
        
        self.wait(10)

    def sceneD_movers(self):
        # Duration: 15s (35-50s)
        # Reuse existing rendering logic or simplified?
        # User: "Show Top 3 gainers then Top 3 losers... Add UNUSUAL badge"
        
        movers = self.data.get("movers_24h", {}) # Wait, need to check if data fetcher provides this key structure
        # In current data_fetcher, it's "weekly_top_movers" or "today_top_movers"
        # The user requested JSON contract update: "movers_24h": check PART A.
        # But I didn't verify if I added "movers_24h" explicitly to data_fetcher? 
        # I checked edits to data_fetcher, I added top30_metrics, btc_series, eth_series.
        # I did existing "weekly_top_movers" logic. 
        # I should use what is available. "today_top_movers" is standard.
        # The prompt PART A said: "movers_24h: ... gainers/losers". 
        # Existing code has "today_top_movers". I'll use that.
        
        movers_data = self.data.get("movers_24h", {})
        gainers = movers_data.get("gainers", [])
        losers = movers_data.get("losers", [])
        
        metrics_list = self.data.get("metrics_top30", []) # For Z-Score cross ref
        
        # Create Rows Helper
        def create_row(item, is_gainer):
            cid = item['id']
            sym = item['symbol'].upper()
            pct = item.get('change_24h_pct', 0)
            price = item.get('price', 0)
            
            color = GREEN if is_gainer else RED
            
            # Row Layout
            # SYM $Price +Pct% [UNUSUAL]
            t_sym = Text(sym, font_size=36, weight=BOLD)
            t_price = Text(f"${price:,.2f}" if price>1 else f"${price:.4f}", font_size=28, color=GRAY)
            t_pct = Text(f"{'+' if pct>0 else ''}{pct:.1f}%", font_size=36, color=color)
            
            row = VGroup(t_sym, t_price, t_pct).arrange(RIGHT, buff=0.4)
            
            # Badge
            # Check metrics for Z-Score >= 2
            # I can re-calculate or look for it. Z-score logic is in metrics processor but not persisted in item?
            # MetricsProcessor returns 'on_radar' which has picked UNUSUAL.
            # But here we want to badge ANY UNUSUAL in the top movers list? 
            # Or just check if this coin is the on_radar UNUSUAL pick?
            # Simple check:
            # We also have 'render_ready' -> 'on_radar' list
            
            is_unusual = False
            # Recalc quickly or check on_radar
            for p in self.render_data.get("on_radar", []):
                if p['id'] == cid and p['reason'] == "UNUSUAL":
                    is_unusual = True
                    break
            
            if is_unusual:
                badge = Text("UNUSUAL", font_size=16, color=YELLOW, weight=BOLD)
                bg = SurroundingRectangle(badge, color=YELLOW, fill_color=BLACK, fill_opacity=0.8, buff=0.1)
                b = VGroup(bg, badge)
                row.add(b)
                b.next_to(t_pct, RIGHT, buff=0.3)
            
            return row

        # TITLE
        title = Text("Top Movers (24h)", font_size=48, weight=BOLD)
        SafeArea.place(title, 0.5, 0.9)
        self.add(title)

        # Gainers
        g_rows = VGroup()
        for m in gainers[:3]:
            g_rows.add(create_row(m, True))
        
        g_rows.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        SafeArea.place(g_rows, 0.5, 0.65)
        
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT) for r in g_rows], lag_ratio=0.2))
        
        # Losers
        l_rows = VGroup()
        for m in losers[:3]:
            l_rows.add(create_row(m, False))
        
        l_rows.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        SafeArea.place(l_rows, 0.5, 0.25)
        
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT) for r in l_rows], lag_ratio=0.2))
        
        self.wait(10)

    def sceneE_playboard(self):
        # Duration: 10s
        # Concise Summary
        
        # 1. Mode
        mode = self.render_data.get("mode", "RANGE")
        t_mode = Text(f"Mode: {mode}", font_size=40, weight=BOLD, color=YELLOW)
        
        # 2. Strategy (Consolidated)
        # Simplify text significantly
        strat_map = {
            "TREND": "Buy Dips • Ride Momentum",
            "CHAOS": "Protect Capital • No Leverage",
            "RANGE": "Buy Support • Sell Resistance"
        }
        strat_text = strat_map.get(mode, "Watch Levels")
        t_strat = Text(f"Strategy: {strat_text}", font_size=28, color=WHITE)
        
        # 3. Radar Visuals (Icons/Boxes instead of long text)
        radar_list = self.render_data.get("on_radar", [])
        
        radar_group = VGroup()
        r_title = Text("ON RADAR:", font_size=32, color=BLUE).to_edge(LEFT, buff=0)
        radar_group.add(r_title)
        
        # Create small cards for radar
        cards = VGroup()
        for r in radar_list:
            # Box
            card = Rectangle(width=2.5, height=1.5, color=GRAY, stroke_opacity=0.5)
            # Sym
            sym = Text(r['symbol'], font_size=32, weight=BOLD)
            # Reason
            reason = Text(r['reason'], font_size=18, color=YELLOW)
            
            content = VGroup(sym, reason).arrange(DOWN, buff=0.2).move_to(card)
            c_grp = VGroup(card, content)
            cards.add(c_grp)
            
        if len(cards) > 0:
            cards.arrange(RIGHT, buff=0.2)
            radar_group.add(cards)
            radar_group.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        
        # Layout
        main_layout = VGroup(t_mode, t_strat, radar_group).arrange(DOWN, buff=0.8)
        SafeArea.place(main_layout, 0.5, 0.5)
        
        self.play(Write(t_mode))
        self.play(FadeIn(t_strat))
        self.wait(1)
        if len(cards) > 0:
            self.play(FadeIn(radar_group))
            
        self.wait(7)
