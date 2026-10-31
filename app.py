
import streamlit as st
import ast
import io
import tokenize
import pycodestyle

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="Python Code Analyzer",
    page_icon="🐍",
    layout="wide"
)

# ---------------------------------
# CUSTOM CSS
# ---------------------------------

st.markdown("""
<style>
.main {
    background-color: #f4f6f9;
}

.title {
    text-align: center;
    color: #1e3a8a;
    font-size: 38px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    color: gray;
    font-size: 18px;
}

div.stButton > button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    width: 100%;
    height: 45px;
    font-size: 17px;
}

div.stButton > button:hover {
    background-color: #1d4ed8;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------
# HEADER
# ---------------------------------

st.markdown(
    '<div class="title">🐍 Python Code Quality Analyzer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Analyze your Python code quality and comments</div>',
    unsafe_allow_html=True
)

st.divider()


# ---------------------------------
# CODE ANALYSIS FUNCTION
# ---------------------------------

def analyze_code(code):

    results = {
        "score": 100,
        "grade": "",
        "errors": [],
        "suggestions": [],
        "comments": [],
        "statistics": {}
    }

    lines = code.splitlines()

    # Syntax Analysis
    try:
        tree = ast.parse(code)

    except SyntaxError as e:
        results["errors"].append(
            f"Syntax Error at line {e.lineno}: {e.msg}"
        )

        results["score"] = 0
        results["grade"] = "Invalid Syntax"
        return results

    # Code Statistics
    results["statistics"]["Total Lines"] = len(lines)

    results["statistics"]["Blank Lines"] = sum(
        1 for line in lines if not line.strip()
    )

    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    classes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]

    results["statistics"]["Functions"] = len(functions)
    results["statistics"]["Classes"] = len(classes)

    # Comment Analysis
    comment_count = 0

    try:
        tokens = tokenize.generate_tokens(
            io.StringIO(code).readline
        )

        for token in tokens:

            if token.type == tokenize.COMMENT:
                comment_count += 1

                results["comments"].append(
                    f"Line {token.start[0]}: {token.string}"
                )

    except tokenize.TokenError:
        results["errors"].append(
            "Unable to complete comment analysis."
        )

    results["statistics"]["Comments"] = comment_count

    if comment_count == 0:
        results["suggestions"].append(
            "No comments found. Add meaningful comments."
        )

    # Docstring Analysis
    documented_functions = sum(
        1 for node in functions if ast.get_docstring(node)
    )

    documented_classes = sum(
        1 for node in classes if ast.get_docstring(node)
    )

    results["statistics"]["Function Docstrings"] = (
        documented_functions
    )

    results["statistics"]["Class Docstrings"] = (
        documented_classes
    )

    missing_functions = len(functions) - documented_functions
    missing_classes = len(classes) - documented_classes

    if missing_functions:
        results["suggestions"].append(
            f"{missing_functions} function(s) are missing docstrings."
        )

    if missing_classes:
        results["suggestions"].append(
            f"{missing_classes} class(es) are missing docstrings."
        )

    # Long Line Analysis
    long_lines = [
        i for i, line in enumerate(lines, 1)
        if len(line) > 79
    ]

    for line_number in long_lines:
        results["errors"].append(
            f"Line {line_number} exceeds 79 characters."
        )

    # PEP 8 Analysis
    style_checker = pycodestyle.Checker(
        lines=code.splitlines(True)
    )

    style_errors = style_checker.check_all()

    results["statistics"]["PEP 8 Issues"] = style_errors

    # Import Analysis
    imported_names = []

    used_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
    }

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imported_names.append(
                    (
                        alias.asname or alias.name.split(".")[0],
                        node.lineno
                    )
                )

        elif isinstance(node, ast.ImportFrom):

            for alias in node.names:

                if alias.name != "*":
                    imported_names.append(
                        (
                            alias.asname or alias.name,
                            node.lineno
                        )
                    )

    for name, line_number in imported_names:

        if name not in used_names:
            results["suggestions"].append(
                f"Import '{name}' on line {line_number} may be unused."
            )

    # Quality Score
    score = 100

    score -= len(results["errors"]) * 5
    score -= style_errors * 2
    score -= len(results["suggestions"]) * 3

    score = max(0, min(100, score))

    results["score"] = score

    if score >= 85:
        results["grade"] = "Excellent"

    elif score >= 70:
        results["grade"] = "Good"

    elif score >= 50:
        results["grade"] = "Average"

    else:
        results["grade"] = "Needs Improvement"

    return results


# ---------------------------------
# CODE EDITOR
# ---------------------------------

st.subheader("📝 Enter Your Python Code")

default_code = '''def add(a, b):
    """Add two numbers."""
    result = a + b
    return result


def greet(name):
    """Display a greeting."""
    print("Hello", name)


x = add(10, 20)
greet("Python")
'''

code = st.text_area(
    "Paste your Python code below:",
    value=default_code,
    height=300
)


# ---------------------------------
# ANALYZE BUTTON
# ---------------------------------

if st.button("🔍 Analyze My Code"):

    if not code.strip():
        st.warning("Please enter Python code first.")

    else:

        with st.spinner("Analyzing your Python code..."):
            result = analyze_code(code)

        st.divider()

        # Quality Score
        st.header("📊 Analysis Results")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Code Quality Score",
                f'{result["score"]}/100'
            )

            st.progress(result["score"] / 100)

        with col2:
            st.metric(
                "Code Quality Grade",
                result["grade"]
            )

        # Statistics
        st.subheader("📈 Code Statistics")

        stats = result["statistics"]

        cols = st.columns(4)

        for index, (name, value) in enumerate(stats.items()):

            with cols[index % 4]:
                st.metric(name, value)

        # Errors
        st.subheader("❌ Errors")

        if result["errors"]:

            for error in result["errors"]:
                st.error(error)

        else:
            st.success("No syntax or long-line errors found.")

        # Suggestions
        st.subheader("💡 Improvement Suggestions")

        if result["suggestions"]:

            for suggestion in result["suggestions"]:
                st.warning(suggestion)

        else:
            st.success("No suggestions. Great work!")

        # Comments
        st.subheader("💬 Comment Analysis")

        if result["comments"]:

            for comment in result["comments"]:
                st.info(comment)

        else:
            st.warning("No comments found in your code.")

        # Download Report
        report = f"""
PYTHON CODE QUALITY ANALYSIS REPORT

Quality Score: {result['score']}/100
Grade: {result['grade']}

STATISTICS:
{stats}

ERRORS:
{result['errors']}

SUGGESTIONS:
{result['suggestions']}

COMMENTS:
{result['comments']}
"""

        st.download_button(
            label="📥 Download Analysis Report",
            data=report,
            file_name="code_analysis_report.txt",
            mime="text/plain"
        )


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.markdown(
    "<center>Python Code Quality Analyzer | Built with Streamlit 🐍</center>",
    unsafe_allow_html=True
)
