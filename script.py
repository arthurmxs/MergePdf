"""Aplicativo para criar PDFs a partir de imagens e mesclar arquivos PDF."""

from pathlib import Path
import sys
from tkinter import END, Listbox, StringVar, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps
from PyPDF2 import PdfReader, PdfWriter, Transformation
from PyPDF2.errors import PyPdfError


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
A4_WIDTH = 595.28
A4_HEIGHT = 841.89
PDF_DPI = 150
A4_PIXEL_WIDTH = round(A4_WIDTH / 72 * PDF_DPI)
A4_PIXEL_HEIGHT = round(A4_HEIGHT / 72 * PDF_DPI)


class PdfMergerApp(ctk.CTk):
    """Interface para criar um PDF de imagens ou mesclar PDFs existentes."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Criar PDF")
        self.geometry("850x650")
        self.minsize(700, 540)
        if sys.platform.startswith("win"):
            self.iconbitmap(default=str(ASSETS_DIR / "app_icon.ico"))

        self.mode = "images"
        self.image_paths: list[Path] = []
        self.pdf_paths: list[Path] = []
        self.output_paths: dict[str, Path | None] = {"images": None, "pdf": None}
        self.destination = StringVar(value="Nenhum destino escolhido")
        self._drag_index: int | None = None
        self._drag_start_y = 0
        self._dragging = False

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self._build_interface()
        self._set_mode("images")

    @property
    def active_paths(self) -> list[Path]:
        """Return the file list for the current operation."""
        return self.image_paths if self.mode == "images" else self.pdf_paths

    def _build_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        self.heading = ctk.CTkLabel(header, text="Criar PDF", font=ctk.CTkFont(size=26, weight="bold"))
        self.heading.grid(row=0, column=0, padx=24, pady=(18, 2), sticky="w")
        self.subtitle = ctk.CTkLabel(
            header,
            text="Adicione imagens do seu computador e organize a ordem das páginas do PDF.",
            text_color=("gray35", "gray75"),
        )
        self.subtitle.grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=24, pady=18, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        self.mode_selector = ctk.CTkSegmentedButton(
            content,
            values=["Criar PDF", "Mesclar PDF"],
            command=self._on_mode_selected,
        )
        self.mode_selector.grid(row=0, column=0, pady=(0, 14), sticky="w")

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.add_button = ctk.CTkButton(actions, text="+ Adicionar imagens", command=self.add_files)
        self.add_button.grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Remover selecionado",
            fg_color="#9b2c2c",
            hover_color="#7f1d1d",
            command=self.remove_selected,
        ).grid(row=0, column=1, padx=8)
        ctk.CTkButton(
            actions,
            text="Limpar lista",
            fg_color="transparent",
            border_width=1,
            command=self.clear_list,
        ).grid(row=0, column=2, padx=8)

        list_frame = ctk.CTkFrame(content)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(2, weight=1)
        self.list_heading = ctk.CTkLabel(list_frame, text="Ordem das imagens", font=ctk.CTkFont(weight="bold"))
        self.list_heading.grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")
        self.drag_hint = ctk.CTkLabel(
            list_frame,
            text="Arraste os arquivos com o mouse para mudar a ordem.",
            text_color=("gray35", "gray75"),
            font=ctk.CTkFont(size=12),
        )
        self.drag_hint.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="w")

        self.file_list = Listbox(
            list_frame,
            activestyle="none",
            borderwidth=0,
            font=("Segoe UI", 11),
            selectmode="extended",
            background="#2b2b2b",
            foreground="#f2f2f2",
            selectbackground="#1f6aa5",
            selectforeground="#ffffff",
        )
        self.file_list.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="nsew")
        self.file_list.bind("<Button-1>", self._start_drag, add="+")
        self.file_list.bind("<B1-Motion>", self._drag_file, add="+")
        self.file_list.bind("<ButtonRelease-1>", self._finish_drag, add="+")

        footer = ctk.CTkFrame(self)
        footer.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, textvariable=self.destination, anchor="w", wraplength=530).grid(
            row=0, column=0, padx=14, pady=14, sticky="ew"
        )
        ctk.CTkButton(footer, text="Escolher destino", command=self.choose_destination).grid(
            row=0, column=1, padx=(0, 8), pady=14
        )
        self.create_button = ctk.CTkButton(
            footer,
            text="Criar PDF",
            font=ctk.CTkFont(weight="bold"),
            command=self.create_pdf_from_images,
        )
        self.create_button.grid(row=0, column=2, padx=(0, 14), pady=14)

    def _on_mode_selected(self, selected_mode: str) -> None:
        self._set_mode("images" if selected_mode == "Criar PDF" else "pdf")

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        is_images = mode == "images"
        title = "Criar PDF" if is_images else "Mesclar PDF"
        self.title(title)
        self.heading.configure(text=title)
        self.subtitle.configure(
            text=(
                "Adicione imagens do seu computador e organize a ordem das páginas do PDF."
                if is_images
                else "Adicione PDFs de várias pastas e organize a ordem das páginas do arquivo final."
            )
        )
        self.add_button.configure(text="+ Adicionar imagens" if is_images else "+ Adicionar PDFs")
        self.list_heading.configure(
            text=(
                "Ordem das imagens (a primeira será a primeira página)"
                if is_images
                else "Ordem de mesclagem (o primeiro arquivo fica no início do PDF)"
            )
        )
        self.create_button.configure(
            text="Criar PDF" if is_images else "Mesclar PDFs",
            command=self.create_pdf_from_images if is_images else self.merge_pdfs,
        )
        self.mode_selector.set(title)
        self.destination.set(self._destination_text())
        self.refresh_file_list()

    def _destination_text(self) -> str:
        output_path = self.output_paths[self.mode]
        return f"Destino: {output_path}" if output_path else "Nenhum destino escolhido"

    def add_files(self) -> None:
        if self.mode == "images":
            selected_files = filedialog.askopenfilenames(
                title="Selecione as imagens para criar o PDF",
                filetypes=[
                    ("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif"),
                    ("Todos os arquivos", "*.*"),
                ],
            )
        else:
            selected_files = filedialog.askopenfilenames(
                title="Selecione os PDFs para mesclar",
                filetypes=[("Arquivos PDF", "*.pdf")],
            )

        paths = self.active_paths
        for file_name in selected_files:
            path = Path(file_name)
            if path not in paths:
                paths.append(path)
        self.refresh_file_list()

    def refresh_file_list(self, selected_indices: tuple[int, ...] = ()) -> None:
        self.file_list.delete(0, END)
        for index, path in enumerate(self.active_paths, start=1):
            self.file_list.insert(END, f"{index:02d}.  {path.name}    —    {path.parent}")
        for index in selected_indices:
            if 0 <= index < len(self.active_paths):
                self.file_list.selection_set(index)

    def _start_drag(self, event) -> None:
        if not self.active_paths:
            self._drag_index = None
            return
        self._drag_index = self.file_list.nearest(event.y)
        self._drag_start_y = event.y
        self._dragging = False

    def _drag_file(self, event) -> str | None:
        if self._drag_index is None or not self.active_paths:
            return None
        if not self._dragging and abs(event.y - self._drag_start_y) < 5:
            return None

        self._dragging = True
        target_index = self.file_list.nearest(event.y)
        target_index = max(0, min(target_index, len(self.active_paths) - 1))
        if target_index != self._drag_index:
            paths = self.active_paths
            path = paths.pop(self._drag_index)
            paths.insert(target_index, path)
            self.refresh_file_list((target_index,))
            self._drag_index = target_index
        return "break"

    def _finish_drag(self, _event) -> None:
        self._drag_index = None
        self._dragging = False

    def remove_selected(self) -> None:
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showinfo("Nenhum arquivo selecionado", "Selecione ao menos um arquivo para removê-lo.")
            return
        paths = self.active_paths
        for index in reversed(selected):
            paths.pop(index)
        self.refresh_file_list()

    def clear_list(self) -> None:
        if not self.active_paths:
            return
        file_type = "imagens" if self.mode == "images" else "PDFs"
        if messagebox.askyesno("Limpar lista", f"Remover todos os arquivos ({file_type}) selecionados?"):
            self.active_paths.clear()
            self.refresh_file_list()

    def choose_destination(self) -> None:
        output_path = self.output_paths[self.mode]
        is_images = self.mode == "images"
        file_name = filedialog.asksaveasfilename(
            title="Salvar PDF criado como" if is_images else "Salvar PDF mesclado como",
            defaultextension=".pdf",
            initialfile=output_path.name if output_path else ("Imagens.pdf" if is_images else "PDF mesclado.pdf"),
            initialdir=str(output_path.parent) if output_path else None,
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if file_name:
            self.output_paths[self.mode] = Path(file_name)
            self.destination.set(self._destination_text())

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

    @staticmethod
    def image_page(image_path: Path) -> Image.Image:
        """Fit an image onto a white A4 portrait page without changing its proportions."""
        with Image.open(image_path) as source:
            source.seek(0)
            image = ImageOps.exif_transpose(source).convert("RGBA")

        image.thumbnail((A4_PIXEL_WIDTH, A4_PIXEL_HEIGHT), Image.Resampling.LANCZOS)
        page = Image.new("RGB", (A4_PIXEL_WIDTH, A4_PIXEL_HEIGHT), "white")
        x = (A4_PIXEL_WIDTH - image.width) // 2
        y = (A4_PIXEL_HEIGHT - image.height) // 2
        page.paste(image.convert("RGB"), (x, y), image.getchannel("A"))
        image.close()
        return page

    def create_pdf_from_images(self) -> None:
        if not self.image_paths:
            messagebox.showwarning("Lista vazia", "Adicione pelo menos uma imagem para criar o PDF.")
            return
        if self.output_paths["images"] is None:
            self.choose_destination()
            if self.output_paths["images"] is None:
                return

        output_path = self.output_paths["images"]
        if output_path.resolve() in {image_path.resolve() for image_path in self.image_paths}:
            messagebox.showwarning(
                "Destino inválido",
                "Escolha um nome diferente das imagens selecionadas para não sobrescrever um arquivo de origem.",
            )
            return

        pages: list[Image.Image] = []
        try:
            pages = [self.image_page(image_path) for image_path in self.image_paths]
            pages[0].save(
                output_path,
                "PDF",
                save_all=True,
                append_images=pages[1:],
                resolution=PDF_DPI,
            )
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror("Não foi possível criar o PDF", f"Ocorreu um erro ao processar as imagens:\n{error}")
        else:
            messagebox.showinfo(
                "PDF criado com sucesso",
                f"O PDF foi criado com sucesso.\n\nCaminho do arquivo:\n{output_path}",
            )
        finally:
            for page in pages:
                page.close()

    def merge_pdfs(self) -> None:
        if not self.pdf_paths:
            messagebox.showwarning("Lista vazia", "Adicione pelo menos um arquivo PDF.")
            return
        if self.output_paths["pdf"] is None:
            self.choose_destination()
            if self.output_paths["pdf"] is None:
                return

        output_path = self.output_paths["pdf"]
        if output_path.resolve() in {pdf_path.resolve() for pdf_path in self.pdf_paths}:
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
            with output_path.open("wb") as output_file:
                writer.write(output_file)
        except (OSError, ValueError, PyPdfError) as error:
            messagebox.showerror("Não foi possível mesclar", f"Ocorreu um erro ao processar os PDFs:\n{error}")
        else:
            messagebox.showinfo(
                "PDF mesclado com sucesso",
                f"O PDF foi mesclado com sucesso.\n\nCaminho do arquivo:\n{output_path}",
            )


if __name__ == "__main__":
    PdfMergerApp().mainloop()
