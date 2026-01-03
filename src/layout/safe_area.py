from manim import *
import numpy as np

class SafeArea:
    """
    YouTube Shorts Safe Area Layout Helper
    Target Platform: YouTube Shorts (9:16)
    Resolution: 1080x1920
    Manim Config: frame_width=9.0, frame_height=16.0
    
    Coordinate System:
    - Manim origin (0,0) is center.
    - Width range: [-4.5, +4.5]
    - Height range: [-8.0, +8.0]
    
    Safe Margins (Px -> Manim Units):
    - 1.0 unit = 120px
    - Left Margin: 120px -> 1.0 unit
    - Top Margin: 220px -> 1.833 units
    - Bottom Reserved: 288px -> 2.4 units
    - Right Reserved: 240px -> 2.0 units
    """
    
    # Constants
    FRAME_WIDTH = 9.0
    FRAME_HEIGHT = 16.0
    PX_PER_UNIT = 120.0
    
    # Margins in Manim Units
    MARGIN_LEFT = 120.0 / PX_PER_UNIT  # 1.0
    MARGIN_RIGHT = 240.0 / PX_PER_UNIT # 2.0 (Reserved for actions)
    MARGIN_TOP = 220.0 / PX_PER_UNIT   # 1.833
    MARGIN_BOTTOM = 288.0 / PX_PER_UNIT # 2.4 (Reserved for metadata)
    
    @classmethod
    def bounds(cls):
        """
        Returns the safe area bounds (left, valid_right, bottom, top) in Manim coordinates.
        Note: valid_right is the boundary before the right sidebar UI.
        """
        half_w = cls.FRAME_WIDTH / 2
        half_h = cls.FRAME_HEIGHT / 2
        
        left = -half_w + cls.MARGIN_LEFT
        right = half_w - cls.MARGIN_RIGHT # Usable right edge
        top = half_h - cls.MARGIN_TOP
        bottom = -half_h + cls.MARGIN_BOTTOM
        
        return left, right, bottom, top
    
    @classmethod
    def point(cls, ux, uy):
        """
        Returns a point in Manim coordinates relative to the SAFE AREA.
        ux: 0.0 (left) to 1.0 (right of safe area)
        uy: 0.0 (bottom) to 1.0 (top of safe area)
        """
        left, right, bottom, top = cls.bounds()
        
        x = left + (right - left) * ux
        y = bottom + (top - bottom) * uy
        return np.array([x, y, 0])
    
    @classmethod
    def place(cls, mobject, ux, uy, anchor=ORIGIN):
        """
        Places a mobject at normalized coordinates (ux, uy) within the safe area.
        anchor: Alignment of the mobject relative to the point (default centered).
        """
        target_point = cls.point(ux, uy)
        mobject.move_to(target_point, aligned_edge=anchor)
        return mobject
        
    @classmethod
    def clamp(cls, mobject):
        """
        Shifts the mobject to ensure it stays strictly within the safe area.
        Does NOT scale, only shifts.
        """
        left, right, bottom, top = cls.bounds()
        
        # Get current bounds of the object
        mob_left = mobject.get_left()[0]
        mob_right = mobject.get_right()[0]
        mob_top = mobject.get_top()[1]
        mob_bottom = mobject.get_bottom()[1]
        
        shift_vec = np.array([0., 0., 0.])
        
        # X Axis
        if mob_left < left:
            shift_vec[0] = left - mob_left
        elif mob_right > right:
            shift_vec[0] = right - mob_right
            
        # Y Axis
        if mob_bottom < bottom:
            shift_vec[1] = bottom - mob_bottom
        elif mob_top > top:
            shift_vec[1] = top - mob_top
            
        mobject.shift(shift_vec)
        return mobject
        
    @classmethod
    def debug_overlay(cls):
        """
        Returns a VGroup containing the visual representation of the Safe Area and Reserved Zones.
        """
        left, right, bottom, top = cls.bounds()
        
        # Safe Rect (Green outline)
        safe_width = right - left
        safe_height = top - bottom
        safe_center = np.array([(left + right) / 2, (bottom + top) / 2, 0])
        
        safe_rect = Rectangle(
            width=safe_width, 
            height=safe_height,
            color=GREEN,
            stroke_width=4
        ).move_to(safe_center)
        
        label_safe = Text("SAFE AREA", font_size=24, color=GREEN).move_to(safe_rect.get_top() + DOWN * 0.5)
        
        # Right Reserved Zone (Red)
        half_w = cls.FRAME_WIDTH / 2
        r_width = cls.MARGIN_RIGHT
        r_center_x = (right + half_w) / 2
        r_rect = Rectangle(
            width=r_width, 
            height=cls.FRAME_HEIGHT,
            color=RED, 
            fill_opacity=0.2, 
            stroke_opacity=0
        ).move_to(np.array([r_center_x, 0, 0]))
        
        label_right = Text("UI ZONE", font_size=24, color=RED).move_to(r_rect.get_center()).rotate(PI/2)
        
        return VGroup(safe_rect, label_safe, r_rect, label_right)
