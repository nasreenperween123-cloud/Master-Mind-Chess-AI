"""
===============================================================================
MASTERMIND CHESS AI (NEXUS ENGINE v6.0)
Architecture: Autonomous State Engine + Heuristic Pipeline + Cyber-HUD
Frameworks: asyncio, python-chess, customtkinter, stockfish
===============================================================================
"""

import asyncio
import math
import os
import sys
from typing import List, Dict, Any, Optional, Tuple

try:
    import chess
    import chess.engine
except ImportError:
    print("\n[CRITICAL ERROR]: 'python-chess' library is not installed.")
    print("Please execute: pip install python-chess")
    sys.exit(1)

try:
    import customtkinter as ctk
except ImportError:
    print("\n[CRITICAL ERROR]: 'customtkinter' library is not installed.")
    print("Please execute: pip install customtkinter")
    sys.exit(1)

# =============================================================================
# 0. ENGINE CONFIGURATION
# =============================================================================
# Modify this path if Stockfish is not in your system PATH.
STOCKFISH_PATH = "stockfish"
USER_ELO = 800  # Adjust this to test different curriculum tiers (0 to 2800+)

# =============================================================================
# 1. COLOR & HUD THEME SYSTEM
# =============================================================================
class CyberTheme:
    """Design matrix for GUI color arrays."""
    OBSIDIAN_BG = "#0B0E14"
    PANEL_BG = "#12161E"
    BOARD_LIGHT = "#1E232D"
    BOARD_DARK = "#141820"
    BOARD_HIGHLIGHT = "#2B4C5E"
    CYAN_NEON = "#00F3FF"
    GREEN_TOXIC = "#00FF66"
    CRIMSON_ALERT = "#FF0055"
    PURPLE_VOID = "#7000FF"
    YELLOW_WARN = "#FFCC00"
    WHITE_TITANIUM = "#F0F4F8"
    TEXT_MUTED = "#8A95A5"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================================================================
# 2. CURRICULUM TIER MANAGEMENT
# =============================================================================
class EloCurriculumManager:
    """Manages pedagogical parameters and Blunder Shield sensitivities."""
    
    @classmethod
    def get_tier_label(cls, elo: int) -> str:
        if elo < 400:
            return "TIER 0: GENESIS (Foundational Vectors)"
        elif elo < 1000:
            return "TIER 1: TACTICS & ECONOMY (Shield Active)"
        elif elo < 1500:
            return "TIER 2: POSITIONAL FOUNDATIONS"
        elif elo < 2000:
            return "TIER 3: STRATEGIC MASTERY"
        else:
            return "TIER 4: GRANDMASTER INTUITION"

    @classmethod
    def get_blunder_threshold_cp(cls, elo: int) -> float:
        """Returns the centipawn drop required to trigger Blunder Shield."""
        if elo < 400:
            return -350.0  # Full piece loss
        elif elo < 1000:
            return -200.0  # 2-pawn blunder
        elif elo < 1500:
            return -120.0  # Minor tactical oversight
        elif elo < 2000:
            return -80.0   # Positional mistake
        else:
            return -40.0   # Micro-inaccuracy

# =============================================================================
# 3. MATHEMATICAL HEURISTICS & ENGINE ANALYZER
# =============================================================================
class HeuristicEngine:
    """Evaluates mathematical board properties directly."""

    PIECE_VALUES = {
        chess.PAWN: 1.0, chess.KNIGHT: 3.0, chess.BISHOP: 3.25,
        chess.ROOK: 5.0, chess.QUEEN: 9.0, chess.KING: 0.0
    }
    CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]
    EXTENDED_CENTER = [
        chess.C3, chess.D3, chess.E3, chess.F3,
        chess.C4, chess.F4, chess.C5, chess.F5,
        chess.C6, chess.D6, chess.E6, chess.F6
    ]

    @classmethod
    def calculate_material_balance(cls, board: chess.Board) -> Dict[str, float]:
        white_mat = sum(cls.PIECE_VALUES.get(p.piece_type, 0.0) for p in board.piece_map().values() if p.color == chess.WHITE)
        black_mat = sum(cls.PIECE_VALUES.get(p.piece_type, 0.0) for p in board.piece_map().values() if p.color == chess.BLACK)
        return {
            "white_material": white_mat,
            "black_material": black_mat,
            "net_difference": white_mat - black_mat
        }

    @classmethod
    def evaluate_square_control(cls, board: chess.Board) -> Dict[str, Any]:
        white_control = sum(len(board.attackers(chess.WHITE, sq)) for sq in cls.CENTER_SQUARES)
        black_control = sum(len(board.attackers(chess.BLACK, sq)) for sq in cls.CENTER_SQUARES)
        ext_white = sum(len(board.attackers(chess.WHITE, sq)) for sq in cls.EXTENDED_CENTER)
        ext_black = sum(len(board.attackers(chess.BLACK, sq)) for sq in cls.EXTENDED_CENTER)

        total_white = (white_control * 2) + ext_white
        total_black = (black_control * 2) + ext_black

        if total_white > total_black + 2: dominance = "WHITE DOMINANCE"
        elif total_black > total_white + 2: dominance = "BLACK DOMINANCE"
        else: dominance = "CONTESTED CENTER"

        return {"white_score": total_white, "black_score": total_black, "dominance": dominance}

    @classmethod
    def analyze_pawn_structure(cls, board: chess.Board, color: chess.Color) -> Dict[str, Any]:
        pawns = board.pieces(chess.PAWN, color)
        files = [chess.square_file(sq) for sq in pawns]
        doubled = len(files) - len(set(files))
        isolated = 0
        for f in set(files):
            if (f - 1 not in files) and (f + 1 not in files):
                isolated += 1
        return {"doubled": doubled, "isolated": isolated, "total": len(pawns)}

    @staticmethod
    def convert_cp_to_win_probability(cp: float) -> float:
        """Sigmoid mathematical conversion from centipawns to win probability percentage."""
        # W(cp) = 50 + 50 * (2 / (1 + e^(-0.00368208 * cp)) - 1)
        # Bounded to avoid math domain errors
        clamped_cp = max(min(cp, 4000), -4000)
        return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * clamped_cp)) - 1.0)


# =============================================================================
# 4. NEURAL COACH TUTORIAL ENGINE
# =============================================================================
class NeuralCoachPipeline:
    """Generates tier-adaptive natural language explanations."""

    VECTOR_TUTORIALS = {
        chess.PAWN: "PAWN VECTOR: Marches forward 1 square. Captures diagonally. Crucial for locking down territory.",
        chess.KNIGHT: "KNIGHT VECTOR: Moves in an 'L-shape'. The ONLY unit capable of leaping over obstructing pieces.",
        chess.BISHOP: "BISHOP VECTOR: Rays diagonally across matching square colors. Dominates long corridors.",
        chess.ROOK: "ROOK VECTOR: Rays orthogonally. Devastating when controlling open files and the 7th rank.",
        chess.QUEEN: "QUEEN VECTOR: Combines Rook + Bishop vectors. Your most powerful striking piece.",
        chess.KING: "KING VECTOR: Shifts 1 square in any direction. Must be protected via Castling!"
    }

    @classmethod
    def get_move_explanation(cls, board: chess.Board, move: chess.Move, elo: int) -> str:
        piece = board.piece_at(move.from_square)
        if not piece: return ""

        if elo < 400:
            return cls.VECTOR_TUTORIALS.get(piece.piece_type, "Standard Movement.")

        board.push(move)
        is_check = board.is_check()
        is_mate = board.is_checkmate()
        is_capture = board.is_capture(move)
        board.pop()

        ctx = f"Executed {chess.piece_name(piece.piece_type).upper()} -> {chess.square_name(move.to_square)}. "
        if is_mate: ctx += "TERMINAL CHECKMATE!"
        elif is_check: ctx += "DELIVERED DIRECT CHECK!"
        elif is_capture: ctx += "CAPTURED ENEMY MATERIAL."
        else: ctx += "Repositioned for spatial control."
        return ctx

# =============================================================================
# 5. ASYNC STOCKFISH MANAGER
# =============================================================================
class AsyncStockfishManager:
    """Handles non-blocking I/O with Stockfish 16+ via asyncio."""
    
    def __init__(self, path: str):
        self.path = path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.limit = chess.engine.Limit(time=0.1, depth=15)

    async def initialize(self):
        try:
            transport, self.engine = await chess.engine.popen_uci(self.path)
            print(f"[NEXUS_CORE]: Stockfish engine initialized securely.")
        except Exception as e:
            print(f"[NEXUS_WARNING]: Stockfish not found at '{self.path}'.")
            print("Blunder Shield and AI responses will be disabled.")
            self.engine = None

    async def get_evaluation(self, board: chess.Board) -> float:
        if not self.engine: return 0.0
        info = await self.engine.analyse(board, self.limit)
        score = info["score"].white()
        if score.is_mate():
            return 10000.0 if score.mate() > 0 else -10000.0
        return float(score.score(mate_score=10000))

    async def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        if not self.engine: return None
        result = await self.engine.play(board, self.limit)
        return result.move

    async def quit(self):
        if self.engine:
            await self.engine.quit()

# =============================================================================
# 6. NEXUS CYBER-HUD (CUSTOMTKINTER GUI)
# =============================================================================
class NexusGUI(ctk.CTk):
    """Main graphical interface and asynchronous event orchestrator."""

    PIECE_UNICODE = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
    }

    def __init__(self, engine_manager: AsyncStockfishManager, user_elo: int):
        super().__init__()
        self.title("MASTERMIND CHESS AI (NEXUS ENGINE v6.0)")
        self.geometry("1100x700")
        self.configure(fg_color=CyberTheme.OBSIDIAN_BG)
        
        self.engine_manager = engine_manager
        self.board = chess.Board()
        self.user_elo = user_elo
        self.heuristics = HeuristicEngine()
        self.coach = NeuralCoachPipeline()

        self.selected_square: Optional[int] = None
        self.current_cp = 0.0
        self.win_prob = 50.0
        self.running = True

        self.setup_ui()
        self.update_board_ui()
        self.refresh_telemetry()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0) # Eval Bar
        self.grid_columnconfigure(1, weight=1) # Board
        self.grid_columnconfigure(2, weight=1) # Telemetry

        # --- EVAL BAR ---
        eval_frame = ctk.CTkFrame(self, fg_color=CyberTheme.PANEL_BG, corner_radius=10)
        eval_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ns")
        
        self.eval_label = ctk.CTkLabel(eval_frame, text="50.0%", text_color=CyberTheme.CYAN_NEON, font=("Courier", 16, "bold"))
        self.eval_label.pack(pady=10)

        self.eval_bar = ctk.CTkProgressBar(eval_frame, orientation="vertical", width=30, 
                                           progress_color=CyberTheme.WHITE_TITANIUM, fg_color=CyberTheme.BOARD_DARK)
        self.eval_bar.pack(expand=True, fill="y", pady=10)
        self.eval_bar.set(0.5)

        # --- CHESS BOARD ---
        self.board_frame = ctk.CTkFrame(self, fg_color=CyberTheme.BOARD_DARK, corner_radius=5)
        self.board_frame.grid(row=0, column=1, padx=20, pady=20)
        
        self.squares_ui = {}
        for rank in range(7, -1, -1):
            for file in range(8):
                sq_index = chess.square(file, rank)
                color = CyberTheme.BOARD_LIGHT if (rank + file) % 2 != 0 else CyberTheme.BOARD_DARK
                
                btn = ctk.CTkButton(self.board_frame, text="", width=70, height=70, corner_radius=0,
                                    fg_color=color, hover_color=CyberTheme.BOARD_HIGHLIGHT,
                                    font=("Arial", 36), text_color=CyberTheme.WHITE_TITANIUM,
                                    command=lambda s=sq_index: self.on_square_clicked(s))
                btn.grid(row=7-rank, column=file)
                self.squares_ui[sq_index] = btn

        # --- TELEMETRY PANEL ---
        tel_frame = ctk.CTkFrame(self, fg_color=CyberTheme.PANEL_BG, corner_radius=10)
        tel_frame.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
        
        header = ctk.CTkLabel(tel_frame, text="NEXUS-7 TELEMETRY", text_color=CyberTheme.CYAN_NEON, font=("Courier", 20, "bold"))
        header.pack(pady=15, padx=10, anchor="w")

        tier_lbl = ctk.CTkLabel(tel_frame, text=EloCurriculumManager.get_tier_label(self.user_elo), 
                                text_color=CyberTheme.PURPLE_VOID, font=("Courier", 14, "bold"))
        tier_lbl.pack(pady=5, padx=10, anchor="w")

        self.info_text = ctk.CTkTextbox(tel_frame, width=350, height=250, fg_color=CyberTheme.BOARD_DARK,
                                        text_color=CyberTheme.TEXT_MUTED, font=("Courier", 12))
        self.info_text.pack(pady=10, padx=10)
        
        self.coach_text = ctk.CTkTextbox(tel_frame, width=350, height=150, fg_color=CyberTheme.OBSIDIAN_BG,
                                         text_color=CyberTheme.GREEN_TOXIC, font=("Courier", 12))
        self.coach_text.pack(pady=10, padx=10)

    def update_board_ui(self):
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            btn = self.squares_ui[sq]
            
            # Reset colors
            rank, file = chess.square_rank(sq), chess.square_file(sq)
            base_color = CyberTheme.BOARD_LIGHT if (rank + file) % 2 != 0 else CyberTheme.BOARD_DARK
            if sq == self.selected_square:
                base_color = CyberTheme.YELLOW_WARN
                
            btn.configure(fg_color=base_color)
            
            # Set piece symbol
            if piece:
                btn.configure(text=self.PIECE_UNICODE[piece.symbol()])
                # Color code pieces
                p_color = CyberTheme.WHITE_TITANIUM if piece.color == chess.WHITE else CyberTheme.CRIMSON_ALERT
                btn.configure(text_color=p_color)
            else:
                btn.configure(text="")

    def on_square_clicked(self, square: int):
        if self.board.turn != chess.WHITE: return # Lock input during AI turn

        if self.selected_square is None:
            # Select piece
            piece = self.board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = square
                self.update_board_ui()
        else:
            # Attempt Move
            move = chess.Move(self.selected_square, square)
            # Handle auto-queen promotion for simplicity
            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN and chess.square_rank(square) == 7:
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            self.selected_square = None
            self.update_board_ui()

            if move in self.board.legal_moves:
                asyncio.create_task(self.process_user_move(move))
            else:
                # Invalid move, just reset selection
                pass

    async def process_user_move(self, move: chess.Move):
        """Intercepts move for Blunder Shield analysis."""
        pre_cp = self.current_cp
        
        # Test move
        self.board.push(move)
        post_cp = await self.engine_manager.get_evaluation(self.board)
        self.board.pop()

        delta_e = post_cp - pre_cp
        threshold = EloCurriculumManager.get_blunder_threshold_cp(self.user_elo)

        if delta_e < threshold:
            self.trigger_blunder_shield(move, delta_e)
            return

        # Move accepted
        explanation = self.coach.get_move_explanation(self.board, move, self.user_elo)
        self.board.push(move)
        self.current_cp = post_cp
        
        self.update_coach_display(f"[USER MOVE APPROVED]\n{explanation}")
        self.update_board_ui()
        self.refresh_telemetry()
        
        # Trigger AI
        if not self.board.is_game_over():
            asyncio.create_task(self.ai_response_task())

    def trigger_blunder_shield(self, move: chess.Move, delta_e: float):
        """Halts execution and forces tactical recalculation modal."""
        modal = ctk.CTkToplevel(self)
        modal.title("BLUNDER SHIELD INTERCEPT")
        modal.geometry("450x250")
        modal.configure(fg_color=CyberTheme.CRIMSON_ALERT)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text="CRITICAL TACTICAL ERROR DETECTED", font=("Courier", 18, "bold"), text_color=CyberTheme.WHITE_TITANIUM).pack(pady=20)
        ctk.CTkLabel(modal, text=f"Proposed Move: {move.uci()}", font=("Courier", 14), text_color=CyberTheme.OBSIDIAN_BG).pack(pady=5)
        ctk.CTkLabel(modal, text=f"Centipawn Drop: {delta_e:.1f} (Threshold: {EloCurriculumManager.get_blunder_threshold_cp(self.user_elo)})", font=("Courier", 14), text_color=CyberTheme.OBSIDIAN_BG).pack(pady=5)
        
        ctk.CTkButton(modal, text="RECALCULATE (Dismiss)", fg_color=CyberTheme.OBSIDIAN_BG, hover_color=CyberTheme.BOARD_DARK, command=modal.destroy).pack(pady=20)

    async def ai_response_task(self):
        """Non-blocking AI calculation."""
        self.update_coach_display("[NEXUS AI THINKING...]")
        
        best_move = await self.engine_manager.get_best_move(self.board)
        if best_move:
            self.board.push(best_move)
            self.current_cp = await self.engine_manager.get_evaluation(self.board)
            self.update_board_ui()
            self.refresh_telemetry()
            self.update_coach_display(f"[NEXUS AI EXECUTED: {best_move.uci()}]\nYour turn.")
            
            if self.board.is_game_over():
                self.update_coach_display("[GAME TERMINATED]\n" + self.board.result())

    def refresh_telemetry(self):
        """Updates Win %, Radar, and Matrices."""
        self.win_prob = self.heuristics.convert_cp_to_win_probability(self.current_cp)
        
        # Update Eval Bar UI
        # Map 0-100 to 0.0-1.0
        normalized_prob = self.win_prob / 100.0
        self.eval_bar.set(normalized_prob)
        self.eval_label.configure(text=f"{self.win_prob:.1f}%")

        if normalized_prob > 0.6: self.eval_bar.configure(progress_color=CyberTheme.CYAN_NEON)
        elif normalized_prob < 0.4: self.eval_bar.configure(progress_color=CyberTheme.CRIMSON_ALERT)
        else: self.eval_bar.configure(progress_color=CyberTheme.WHITE_TITANIUM)

        # Calculate matrices
        mat_info = self.heuristics.calculate_material_balance(self.board)
        center = self.heuristics.evaluate_square_control(self.board)
        wp = self.heuristics.analyze_pawn_structure(self.board, chess.WHITE)
        bp = self.heuristics.analyze_pawn_structure(self.board, chess.BLACK)

        stats = (
            f"--- MATERIAL ECONOMY ---\n"
            f"White: {mat_info['white_material']} | Black: {mat_info['black_material']}\n"
            f"Net Delta: {mat_info['net_difference']:+.1f}\n\n"
            f"--- CONTROL RADAR ---\n"
            f"Status: {center['dominance']}\n"
            f"W-Score: {center['white_score']} | B-Score: {center['black_score']}\n\n"
            f"--- STRUCTURAL DEFECTS ---\n"
            f"White Doubled/Iso: {wp['doubled']}/{wp['isolated']}\n"
            f"Black Doubled/Iso: {bp['doubled']}/{bp['isolated']}\n"
        )
        
        self.info_text.configure(state="normal")
        self.info_text.delete("0.0", "end")
        self.info_text.insert("0.0", stats)
        self.info_text.configure(state="disabled")

    def update_coach_display(self, text: str):
        self.coach_text.configure(state="normal")
        self.coach_text.delete("0.0", "end")
        self.coach_text.insert("0.0", text)
        self.coach_text.configure(state="disabled")

    async def async_mainloop(self):
        """Binds customtkinter mainloop directly to the asyncio event loop."""
        while self.running:
            self.update()
            await asyncio.sleep(0.01)

    def on_closing(self):
        self.running = False
        self.destroy()

# =============================================================================
# 7. ASYNC BOOTSTRAPPER
# =============================================================================
async def main():
    engine_manager = AsyncStockfishManager(STOCKFISH_PATH)
    await engine_manager.initialize()

    app = NexusGUI(engine_manager, USER_ELO)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        await app.async_mainloop()
    finally:
        await engine_manager.quit()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())