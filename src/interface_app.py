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
DIRECTION_LABELS = {
    "Normal": "normal",
    "Invertido": "inverted",
    "Automatico": "auto",
}
FEED_LABELS = {
    "Simulado": "simulated",
    "CSV": "csv",
    "OANDA": "oanda",
}
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
        self.root.geometry("1040x720")
        self.root.minsize(920, 620)

        self.direction_mode = tk.StringVar(value="Automatico")
        self.include_all_signals = tk.BooleanVar(value=True)
        self.min_win_rate = tk.StringVar(value="53")
        self.cycles = tk.StringVar(value="5")
        self.feed = tk.StringVar(value="Simulado")
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
            text="Interface local para replay de candles, analise de oportunidades e validacao em papel.",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(self.root, padding=(12, 6, 12, 12))
        main.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(main, text="Painel de controle", padding=12)
        controls.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(controls, text="Modo de direcao").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.direction_mode,
            values=list(DIRECTION_LABELS.keys()),
            state="readonly",
            width=24,
        ).pack(anchor="w", pady=(2, 10))

        ttk.Checkbutton(
            controls,
            text="Incluir todos os sinais",
            variable=self.include_all_signals,
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(controls, text="Filtro minimo de acerto (%)").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.min_win_rate, width=26).pack(anchor="w", pady=(2, 10))

        ttk.Label(controls, text="Fonte da validacao em papel").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.feed,
            values=list(FEED_LABELS.keys()),
            state="readonly",
            width=24,
        ).pack(anchor="w", pady=(2, 10))

        ttk.Label(controls, text="Quantidade de ciclos").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.cycles, width=26).pack(anchor="w", pady=(2, 14))

        ttk.Button(controls, text="1. Rodar replay dos candles", command=self.run_csv_replay).pack(fill="x", pady=3)
        ttk.Button(controls, text="2. Analisar oportunidades", command=self.run_opportunity_analysis).pack(fill="x", pady=3)
        ttk.Button(controls, text="3. Rodar replay automatico", command=self.run_auto_replay).pack(fill="x", pady=3)
        ttk.Button(controls, text="Validar vela por vela", command=self.run_paper_validation).pack(fill="x", pady=(14, 3))
        ttk.Button(controls, text="Abrir relatorios", command=self.open_reports).pack(fill="x", pady=3)
        ttk.Button(controls, text="Como usar o robo", command=self.show_help).pack(fill="x", pady=3)
        ttk.Button(controls, text="Abrir pasta do projeto", command=self.open_project_folder).pack(fill="x", pady=3)

        warning = ttk.Label(
            controls,
            text="Dica: o replay roda em segundos.\nA validacao vela por vela pode demorar.",
            wraplength=230,
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

        self.log("Interface iniciada. Use os botoes para rodar o robo sem digitar comandos toda hora.\n")

    def log(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")
        self.root.update_idletasks()

    def selected_direction(self) -> str:
        return DIRECTION_LABELS.get(self.direction_mode.get(), "auto")

    def selected_feed(self) -> str:
        return FEED_LABELS.get(self.feed.get(), "simulated")

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
            self.log("Comando interno: " + " ".join(command) + "\n\n")

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
        self.run_in_thread("Replay dos candles", self.replay_command(self.selected_direction()))

    def run_auto_replay(self) -> None:
        self.run_in_thread("Replay automatico", self.replay_command("auto"))

    def run_opportunity_analysis(self) -> None:
        command = [sys.executable, "-m", "src.tools.analyze_csv_replay_opportunities"]
        self.run_in_thread("Analise de oportunidades", command)

    def run_paper_validation(self) -> None:
        confirm = messagebox.askyesno(
            "Validacao vela por vela",
            "Essa validacao demora porque espera a proxima vela fechar. Deseja continuar?",
        )
        if not confirm:
            return

        command = [
            sys.executable,
            "src/paper_validation_runner.py",
            "--feed",
            self.selected_feed(),
            "--cycles",
            self.cycles.get().strip() or "5",
            "--direction-mode",
            self.selected_direction(),
            "--fresh",
            "--min-win-rate",
            self.min_win_rate.get().strip() or "53",
        ]
        if self.include_all_signals.get():
            command.append("--include-all-signals")
        self.run_in_thread("Validacao vela por vela", command)

    def show_help(self) -> None:
        help_window = tk.Toplevel(self.root)
        help_window.title("Como usar o robo")
        help_window.geometry("760x560")
        help_window.minsize(640, 480)

        frame = ttk.Frame(help_window, padding=12)
        frame.pack(fill="both", expand=True)

        text = tk.Text(frame, wrap="word")
        text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll.set)

        content = """
COMO USAR O ROBO DE ANALISE MINIMALISTA

1. Prepare os candles
Coloque arquivos CSV na pasta data/ com as colunas:
timestamp, open, high, low, close

Exemplo de nome:
EURUSD -> data/eurusd_m1.csv
GBPUSD -> data/gbpusd_m1.csv
USDJPY -> data/usdjpy_m1.csv

2. Primeiro rode: Rodar replay dos candles
Esse botao testa os candles historicos e mostra quantos sinais deram WIN, LOSS ou DRAW.

3. Depois rode: Analisar oportunidades
Esse botao verifica se algum ativo performou melhor com o sinal invertido.

4. Depois rode: Rodar replay automatico
Esse botao usa o modo Automatico e inverte somente os grupos que foram marcados como promissores.

5. Abra os relatorios
Use o botao Abrir relatorios para ver os arquivos CSV gerados.
O mais importante e o csv_replay_performance_report.csv.

6. Validacao vela por vela
Use apenas depois do replay. Ela demora porque espera a proxima vela fechar.

O QUE SIGNIFICAM OS MODOS

Normal:
Usa o sinal original do robo.

Invertido:
Troca BUY por SELL e SELL por BUY.

Automatico:
O robo decide quais grupos devem ser invertidos com base no relatorio de oportunidades.

O QUE OBSERVAR

Procure grupos com:
- Win rate acima de 55%
- Pelo menos 30 a 50 sinais para observacao inicial
- 100 ou mais sinais para uma leitura mais forte

AVISO IMPORTANTE

Este robo nao garante lucro e nao envia entradas reais.
Ele serve para estudo estatistico, replay, validacao e analise.
Sempre teste em ambiente demo e use dados suficientes antes de confiar em qualquer resultado.
""".strip()

        text.insert("1.0", content)
        text.configure(state="disabled")

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
            messagebox.showinfo("Relatorios", "Nenhum relatorio encontrado ainda. Rode o replay dos candles primeiro.")

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
