flashcard() {
  source ~/.venv/bin/activate || return
  cd ~/program/LatinLearner || return
  streamlit run flashcard.py
}
