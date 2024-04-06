# VocabMaster

VocabMaster is a powerful vocabulary learning application designed to help users master new words efficiently. With VocabMaster, you can easily import vocabulary lists from SQLite databases, choose between different review modes, track your progress, and even listen to pronunciations of words and sentences.

## Features

- Import vocabulary lists from SQLite databases
- Choose between "Sequence" and "Random" review modes
- Mark words as known or new and track your progress
- Toggle English translations on or off
- Listen to pronunciations of French words and sentences

## Installation

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies by running the following command:


## Usage

1. Run the `vocabulary_app.py` script using Python.
2. Click on the "Open Database" button to select an SQLite database file containing your vocabulary lists.
3. Select a vocabulary table from the list to start reviewing words.
4. Use the "Sequence" or "Random" buttons to choose the review mode.
5. Click the "Y" button or press the Left arrow key to mark a word as known, or click the "N" button or press the Right arrow key to mark it as new.
6. Use the "Pronunciation" button to listen to the pronunciation of the current French word.
7. Use the "Sentence Pronunciation" button to listen to the pronunciation of the French sentence or example.
8. Customize your learning experience by toggling translations, refreshing the vocabulary list, or clearing known/new word lists.

## Dependencies

- gTTS: Google Text-to-Speech library for generating pronunciations.
- pygame: Library for playing audio files.

The required dependencies are listed in the `requirements.txt` file and can be installed using `pip`.
