import streamlit as st
from solving.puzzle import Puzzle
from solving.solver import Solver
from words.dictionary import Dictionary
from words.word import Word
from time import perf_counter


APP_NAME = "WordLadder"
MINIMUM_WORD_LENGTH = 2
MAXIMUM_WORD_LENGTH = 15
MINIMUM_LADDER_LENGTH = 1
MAXIMUM_LADDER_LENGTH = 10


def green(msg):
    return f'<span style="color: green;">{msg}</span>'

def red(msg):
    return f'<span style="color: red;">{msg}</span>'


if "page_start" not in st.session_state:
    st.session_state.page_start = 0
if "solutions" not in st.session_state:
    st.session_state.solutions = None


def main():
    st.title(APP_NAME)
    st.markdown("Generate a word ladder from a **starting word** to an **ending word** by changing one letter at a time. 🔠")

    
    with st.sidebar:
        st.header("Settings")
        start_word_input = st.text_input("Enter start word:")
        end_word_input = st.text_input("Enter end word:")
        max_ladder_length = st.number_input(
            "Max ladder length (optional)", min_value=MINIMUM_LADDER_LENGTH, max_value=MAXIMUM_LADDER_LENGTH,
            value=8, step=1
        )
        limit = st.number_input("Solutions to display at once", min_value=1, max_value=10, value=5)

    
    if start_word_input:
        word_length = len(start_word_input)
        if MINIMUM_WORD_LENGTH <= word_length <= MAXIMUM_WORD_LENGTH:
            with st.spinner("Loading dictionary..."):
                dictionary = Dictionary(word_length)
            st.session_state['dictionary'] = dictionary
            st.session_state['dictionary_load_time'] = perf_counter()

    
    if st.button("Solve"):
        if 'dictionary' not in st.session_state:
            st.markdown(red("⚠️ Please enter a valid start word length between 2 and 15 characters."), unsafe_allow_html=True)
            return

        dictionary = st.session_state['dictionary']
        dictionary_load_time = (perf_counter() - st.session_state['dictionary_load_time']) * 1000

        
        start_word = validate_word(dictionary, start_word_input)
        end_word = validate_word(dictionary, end_word_input)

        if not start_word or not end_word:
            return

        st.markdown(f"Took {green('%.2fms' % dictionary_load_time)} to load dictionary.", unsafe_allow_html=True)

        
        puzzle = Puzzle(start_word, end_word)

        
        if max_ladder_length == -1:
            start = perf_counter()
            min_ladder = puzzle.calculate_minimum_ladder_length()
            took = (perf_counter() - start) * 1000
            if min_ladder is None:
                st.markdown(red(f"Cannot solve '{start_word}' to '{end_word}' (took {took:.2f}ms to determine that)."), unsafe_allow_html=True)
                return
            max_ladder_length = min_ladder
            st.markdown(f"Took {green('%.2fms' % took)} to determine minimum ladder length of {green(min_ladder)}.", unsafe_allow_html=True)

        
        solver = Solver(puzzle)
        with st.spinner("Solving the puzzle..."):
            start = perf_counter()
            solutions = solver.solve(max_ladder_length)
            took = (perf_counter() - start) * 1000
        st.session_state.solutions = solutions  

        if len(solutions) == 0:
            st.markdown(red(f"Took {took:.2f}ms to find no solutions (explored {solver.explored_count} solutions)."), unsafe_allow_html=True)
        else:
            st.markdown(f"Took {green('%.2fms' % took)} to find {green(len(solutions))} solutions (explored {green(solver.explored_count)} solutions).", unsafe_allow_html=True)

    
    if st.session_state.solutions:
        solutions = st.session_state.solutions

        
        page_start = st.session_state.page_start
        for solution in solutions[page_start: page_start + limit]:
            
            ladder_display = []
            for i in range(len(solution)):
                word = str(solution[i])  

                if i == 0:
                    
                    ladder_display.append(word)
                else:
                    
                    prev_word = str(solution[i - 1])
                    highlighted_word = ""
                    for j in range(len(word)):
                        if word[j] == prev_word[j]:
                            highlighted_word += word[j]  
                        else:
                            highlighted_word += f'<span style="color: green; font-weight: bold;">{word[j]}</span>'  
                    ladder_display.append(highlighted_word)

            
            st.markdown(" ➔ ".join(ladder_display), unsafe_allow_html=True)

        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous"):
                st.session_state.page_start = max(st.session_state.page_start - limit, 0)
        with col2:
            if st.button("Next"):
                st.session_state.page_start = min(st.session_state.page_start + limit, len(solutions) - limit)



def validate_word(dictionary, word_input):
    word = dictionary.get(word_input.upper())
    if word is None:
        st.markdown(red(f"⚠️ Word '{word_input}' does not exist!"), unsafe_allow_html=True)
    elif word.is_island:
        st.markdown(red(f"⚠️ Word '{word_input}' is an island word (cannot change single letter to form another word)."), unsafe_allow_html=True)
    else:
        return word
    return None


if __name__ == "__main__":
    main()
