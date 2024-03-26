import sqlite3
import random
import tkinter as tk
from tkinter import ttk, filedialog

class VocabularyApp:
    def __init__(self):
        self.db_file = None
        self.current_table = None
        self.current_word_index = 0
        self.vocabulary_data = []
        self.review_mode = "sequence"
        self.create_ui()

    def create_ui(self):
        self.window = tk.Tk()
        self.window.title("Vocabulary App")

        self.table_frame = ttk.Frame(self.window)
        self.table_frame.pack(pady=10)

        listbox_frame = ttk.Frame(self.table_frame)
        listbox_frame.pack(side=tk.LEFT, padx=10)

        title_label = ttk.Label(listbox_frame, text="Vocabulary List", font=("Arial", 14, "bold"))
        title_label.pack(side=tk.TOP)

        self.table_listbox = tk.Listbox(listbox_frame)
        self.table_listbox.pack(side=tk.TOP)
        self.table_listbox.bind("<<ListboxSelect>>", self.on_table_select)

        scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.table_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.window)
        button_frame.pack()

        open_button = ttk.Button(button_frame, text="Open Database", command=self.open_database)
        open_button.pack(side=tk.LEFT, padx=5)

        sequence_button = ttk.Button(button_frame, text="Sequence", command=lambda: self.set_review_mode("sequence"))
        sequence_button.pack(side=tk.LEFT, padx=5)

        self.window.bind("<Left>", self.on_left_key)
        self.window.bind("<Right>", self.on_right_key)

        random_button = ttk.Button(button_frame, text="Random", command=lambda: self.set_review_mode("random"))
        random_button.pack(side=tk.LEFT, padx=5)

        refresh_button = ttk.Button(button_frame, text="Refresh Vocabulary", command=self.refresh_vocabulary)
        refresh_button.pack(side=tk.LEFT, padx=5)

        clear_known_button = ttk.Button(button_frame, text="Clear Known Vocab List", command=self.clear_known_vocab)
        clear_known_button.pack(side=tk.LEFT, padx=5)

        clear_new_button = ttk.Button(button_frame, text="Clear New Vocab List", command=self.clear_new_vocab)
        clear_new_button.pack(side=tk.LEFT, padx=5)

        self.word_frame = ttk.Frame(self.window)
        self.word_frame.pack(pady=10)

        self.id_label = ttk.Label(self.word_frame, text="", font=("Arial", 20))
        self.id_label.pack()

        self.french_label = ttk.Label(self.word_frame, text="", font=("Arial", 32, "bold"))
        self.french_label.pack()

        self.english_label = ttk.Label(self.word_frame, text="", font=("Arial", 24))
        self.english_label.pack()

        self.example_label = ttk.Label(self.word_frame, text="", font=("Arial", 20, "italic"))
        self.example_label.pack()

        self.translation_label = ttk.Label(self.word_frame, text="", font=("Arial", 20))
        self.translation_label.pack()

        choice_frame = ttk.Frame(self.window)
        choice_frame.pack(pady=10)

        yes_button = ttk.Button(choice_frame, text="Y", command=self.mark_word_known)
        yes_button.pack(side=tk.LEFT, padx=5)

        no_button = ttk.Button(choice_frame, text="N", command=self.mark_word_new)
        no_button.pack(side=tk.LEFT, padx=5)

        instruction_frame = ttk.Frame(self.window)
        instruction_frame.pack(pady=10)

        instruction_label = ttk.Label(instruction_frame, text="Instructions:", font=("Arial", 12, "bold"))
        instruction_label.pack()

        instructions = [
            "1. Select a vocabulary table from the list.",
            "2. Choose 'Sequence' or 'Random' review mode.",
            "3. Click 'Y' if you know the word, 'N' if you don't.",
            "4. Use 'Refresh Vocabulary' to reset the word list.",
            "5. Use 'Clear Known Vocab List' and 'Clear New Vocab List' to manage your lists.",
            "6. vocabulary is the root list (can be expanded)", 
            "7. vocab_exe is the running list, everyw word you review, we will remove it from the list",
            "8. known_vocab has words that you know.",
            "9. new_vocab has words that you need to memorizie." 
        ]

        for instruction in instructions:
            bullet_label = ttk.Label(instruction_frame, text=instruction)
            bullet_label.pack(anchor=tk.W)

        self.status_label = ttk.Label(self.window, text="")
        self.status_label.pack()

    def open_database(self):
        self.db_file = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if self.db_file:
            self.explore_database()

    def explore_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        self.table_listbox.delete(0, tk.END)
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            word_count = cursor.fetchone()[0]
            self.table_listbox.insert(tk.END, f"{table_name} ({word_count} words)")

        conn.close()
        self.status_label.config(text=f"Database: {self.db_file}")

    def on_table_select(self, event):
        if self.table_listbox.curselection():
            index = self.table_listbox.curselection()[0]
            self.current_table = self.table_listbox.get(index).split(" ")[0]
            self.load_vocabulary_data()
            self.current_word_index = 0
            self.display_word()

    def load_vocabulary_data(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {self.current_table};")
        self.vocabulary_data = cursor.fetchall()

        conn.close()

    def display_word(self):
        if self.vocabulary_data:
            word_data = self.vocabulary_data[self.current_word_index]
            self.id_label.config(text=f"ID: {word_data[0]}")
            self.french_label.config(text=word_data[1])
            self.english_label.config(text=f"English: {word_data[2]}")
            self.example_label.config(text=f"Example: {word_data[3]}")
            self.translation_label.config(text=f"Translation: {word_data[4]}")
        else:
            self.id_label.config(text="")
            self.french_label.config(text="")
            self.english_label.config(text="")
            self.example_label.config(text="")
            self.translation_label.config(text="")

    def set_review_mode(self, mode):
        self.review_mode = mode
        self.display_next_word()
        self.refresh_vocabulary_list()

    def display_next_word(self):
        if self.review_mode == "sequence":
            self.current_word_index = (self.current_word_index + 1) % len(self.vocabulary_data)
        else:
            self.current_word_index = random.randint(0, len(self.vocabulary_data) - 1)
        self.display_word()

    def mark_word_known(self):
        word_data = self.vocabulary_data[self.current_word_index]
        self.remove_word_from_table(word_data, "new_vocab")
        self.remove_word_from_table(word_data, "vocab_exe")
        self.add_word_to_table(word_data, "known_vocab")
        self.display_next_word()
        self.refresh_vocabulary_list()

    def mark_word_new(self):
        word_data = self.vocabulary_data[self.current_word_index]
        self.remove_word_from_table(word_data, "known_vocab")
        self.remove_word_from_table(word_data, "vocab_exe")
        self.add_word_to_table(word_data, "new_vocab")
        self.display_next_word()
        self.refresh_vocabulary_list()

    def remove_word_from_table(self, word_data, table_name):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Check if the word exists in the table
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (word_data[0],))
        count = cursor.fetchone()[0]

        if count > 0:
            # If the word exists, delete it from the table
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (word_data[0],))
            conn.commit()
        else: 
            # If the word doesn't exist, do nothing
            pass
        conn.close()

    def add_word_to_table(self, word_data, table_name):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
        # Try to insert the word into the table
            cursor.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?)", word_data)
            conn.commit()
        except sqlite3.IntegrityError:
            # If the word already exists, do nothing
            pass
        finally:
           conn.close()

    def refresh_vocabulary(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM vocab_exe")
        cursor.execute("INSERT INTO vocab_exe SELECT * FROM vocabulary")

        conn.commit()
        conn.close()
        self.load_vocabulary_data()
        self.current_word_index = 0
        self.display_word()
        self.refresh_vocabulary_list()

    def clear_known_vocab(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM known_vocab")

        conn.commit()
        conn.close()
        self.refresh_vocabulary_list()

    def clear_new_vocab(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM new_vocab")

        conn.commit()
        conn.close()
        self.refresh_vocabulary_list()

    def refresh_vocabulary(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
           # Delete all words from vocab_exe
           cursor.execute("DELETE FROM vocab_exe")

           # Copy all words from vocabulary to vocab_exe
           cursor.execute("INSERT INTO vocab_exe SELECT * FROM vocabulary")

          # Remove words from vocab_exe that are in known_vocab
           cursor.execute("""
              DELETE FROM vocab_exe
              WHERE id IN (
                  SELECT id FROM known_vocab
               )
           """)

           # Remove words from vocab_exe that are in new_vocab
           cursor.execute("""
              DELETE FROM vocab_exe
                WHERE id IN (
                 SELECT id FROM new_vocab
              )
           """)

           conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while refreshing vocabulary: {e}")
        finally:
           conn.close()

        self.load_vocabulary_data()
        self.current_word_index = 0
        self.display_word()
        self.refresh_vocabulary_list()


    def refresh_vocabulary_list(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        self.table_listbox.delete(0, tk.END)
        for table_name in ["vocabulary", "vocab_exe", "known_vocab", "new_vocab"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            word_count = cursor.fetchone()[0]
            self.table_listbox.insert(tk.END, f"{table_name} ({word_count} words)")

        conn.close()

    def on_left_key(self, event):
        self.mark_word_known()

    def on_right_key(self, event):
        self.mark_word_new()

    def run(self):
        self.window.mainloop()

# Example usage
app = VocabularyApp()
app.run()