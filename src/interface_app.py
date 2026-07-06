from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "ROBO DE ANALISE MINIMALISTA"
REPORTS = [
    "csv_replay_performance_report.csv",
    "csv_replay_opportunity_report.csv",
    "csv_replay_results.csv",
    "paper_validation_results.csv",
    "real_performance_report.csv",
    "empirical_win_rates.csv",
]


class MinimalAnalysisRobotApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_NAME} - MVP")
        self.root.geometry("980x680")
        self.root.minsize(860, 560)

        self.direction_mode = tk.StringVar(value="auto")
        self.include_all_signals = tk.BooleanVar(value=True)
        self.min_win_rate = tk.StringVar(value="53")
        self.cycles = tk.StringVar(value="5")
        self.feed = tk.StringVar(value="simulated")
        self.status = tk.StringVar(value="Pronto.")
        self.running = False

        self.build_ui()

    def build_ui(self) -> None:
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")

        title = ttk.Label(header, text=APP_NAME, font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text="Interface local para CSV Replay, analise de oportunidades e validacao em papel.",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(self.root, padding=(12, 6, 12, 12))
        main.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(main, text="Controles", padding=12)
        controls.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(controls, text="Modo de direcao").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.direction_mode,
            values=["normal", "inverted", "auto"],
            state="readonly",
            width=22,
        ).pack(anchor="w", pady=(2, 10))

        ttk.Checkbutton(
            controls,
            text="Incluir todos os sinais",
            variable=self.include_all_signals,
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(controls, text="Filtro minimo de win rate (%)").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.min_win_rate, width=24).pack(anchor="w", pady=(2, 10))

        ttk.Label(controls, text="Feed da validacao em papel").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.feed,
            values=["simulated", "csv", "oanda"],
            state="readonly",
            width=22,
        ).pack(anchor="w", pady=(2, 10))

        ttk.Label(controls, text="Ciclos da validacao em papel").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.cycles, width=24).pack(anchor="w", pady=(2, 14))

        ttk.Button(controls, text="1. Rodar CSV Replay", command=self.run_csv_replay).pack(fill="x", pady=3)
        ttk.Button(controls, text="2. Analisar oportunidades", command=self.run_opportunity_analysis).pack(fill="x", pady=3)
        ttk.Button(controls, text="3. Replay Auto", command=self.run_auto_replay).pack(fill="x", pady=3)
        ttk.Button(controls, text="Validacao em papel", command=self.run_paper_validation).pack(fill="x", pady=(14, 3))
        ttk.Button(controls, text="Abrir relatorios", command=self.open_reports).pack(fill="x", pady=3)
        ttk.Button(controls, text="Abrir pasta do projeto", command=self.open_project_folder).pack(fill="x", pady=3)

        warning = ttk.Label(
            controls,
            text="Dica: CSV Replay roda em segundos.\nValidacao em papel espera vela por vela.",
            wraplength=220,
            foreground="#8a5a00",
        )
        warning.pack(anchor="w", pady=(18, 0))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        status_bar = ttk.Label(right, textvariable=self.status)
        status_bar.pack(anchor="w", pady=(0, 6))

        output_frame = ttk.LabelFrame(right, text="Saida do sistema", padding=8)
        output_frame.pack(fill="both", expand=True)

        self.output = tk.Text(output_frame, wrap="word", height=28)
        self.output.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        scroll.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=scroll.set)

        self.log("Interface iniciada. Use os botoes para rodar o projeto sem comandos no terminal.\n")

    def log(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")
        self.root.update_idletasks()

    def set_running(self, value: bool, message: str) -> None:
        self.running = value
        self.status.set(message)

    def run_in_thread(self, title: str, command: list[str]) -> None:
        if self.running:
            messagebox.showinfo("Aguarde", "Ja existe um processo rodando.")
            return

        def worker() -> None:
            self.set_running(True, f"Rodando: {title}")
            self.log(f"\n=== {title} ===\n")
            self.log("Comando: " + " ".join(command) + "\n\n")

            try:
                process = subprocess.Popen(
                    command,
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                assert process.stdout is not None
                for line in process.stdout:
                    self.log(line)

                code = process.wait()
                if code == 0:
                    self.log("\nProcesso finalizado com sucesso.\n")
                    self.set_running(False, "Pronto.")
                else:
                    self.log(f"\nProcesso terminou com erro. Codigo: {code}\n")
                    self.set_running(False, "Erro no processo.")
            except Exception as exc:
                self.log(f"\nErro: {exc}\n")
                self.set_running(False, "Erro.")

        threading.Thread(target=worker, daemon=True).start()

    def replay_command(self, direction_mode: str) -> list[str]:
        command = [
            sys.executable,
            "-m",
            "src.tools.run_csv_replay",
            "--direction-mode",
            direction_mode,
            "--fresh",
            "--min-win-rate",
            self.min_win_rate.get().strip() or "53",
        ]
        if self.include_all_signals.get():
            command.append("--include-all-signals")
        return command

    def run_csv_replay(self) -> None:
        self.run_in_thread("CSV Replay", self.replay_command(self.direction_mode.get()))

    def run_auto_replay(self) -> None:
        self.run_in_thread("CSV Replay Auto", self.replay_command("auto"))

    def run_opportunity_analysis(self) -> None:
        command = [sys.executable, "-m", "src.tools.analyze_csv_replay_opportunities"]
        self.run_in_thread("Analise de oportunidades", command)

    def run_paper_validation(self) -> None:
        confirm = messagebox.askyesno(
            "Validacao em papel",
            "A validacao em papel demora porque espera vela por vela. Deseja continuar?",
        )
        if not confirm:
            return

        command = [
            sys.executable,
            "src/paper_validation_runner.py",
            "--feed",
            self.feed.get(),
            "--cycles",
            self.cycles.get().strip() or "5",
            "--direction-mode",
            self.direction_mode.get(),
            "--fresh",
            "--min-win-rate",
            self.min_win_rate.get().strip() or "53",
        ]
        if self.include_all_signals.get():
            command.append("--include-all-signals")
        self.run_in_thread("Validacao em papel", command)

    def open_file(self, path: Path) -> None:
        if not path.exists():
            self.log(f"Arquivo nao encontrado: {path.name}\n")
            return

        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def open_reports(self) -> None:
        self.log("\nAbrindo relatorios disponiveis...\n")
        opened = 0
        for report in REPORTS:
            path = PROJECT_ROOT / report
            if path.exists():
                self.open_file(path)
                opened += 1
            else:
                self.log(f"Ignorado, nao existe: {report}\n")

        if opened == 0:
            messagebox.showinfo("Relatorios", "Nenhum relatorio encontrado ainda. Rode o CSV Replay primeiro.")

    def open_project_folder(self) -> None:
        if os.name == "nt":
            os.startfile(PROJECT_ROOT)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(PROJECT_ROOT)])
        else:
            subprocess.Popen(["xdg-open", str(PROJECT_ROOT)])


def main() -> None:
    root = tk.Tk()
    MinimalAnalysisRobotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
