import sqlite3
import random
import tkinter as tk
from tkinter import ttk, filedialog
import os
import tempfile
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import numpy as np

try:
    from gtts import gTTS
    import pygame
except ImportError as e:
    print("Please install the required dependencies by running:")
    print("pip install -r requirements.txt")
    print("Error details:", e)
    exit(1)

class VocabularyApp:
    def __init__(self):
        self.db_file = None
        self.current_table = None
        self.current_word_index = 0
        self.vocabulary_data = []
        self.translation_visible = False
        self.review_mode = "sequence"
        pygame.mixer.init()
        self.words_reviewed = 0
        self.words_known = set()
        self.words_unknown = set()
        self.daily_stats = defaultdict(lambda: {"reviewed": 0, "known": 0, "unknown": 0})
        self.log_file = None
        self.create_ui()
        self.load_daily_stats()

    def create_ui(self):
        self.window = tk.Tk()
        self.window.title("Vocabulary App")

        # Main frame to hold left and right sections
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for existing content
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right frame for the chart
        self.right_frame = ttk.Frame(main_frame, width=400)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add stats frame to left frame
        self.stats_frame = ttk.Frame(left_frame)
        self.stats_frame.pack(anchor=tk.NW, padx=10, pady=10)

        self.stats_label = ttk.Label(self.stats_frame, text="Reviewed: 0 | Known: 0 | Unknown: 0", font=("Arial", 18, "bold"))
        self.stats_label.pack()

        self.table_frame = ttk.Frame(left_frame)
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

        button_frame = ttk.Frame(left_frame)
        button_frame.pack()

        open_button = ttk.Button(button_frame, text="Open Database", command=self.open_database)
        open_button.pack(side=tk.LEFT, padx=5)

        sequence_button = ttk.Button(button_frame, text="Sequence", command=lambda: self.set_review_mode("sequence"))
        sequence_button.pack(side=tk.LEFT, padx=5)

        self.window.bind("<Left>", self.on_left_key)
        self.window.bind("<Right>", self.on_right_key)
        self.window.bind("<Up>", self.on_up_key)
        self.window.bind("<Down>", self.on_down_key)
        self.window.bind("<Return>", self.on_return_key)

        random_button = ttk.Button(button_frame, text="Random", command=lambda: self.set_review_mode("random"))
        random_button.pack(side=tk.LEFT, padx=5)

        refresh_button = ttk.Button(button_frame, text="Refresh Vocabulary", command=self.refresh_vocabulary)
        refresh_button.pack(side=tk.LEFT, padx=5)

        clear_known_button = ttk.Button(button_frame, text="Clear Known Vocab List", command=self.clear_known_vocab)
        clear_known_button.pack(side=tk.LEFT, padx=5)

        clear_new_button = ttk.Button(button_frame, text="Clear New Vocab List", command=self.clear_new_vocab)
        clear_new_button.pack(side=tk.LEFT, padx=5)
        
        toggle_frame = ttk.Frame(left_frame)
        toggle_frame.pack()
        
        #control visibility of the english translation 
        toggle_translation_button = ttk.Button(toggle_frame, text="Toggle Translation", command=self.toggle_translation)
        toggle_translation_button.pack(side=tk.LEFT, padx=5)

        #button to show translation for current word
        show_current_translation_button = ttk.Button(toggle_frame, text="Show Current Translation", command=self.show_current_translation)
        show_current_translation_button.pack(side=tk.LEFT, padx=5)
        
        #button to prounce vocab
        pronunciation_button = ttk.Button(toggle_frame, text="Pronunce Word", command=self.play_current_pronunciation)
        pronunciation_button.pack(side=tk.LEFT, padx=5)

        sentence_pronunciation_button = ttk.Button(toggle_frame, text="Pronunce Sentence", command=self.play_sentence_pronunciation)
        sentence_pronunciation_button.pack(side=tk.LEFT, padx=5)

        self.word_frame = ttk.Frame(left_frame)
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

        choice_frame = ttk.Frame(left_frame)
        choice_frame.pack(pady=10)

        yes_button = ttk.Button(choice_frame, text="Y", command=self.mark_word_known)
        yes_button.pack(side=tk.LEFT, padx=5)

        no_button = ttk.Button(choice_frame, text="N", command=self.mark_word_new)
        no_button.pack(side=tk.LEFT, padx=5)

        instruction_frame = ttk.Frame(left_frame)
        instruction_frame.pack(pady=10)

        instruction_label = ttk.Label(instruction_frame, text="Instructions:", font=("Arial", 12, "bold"))
        instruction_label.pack()

        instructions = [
            "1. Select a vocabulary table from the list.",
            "2. Choose 'Sequence' or 'Random' review mode.",
            "3. Click 'Y' or Left key if you know the word, 'N' or Right key if you don't.",
            "4. Use 'Refresh Vocabulary' to reset the word list.",
            "5. Use 'Clear Known Vocab List' and 'Clear New Vocab List' to manage your lists.",
            "6. vocabulary is the root list (can be expanded)", 
            "7. vocab_exe is the running list, everyw word you review, we will remove it from the list",
            "8. known_vocab has words that you know.",
            "9. new_vocab has words that you need to memorizie.",
            "10. Click 'Toggle Translation' or Down key to show/hide English translations.",
            "11. Click 'Show Current Translation' or Up key to reveal the translation for the current word."
        ]

        for instruction in instructions:
            bullet_label = ttk.Label(instruction_frame, text=instruction)
            bullet_label.pack(anchor=tk.W)

        self.status_label = ttk.Label(left_frame, text="")
        self.status_label.pack()

        # Create the chart
        self.create_chart()

    def create_chart(self):
        fig, ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax = ax

    def update_chart(self):
        self.ax.clear()
        dates = list(self.daily_stats.keys())[-7:]  # Last 7 days
        reviewed = [self.daily_stats[date]["reviewed"] for date in dates]
        known = [self.daily_stats[date]["known"] for date in dates]
        unknown = [self.daily_stats[date]["unknown"] for date in dates]

        x = np.arange(len(dates))  # the label locations
        width = 0.25  # the width of the bars

        self.ax.bar(x - width, reviewed, width, label='Reviewed', color='blue')
        self.ax.bar(x, known, width, label='Known', color='green')
        self.ax.bar(x + width, unknown, width, label='Unknown', color='red')

        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Number of Words')
        self.ax.set_title('Daily Statistics')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(dates, rotation=45, ha='right')
        self.ax.legend()

        plt.tight_layout()
        self.canvas.draw()

    def load_daily_stats(self):
        if self.log_file and os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                for line in f:
                    date, reviewed, known, unknown = line.strip().split(',')
                    self.daily_stats[date] = {
                        "reviewed": int(reviewed),
                        "known": int(known),
                        "unknown": int(unknown)
                    }
        self.update_chart()

    def save_daily_stats(self):
        today = datetime.date.today().isoformat()
        self.daily_stats[today] = {
            "reviewed": self.words_reviewed,
            "known": len(self.words_known),
            "unknown": len(self.words_unknown)
        }
        
        with open(self.log_file, 'w') as f:
            for date, stats in self.daily_stats.items():
                f.write(f"{date},{stats['reviewed']},{stats['known']},{stats['unknown']}\n")
        
        self.update_chart()

    #function to control visibility of translation
    def toggle_translation(self):
        self.translation_visible = not self.translation_visible
        self.display_word()

    def open_database(self):
        self.db_file = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if self.db_file:
            self.log_file = os.path.join(os.path.dirname(self.db_file), "vocab_stats.txt")
            self.load_daily_stats()
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

    # def display_word(self):
    #     if self.vocabulary_data:
    #         word_data = self.vocabulary_data[self.current_word_index]
    #         self.id_label.config(text=f"ID: {word_data[0]}")
    #         self.french_label.config(text=word_data[1])
    #         self.english_label.config(text=f"English: {word_data[2]}")
    #         self.example_label.config(text=f"Example: {word_data[3]}")
    #         self.translation_label.config(text=f"Translation: {word_data[4]}")
    #     else:
    #         self.id_label.config(text="")
    #         self.french_label.config(text="")
    #         self.english_label.config(text="")
    #         self.example_label.config(text="")
    #         self.translation_label.config(text="")

    def display_word(self):
        if self.vocabulary_data:
           word_data = self.vocabulary_data[self.current_word_index]
           self.id_label.config(text=f"ID: {word_data[0]}")
           self.french_label.config(text=word_data[1])
        
           if self.translation_visible:
              self.english_label.config(text=f"English: {word_data[2]}")
              self.translation_label.config(text=f"Translation: {word_data[4]}")
           else:
              self.english_label.config(text="")
              self.translation_label.config(text="")
        
           self.example_label.config(text=f"Example: {word_data[3]}")
        else:
           self.id_label.config(text="")
           self.french_label.config(text="")
           self.english_label.config(text="")
           self.example_label.config(text="")
           self.translation_label.config(text="")

    def show_current_translation(self):
        if self.vocabulary_data:
           word_data = self.vocabulary_data[self.current_word_index]
           self.english_label.config(text=f"English: {word_data[2]}")
           self.translation_label.config(text=f"Translation: {word_data[4]}")
    
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


    def display_next_word(self):
        if self.vocabulary_data:
            if self.review_mode == "sequence":
             # Get the list of indexes from the current table
               conn = sqlite3.connect(self.db_file)
               cursor = conn.cursor()
               cursor.execute(f"SELECT id FROM {self.current_table} ORDER BY id")
               indexes = [row[0] for row in cursor.fetchall()]
               conn.close()

               # Find the next smallest index greater than the current index
               next_index = None
               for index in indexes:
                   if index > self.vocabulary_data[self.current_word_index][0]:
                       next_index = index
                       break

               # If no next index found, wrap around to the smallest index
               if next_index is None:
                   next_index = indexes[0]

               # Find the index of the word with the next smallest index
               self.current_word_index = next((i for i, word in enumerate(self.vocabulary_data) if word[0] == next_index), 0)
            else:
               # Get the list of indexes from the current table
               conn = sqlite3.connect(self.db_file)
               cursor = conn.cursor()
               cursor.execute(f"SELECT id FROM {self.current_table}")
               indexes = [row[0] for row in cursor.fetchall()]
               conn.close()

               # Randomly select an index from the list of indexes
               random_index = random.choice(indexes)

               # Find the index of the word with the randomly selected index
               self.current_word_index = next((i for i, word in enumerate(self.vocabulary_data) if word[0] == random_index), 0)

            self.display_word()   

    def mark_word_known(self):
        word_data = self.vocabulary_data[self.current_word_index]
        self.remove_word_from_table(word_data, "new_vocab")
        self.remove_word_from_table(word_data, "vocab_exe")
        self.add_word_to_table(word_data, "known_vocab")
        self.words_reviewed += 1
        self.words_known.add(word_data[0])  # Add word ID to known set
        self.words_unknown.discard(word_data[0])  # Remove from unknown set if present
        self.update_stats()
        self.display_next_word()
        self.refresh_vocabulary_list()
        self.save_daily_stats()

    def mark_word_new(self):
        word_data = self.vocabulary_data[self.current_word_index]
        self.remove_word_from_table(word_data, "known_vocab")
        self.remove_word_from_table(word_data, "vocab_exe")
        self.add_word_to_table(word_data, "new_vocab")
        self.words_reviewed += 1
        self.words_unknown.add(word_data[0])  # Add word ID to unknown set
        self.words_known.discard(word_data[0])  # Remove from known set if present
        self.update_stats()
        self.display_next_word()
        self.refresh_vocabulary_list()
        self.save_daily_stats()

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

#this is old version should not be used since it doesnt remove words from known and new vocab list
    # def refresh_vocabulary(self):
    #     conn = sqlite3.connect(self.db_file)
    #     cursor = conn.cursor()

    #     cursor.execute("DELETE FROM vocab_exe")
    #     cursor.execute("INSERT INTO vocab_exe SELECT * FROM vocabulary")

    #     conn.commit()
    #     conn.close()
    #     self.load_vocabulary_data()
    #     self.current_word_index = 0
    #     self.display_word()
    #     self.refresh_vocabulary_list()

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

        self.words_reviewed = 0
        self.words_known.clear()
        self.words_unknown.clear()
        self.update_stats()

        self.load_vocabulary_data()
        self.current_word_index = 0
        self.display_word()
        self.refresh_vocabulary_list()
        self.save_daily_stats()

    def update_stats(self):
        stats_text = f"Reviewed: {self.words_reviewed} | Known: {len(self.words_known)} | Unknown: {len(self.words_unknown)}"
        self.stats_label.config(text=stats_text)

    def refresh_vocabulary_list(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        self.table_listbox.delete(0, tk.END)
        for table_name in ["vocabulary", "vocab_exe", "known_vocab", "new_vocab"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            word_count = cursor.fetchone()[0]
            self.table_listbox.insert(tk.END, f"{table_name} ({word_count} words)")

        conn.close()

    def play_pronunciation(self, text, language='en'):
        try:
           tts = gTTS(text=text, lang=language)
           with tempfile.NamedTemporaryFile(delete=True) as fp:
               tts.save(f"{fp.name}.mp3")
               pygame.mixer.music.load(f"{fp.name}.mp3")
               pygame.mixer.music.play()
               while pygame.mixer.music.get_busy():
                   pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"An error occurred while playing the pronunciation: {e}")
    
    #pronounce sentence
    def play_sentence_pronunciation(self):
        if self.vocabulary_data:
            word_data = self.vocabulary_data[self.current_word_index]
            french_sentence = word_data[3]
            if french_sentence:
                self.play_pronunciation(french_sentence, language='fr')
            else:
                print("No French sentence available for pronunciation.")
    
    #pronounce word
    def play_current_pronunciation(self):
        if self.vocabulary_data:
            word_data = self.vocabulary_data[self.current_word_index]
            french_word = word_data[1]
            self.play_pronunciation(french_word, language='fr')

    def on_left_key(self, event):
        self.mark_word_known()

    def on_right_key(self, event):
        self.mark_word_new()

    def on_up_key(self, event):
        self.show_current_translation()

    def on_down_key(self, event):
        self.toggle_translation()

    def on_return_key(self, event):
        self.play_current_pronunciation()

    def run(self):
        self.window.mainloop()

# Example usage
app = VocabularyApp()
app.run()