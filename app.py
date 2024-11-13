import streamlit as st
from solving.puzzle import Puzzle
from solving.solver import Solver
from words.dictionary import Dictionary
from words.word import Word
from time import perf_counter
import difflib

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
if "user_solution" not in st.session_state:
    st.session_state.user_solution = None
if "user_solution_input" not in st.session_state:
    st.session_state.user_solution_input = ""
if "max_ladder_length" not in st.session_state:
    st.session_state.max_ladder_length = False
if "button" not in st.session_state:
    st.session_state.button = False


def main():
    st.title(APP_NAME)
    st.markdown("Generate a word ladder from a **starting word** to an **ending word** by changing one letter at a time. 🔠")

    with st.sidebar:
        st.header("Settings")
        start_word_input = st.text_input("Enter start word:", value=st.session_state.get("start_word_input", ""))
        end_word_input = st.text_input("Enter end word:", value=st.session_state.get("end_word_input", ""))
        st.session_state.max_ladder_length = st.number_input(
            "Max ladder length (optional)", min_value=MINIMUM_LADDER_LENGTH, max_value=MAXIMUM_LADDER_LENGTH,
            value=8, step=1
        )
        limit = st.number_input("Solutions to display at once", min_value=1, max_value=10, value=5)
    
    st.session_state["start_word_input"] = start_word_input
    st.session_state["end_word_input"] = end_word_input

    if start_word_input:
        word_length = len(start_word_input)
        if MINIMUM_WORD_LENGTH <= word_length <= MAXIMUM_WORD_LENGTH:
            with st.spinner("Loading dictionary..."):
                dictionary = Dictionary(word_length)
            st.session_state['dictionary'] = dictionary
            st.session_state['dictionary_load_time'] = perf_counter()

    if st.button("Solve") or st.session_state.button:
        st.session_state.button = True
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

        if st.session_state.max_ladder_length == -1:
            start = perf_counter()
            min_ladder = puzzle.calculate_minimum_ladder_length()
            took = (perf_counter() - start) * 1000
            if min_ladder is None:
                st.markdown(red(f"Cannot solve '{start_word}' to '{end_word}' (took {took:.2f}ms to determine that)."), unsafe_allow_html=True)
                return
            st.session_state.max_ladder_length = min_ladder
            st.markdown(f"Took {green('%.2fms' % took)} to determine minimum ladder length of {green(min_ladder)}.", unsafe_allow_html=True)

        solver = Solver(puzzle)
        with st.spinner("Solving the puzzle..."):
            start = perf_counter()
            solutions = solver.solve(st.session_state.max_ladder_length)
            took = (perf_counter() - start) * 1000
        st.session_state.solutions = [[str(word) for word in solution.ladder] for solution in solutions]

        if len(solutions) == 0:
            st.markdown(red(f"Took {took:.2f}ms to find no solutions (explored {solver.explored_count} solutions)."), unsafe_allow_html=True)
        else:
            # Limit the number of solutions displayed based on the 'limit' input from the settings
            limited_solutions = st.session_state.solutions[:limit]
            st.markdown(f"Took {green('%.2fms' % took)} to find {green(len(limited_solutions))} solutions (explored {green(solver.explored_count)} solutions).", unsafe_allow_html=True)


        user_solution_input = st.text_area("Enter your word ladder solution (comma separated):", st.session_state.user_solution_input)
        st.session_state.user_solution_input = user_solution_input
        
        if st.button("Submit Solution"):
            
            if st.session_state.user_solution_input:
                user_solution_list = [word.strip().upper() for word in st.session_state.user_solution_input.split(",")]
                # st.write(f"User's solution (cleaned): {user_solution_list}")

                st.session_state.user_solution = user_solution_list

                if any([user_solution_list == solution for solution in limited_solutions]):
                    st.success("Congratulations! Your solution is correct.")
                else:
                    st.error("Your solution is incorrect. Here are the closest solutions:")
                    closest_solutions = find_closest_solutions(user_solution_list, limited_solutions)
                    for solution in closest_solutions:
                        st.markdown(" ➔ ".join(solution), unsafe_allow_html=True)
            else:
                st.write("⚠️ Please enter a word ladder solution before submitting.")



def validate_word(dictionary, word_input):
    word = dictionary.get(word_input.upper())
    if word is None:
        st.markdown(red(f"⚠️ Word '{word_input}' does not exist!"), unsafe_allow_html=True)
    elif word.is_island:
        st.markdown(red(f"⚠️ Word '{word_input}' is an island word (cannot change single letter to form another word)."), unsafe_allow_html=True)
    else:
        return word
    return None


def find_closest_solutions(user_solution, solutions):
    
    solutions_with_ratio = [
        (solution, difflib.SequenceMatcher(None, user_solution, solution).ratio())
        for solution in solutions
    ]
    
    solutions_with_ratio.sort(key=lambda x: x[1], reverse=True)
    
    
    closest_solutions = [solution for solution, ratio in solutions_with_ratio]
    
    return closest_solutions


def highlight_changes_in_ladder(ladder):
    highlighted_ladder = []
    
    for i in range(len(ladder) - 1):
        word1 = ladder[i]
        word2 = ladder[i + 1]
        
        
        for j in range(len(word1)):
            if word1[j] != word2[j]:
                
                highlighted_word = (
                    word1[:j] + 
                    f'<span style="color: yellow; font-weight: bold;">{word1[j]}</span>' + 
                    word1[j+1:]
                )
                highlighted_ladder.append(highlighted_word)
                break
        highlighted_ladder.append(" ➔ ")  

    
    highlighted_ladder.append(ladder[-1])
    
    return "".join(highlighted_ladder)


if __name__ == "__main__":
    main()
