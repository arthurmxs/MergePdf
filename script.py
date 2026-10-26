"""Aplicativo para selecionar, ordenar e mesclar arquivos PDF."""

from pathlib import Path
from tkinter import END, Listbox, StringVar, filedialog, messagebox

import customtkinter as ctk
from PyPDF2 import PdfReader, PdfWriter, Transformation
from PyPDF2.errors import PyPdfError


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
A4_WIDTH = 595.28
A4_HEIGHT = 841.89


class PdfMergerApp(ctk.CTk):
    """Interface gráfica para criação de um único PDF a partir de vários arquivos."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Mesclador de PDFs")
        self.geometry("850x610")
        self.minsize(700, 500)
        self.iconbitmap(default=ASSETS_DIR / "app_icon.ico")
        self.pdf_paths: list[Path] = []
        self.output_path: Path | None = None
        self.destination = StringVar(value="Nenhum destino escolhido")

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self._build_interface()

    def _build_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Mesclador de PDFs", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(18, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="Adicione arquivos de quaisquer pastas. As páginas serão ajustadas para A4 sem deformar o conteúdo.",
            text_color=("gray35", "gray75"),
        ).grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=24, pady=20, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        ctk.CTkButton(actions, text="+ Adicionar PDFs", command=self.add_pdfs).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(actions, text="Remover selecionado", fg_color="#9b2c2c", hover_color="#7f1d1d", command=self.remove_selected).grid(row=0, column=1, padx=8)
        ctk.CTkButton(actions, text="Limpar lista", fg_color="transparent", border_width=1, command=self.clear_list).grid(row=0, column=2, padx=8)

        list_frame = ctk.CTkFrame(content)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="Ordem de mesclagem (o primeiro arquivo fica no início do PDF)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        self.file_list = Listbox(
            list_frame, activestyle="none", borderwidth=0, font=("Segoe UI", 11), selectmode="extended",
            background="#2b2b2b", foreground="#f2f2f2", selectbackground="#1f6aa5", selectforeground="#ffffff",
        )
        self.file_list.grid(row=1, column=0, padx=(14, 8), pady=(0, 14), sticky="nsew")
        self.file_list.bind("<Control-Up>", lambda _event: self.move_selected(-1))
        self.file_list.bind("<Control-Down>", lambda _event: self.move_selected(1))

        order_controls = ctk.CTkFrame(list_frame, fg_color="transparent")
        order_controls.grid(row=1, column=1, padx=(0, 14), pady=(0, 14), sticky="ns")
        ctk.CTkLabel(order_controls, text="Organizar").pack(pady=(5, 10))
        ctk.CTkButton(order_controls, text="↑ Subir", width=100, command=lambda: self.move_selected(-1)).pack(pady=4)
        ctk.CTkButton(order_controls, text="↓ Descer", width=100, command=lambda: self.move_selected(1)).pack(pady=4)

        footer = ctk.CTkFrame(self)
        footer.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, textvariable=self.destination, anchor="w", wraplength=530).grid(row=0, column=0, padx=14, pady=14, sticky="ew")
        ctk.CTkButton(footer, text="Escolher destino", command=self.choose_destination).grid(row=0, column=1, padx=(0, 8), pady=14)
        ctk.CTkButton(footer, text="Mesclar PDFs", font=ctk.CTkFont(weight="bold"), command=self.merge_pdfs).grid(row=0, column=2, padx=(0, 14), pady=14)

    def add_pdfs(self) -> None:
        selected_files = filedialog.askopenfilenames(title="Selecione os PDFs para mesclar", filetypes=[("Arquivos PDF", "*.pdf")])
        for file_name in selected_files:
            path = Path(file_name)
            if path not in self.pdf_paths:
                self.pdf_paths.append(path)
        self.refresh_file_list()

    def refresh_file_list(self, selected_indices: tuple[int, ...] = ()) -> None:
        self.file_list.delete(0, END)
        for index, path in enumerate(self.pdf_paths, start=1):
            self.file_list.insert(END, f"{index:02d}.  {path.name}    —    {path.parent}")
        for index in selected_indices:
            self.file_list.selection_set(index)

    def remove_selected(self) -> None:
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showinfo("Nenhum arquivo selecionado", "Selecione ao menos um arquivo para removê-lo.")
            return
        for index in reversed(selected):
            self.pdf_paths.pop(index)
        self.refresh_file_list()

    def clear_list(self) -> None:
        if self.pdf_paths and messagebox.askyesno("Limpar lista", "Remover todos os PDFs selecionados?"):
            self.pdf_paths.clear()
            self.refresh_file_list()

    def move_selected(self, direction: int) -> None:
        selected = self.file_list.curselection()
        if len(selected) != 1:
            messagebox.showinfo("Selecione um arquivo", "Selecione apenas um PDF para mudar sua posição.")
            return
        current = selected[0]
        new_position = current + direction
        if not 0 <= new_position < len(self.pdf_paths):
            return
        self.pdf_paths[current], self.pdf_paths[new_position] = self.pdf_paths[new_position], self.pdf_paths[current]
        self.refresh_file_list((new_position,))

    def choose_destination(self) -> None:
        file_name = filedialog.asksaveasfilename(title="Salvar PDF mesclado como", defaultextension=".pdf", initialfile="PDF mesclado.pdf", filetypes=[("Arquivos PDF", "*.pdf")])
        if file_name:
            self.output_path = Path(file_name)
            self.destination.set(f"Destino: {self.output_path}")

    @staticmethod
    def page_to_a4(page):
        """Ajusta uma página para A4 retrato, mantendo sua proporção original."""
        if page.rotation:
            page.transfer_rotation_to_content()

        source_box = page.mediabox
        source_width = float(source_box.width)
        source_height = float(source_box.height)
        if source_width <= 0 or source_height <= 0:
            raise ValueError("Uma das páginas possui dimensões inválidas.")

        scale = min(A4_WIDTH / source_width, A4_HEIGHT / source_height)
        horizontal_margin = (A4_WIDTH - source_width * scale) / 2
        vertical_margin = (A4_HEIGHT - source_height * scale) / 2
        transform = Transformation().scale(scale).translate(
            horizontal_margin - float(source_box.left) * scale,
            vertical_margin - float(source_box.bottom) * scale,
        )
        page.add_transformation(transform)
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (A4_WIDTH, A4_HEIGHT)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (A4_WIDTH, A4_HEIGHT)
        return page

    def merge_pdfs(self) -> None:
        if not self.pdf_paths:
            messagebox.showwarning("Lista vazia", "Adicione pelo menos um arquivo PDF.")
            return
        if self.output_path is None:
            self.choose_destination()
            if self.output_path is None:
                return
        if self.output_path.resolve() in {pdf_path.resolve() for pdf_path in self.pdf_paths}:
            messagebox.showwarning(
                "Destino inválido",
                "Escolha um nome diferente dos PDFs selecionados para evitar sobrescrevê-los.",
            )
            return

        writer = PdfWriter()
        try:
            for pdf_path in self.pdf_paths:
                reader = PdfReader(str(pdf_path))
                if reader.is_encrypted:
                    raise ValueError(f"O arquivo protegido por senha não pode ser processado: {pdf_path.name}")
                for page in reader.pages:
                    writer.add_page(self.page_to_a4(page))
            with self.output_path.open("wb") as output_file:
                writer.write(output_file)
        except (OSError, ValueError, PyPdfError) as error:
            messagebox.showerror("Não foi possível mesclar", f"Ocorreu um erro ao processar os PDFs:\n{error}")
        else:
            messagebox.showinfo("PDF criado", f"Arquivo criado com sucesso:\n{self.output_path}")


if __name__ == "__main__":
    PdfMergerApp().mainloop()
